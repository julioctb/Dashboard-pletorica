"""
Excepciones personalizadas de la aplicación.

Este módulo define las excepciones custom que se usan en todas las capas
de la arquitectura. Sigue el patrón de herencia para facilitar el manejo.

Jerarquía de excepciones:
    ApplicationError (base)
    ├── ValidationError (errores de validación de negocio)
    ├── NotFoundError (recurso no encontrado)
    ├── DuplicateError (recurso duplicado)
    ├── DatabaseError (errores de base de datos)
    └── BusinessRuleError (reglas de negocio violadas)

Uso:
    from app.core.exceptions import NotFoundError, ValidationError

    # En Repository
    if not result.data:
        raise NotFoundError("Empresa no encontrada")

    # En Service
    if empresa.estatus != EstatusEmpresa.ACTIVO:
        raise BusinessRuleError("Solo empresas activas pueden tener empleados")

    # En State (Presentation)
    try:
        await empresa_service.crear(empresa)
    except DuplicateError as e:
        self.mostrar_mensaje(str(e), "error")
    except ValidationError as e:
        self.mostrar_mensaje(str(e), "error")
"""


class ApplicationError(Exception):
    """
    Excepción base para todos los errores de la aplicación.

    Todas las excepciones custom heredan de esta clase para facilitar
    el manejo centralizado de errores.
    """

    def __init__(self, message: str, details: dict = None):
        """
        Args:
            message: Mensaje de error legible para el usuario
            details: Diccionario con detalles adicionales del error
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        return self.message


class ValidationError(ApplicationError):
    """
    Error de validación de datos o reglas de negocio.

    Se lanza cuando los datos no cumplen con las reglas de validación
    definidas en las entidades o en la lógica de negocio.

    Ejemplos:
        - RFC con formato inválido
        - Email sin formato correcto
        - Campo requerido faltante
    """
    pass


class NotFoundError(ApplicationError):
    """
    Recurso no encontrado en la base de datos.

    Se lanza cuando se intenta acceder a un recurso que no existe.

    Ejemplos:
        - Empresa con ID 999 no existe
        - Empleado no encontrado
    """
    pass


class DuplicateError(ApplicationError):
    """
    Recurso duplicado (violación de unicidad).

    Se lanza cuando se intenta crear un recurso que viola una
    constraint de unicidad en la base de datos.

    Ejemplos:
        - RFC duplicado
        - Email ya registrado
    """

    def __init__(self, message: str, field: str = None, value: str = None):
        """
        Args:
            message: Mensaje de error
            field: Campo que viola la unicidad (ej: 'rfc')
            value: Valor duplicado (ej: 'ABC123456XYZ')
        """
        super().__init__(message, {"field": field, "value": value})
        self.field = field
        self.value = value


class DatabaseError(ApplicationError):
    """
    Error de base de datos o infraestructura.

    Se lanza cuando hay problemas de conexión, timeout, o errores
    inesperados de la base de datos.

    Ejemplos:
        - Conexión perdida con Supabase
        - Timeout en query
    """
    pass


class BusinessRuleError(ApplicationError):
    """
    Violación de regla de negocio.

    Se lanza cuando una operación viola una regla de negocio específica
    que no es una simple validación de formato.

    Ejemplos:
        - Intentar agregar empleados a empresa de tipo MANTENIMIENTO
        - Procesar nómina de empresa inactiva
    """
    pass
