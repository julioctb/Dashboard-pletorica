"""
Servicio orquestador de dispersión bancaria.

Responsabilidades:
1. Validar que el período esté CALCULADO o CERRADO.
2. Obtener empleados del período con datos bancarios.
3. Obtener configuración de bancos de la empresa.
4. Agrupar empleados por banco destino.
5. Generar el archivo de layout por banco usando el generador correcto.
6. Almacenar el archivo en Supabase Storage.
7. Registrar la operación en la tabla dispersion_layouts.
8. Retornar el resumen con URLs de descarga.

Patrón: Direct Access (sin repository).
"""
import logging
from typing import Optional

from app.database import db_manager
from app.core.exceptions import BusinessRuleError, NotFoundError, DatabaseError
from app.services.nomina_periodo_service import nomina_periodo_service
from app.services.dispersion import GENERADORES

logger = logging.getLogger(__name__)

# Bucket de Supabase Storage donde se guardan los layouts
_BUCKET = 'archivos'

# Estatus en los que se permite generar layouts
_ESTATUS_PERMITIDOS = ('CALCULADO', 'CERRADO')


class DispersionService:
    """
    Orquesta la generación de archivos bancarios para pago de nómina.

    Genera un layout por cada banco configurado en la empresa que tenga
    empleados asignados en el período. Soporta Banregio (TXT posiciones
    fijas), HSBC (TXT delimitado) y Fondeadora (CSV).
    """

    def __init__(self):
        self.supabase = db_manager.get_client()

    # =========================================================================
    # PÚBLICO PRINCIPAL
    # =========================================================================

    async def generar_layouts(
        self,
        periodo_id: int,
        generado_por: Optional[str] = None,
    ) -> list[dict]:
        """
        Genera todos los layouts de dispersión para el período.

        Args:
            periodo_id:   ID del período de nómina.
            generado_por: UUID del usuario que inicia la operación.

        Returns:
            Lista de dicts con: banco, nombre_archivo, total_empleados,
            total_monto, errores, url_descarga (signed URL 24h).

        Raises:
            BusinessRuleError: Si el período no está en estatus permitido.
            NotFoundError:     Si el período no existe.
        """
        # 1. Validar período
        periodo = await nomina_periodo_service.obtener_periodo(periodo_id)
        if periodo['estatus'] not in _ESTATUS_PERMITIDOS:
            raise BusinessRuleError(
                f"El período debe estar en {_ESTATUS_PERMITIDOS} para dispersar. "
                f"Estatus actual: '{periodo['estatus']}'"
            )

        empresa_id = periodo['empresa_id']

        # 2. Obtener empleados con datos bancarios y monto > 0
        empleados_raw = await nomina_periodo_service.obtener_empleados_periodo(periodo_id)
        empleados = [
            emp for emp in empleados_raw
            if (emp.get('clabe_destino') or '').strip()
            and float(emp.get('total_neto') or 0) > 0
        ]

        if not empleados:
            raise BusinessRuleError(
                "No hay empleados con datos bancarios y monto neto > 0 para dispersar."
            )

        # 3. Obtener configuración de bancos
        configs = await self._obtener_configuraciones(empresa_id)
        if not configs:
            raise BusinessRuleError(
                "La empresa no tiene bancos configurados para dispersión. "
                "Configura los bancos en la tabla configuracion_bancos_empresa."
            )

        # 4. Agrupar empleados por banco_destino
        por_banco: dict[str, list[dict]] = {}
        sin_banco: list[str] = []
        for emp in empleados:
            banco = (emp.get('banco_destino') or '').upper().strip()
            if banco:
                por_banco.setdefault(banco, []).append(emp)
            else:
                sin_banco.append(emp.get('nombre_empleado', '?'))

        resultados: list[dict] = []

        # 5. Generar layout por banco configurado
        for config in configs:
            if not config.get('activo'):
                continue
            nombre_banco = config['nombre_banco'].upper()
            formato = config.get('formato', '')
            empleados_banco = por_banco.get(nombre_banco, [])

            if not empleados_banco:
                logger.info(
                    f"Banco {nombre_banco}: sin empleados asignados — se omite."
                )
                continue

            generador_cls = GENERADORES.get(formato)
            if not generador_cls:
                logger.warning(f"Formato '{formato}' no soportado para banco {nombre_banco}.")
                continue

            generador = generador_cls()

            # Validar datos bancarios
            errores = generador.validar_datos(empleados_banco)

            # Empleados válidos (con CLABE correcta y monto > 0)
            empleados_validos = [
                emp for emp in empleados_banco
                if generador.validar_clabe(emp.get('clabe_destino', ''))
                and float(emp.get('total_neto') or 0) > 0
            ]

            if not empleados_validos:
                resultados.append({
                    'banco': nombre_banco,
                    'nombre_archivo': '',
                    'total_empleados': 0,
                    'total_monto': 0.0,
                    'errores': errores or [f'Sin empleados válidos para {nombre_banco}'],
                    'url_descarga': '',
                })
                continue

            # Generar bytes del archivo
            nombre_archivo, contenido = generador.generar(
                empleados_validos, config, periodo
            )

            # 6. Subir a Supabase Storage
            storage_path = (
                f"dispersion/{empresa_id}/{periodo_id}/{nombre_banco}/{nombre_archivo}"
            )
            url_descarga = await self._subir_archivo(storage_path, contenido)

            total_monto = sum(
                float(emp.get('total_neto') or 0) for emp in empleados_validos
            )

            # 7. Registrar en dispersion_layouts (upsert → permite regenerar)
            await self._registrar_layout(
                periodo_id=periodo_id,
                empresa_id=empresa_id,
                nombre_banco=nombre_banco,
                nombre_archivo=nombre_archivo,
                storage_path=storage_path,
                total_empleados=len(empleados_validos),
                total_monto=total_monto,
                errores=errores,
                generado_por=generado_por,
            )

            resultados.append({
                'banco': nombre_banco,
                'nombre_archivo': nombre_archivo,
                'total_empleados': len(empleados_validos),
                'total_monto': round(total_monto, 2),
                'errores': errores,
                'url_descarga': url_descarga,
            })

            logger.info(
                f"Layout {nombre_banco}: {len(empleados_validos)} empleados, "
                f"total=${total_monto:.2f}"
            )

        # Advertencia si hay empleados sin banco asignado
        if sin_banco:
            logger.warning(
                f"Período {periodo_id}: {len(sin_banco)} empleado(s) sin banco asignado — "
                f"omitidos de todos los layouts."
            )

        return resultados

    async def obtener_layouts_periodo(self, periodo_id: int) -> list[dict]:
        """
        Retorna los layouts ya generados para el período.

        Incluye URL de descarga (signed URL, válida 24h).
        """
        try:
            result = (
                self.supabase.table('dispersion_layouts')
                .select('*')
                .eq('periodo_id', periodo_id)
                .order('nombre_banco')
                .execute()
            )
            layouts = result.data or []
            # Generar signed URLs frescas para descarga
            for layout in layouts:
                layout['url_descarga'] = self._generar_url_descarga(
                    layout.get('storage_path', '')
                )
            return layouts
        except Exception as e:
            logger.error(f"Error obteniendo layouts del período {periodo_id}: {e}")
            return []

    async def generar_url_descarga(self, storage_path: str) -> str:
        """Genera una URL de descarga temporal (24h) para un layout almacenado."""
        return self._generar_url_descarga(storage_path)

    # =========================================================================
    # HELPERS PRIVADOS
    # =========================================================================

    async def _obtener_configuraciones(self, empresa_id: int) -> list[dict]:
        """Obtiene configuraciones de bancos activas de la empresa."""
        try:
            result = (
                self.supabase.table('configuracion_bancos_empresa')
                .select('*')
                .eq('empresa_id', empresa_id)
                .eq('activo', True)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Error obteniendo configuraciones banco empresa {empresa_id}: {e}")
            raise DatabaseError(f"Error obteniendo configuración bancaria: {e}")

    async def _subir_archivo(self, storage_path: str, contenido: bytes) -> str:
        """
        Sube el archivo a Supabase Storage.

        Intenta upload primero; si el archivo existe (409), hace update.
        Retorna la URL de descarga firmada.
        """
        content_type = (
            'text/csv; charset=utf-8'
            if storage_path.endswith('.csv')
            else 'text/plain; charset=latin-1'
        )
        try:
            self.supabase.storage.from_(_BUCKET).upload(
                storage_path,
                contenido,
                {'content-type': content_type, 'upsert': 'true'},
            )
        except Exception as e:
            # Intentar update si ya existe
            try:
                self.supabase.storage.from_(_BUCKET).update(
                    storage_path,
                    contenido,
                    {'content-type': content_type},
                )
            except Exception as e2:
                logger.error(f"Error subiendo layout a Storage: {e} / {e2}")
                return ''

        return self._generar_url_descarga(storage_path)

    def _generar_url_descarga(self, storage_path: str) -> str:
        """Genera URL firmada válida por 24 horas."""
        if not storage_path:
            return ''
        try:
            result = self.supabase.storage.from_(_BUCKET).create_signed_url(
                storage_path,
                86400,  # 24 horas en segundos
            )
            # supabase-py v2: result es dict con 'signedURL'
            if isinstance(result, dict):
                return result.get('signedURL') or result.get('signedUrl', '')
            return ''
        except Exception as e:
            logger.warning(f"No se pudo generar URL firmada para {storage_path}: {e}")
            return ''

    async def _registrar_layout(
        self,
        periodo_id: int,
        empresa_id: int,
        nombre_banco: str,
        nombre_archivo: str,
        storage_path: str,
        total_empleados: int,
        total_monto: float,
        errores: list[str],
        generado_por: Optional[str],
    ) -> None:
        """Upsert del registro en dispersion_layouts."""
        try:
            from datetime import datetime, timezone
            self.supabase.table('dispersion_layouts').upsert({
                'periodo_id': periodo_id,
                'empresa_id': empresa_id,
                'nombre_banco': nombre_banco,
                'nombre_archivo': nombre_archivo,
                'storage_path': storage_path,
                'total_empleados': total_empleados,
                'total_monto': round(total_monto, 2),
                'errores': errores,
                'generado_por': generado_por,
                'fecha_generacion': datetime.now(timezone.utc).isoformat(),
            }, on_conflict='periodo_id,nombre_banco').execute()
        except Exception as e:
            logger.error(f"Error registrando layout {nombre_banco} período {periodo_id}: {e}")


# Singleton
dispersion_service = DispersionService()
