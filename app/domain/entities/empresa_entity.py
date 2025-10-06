from app.database.models.empresa_models import Empresa

class EmpresaEntity(Empresa):
    '''extiende el modelo de la logica de negocio'''

    def puede_facturar(self) -> bool:
        return self.estatus == 'ACTIVO'
    
    def puede_tener_empleados(self) -> bool:
        return self.tipo_empresa == 'NOMINA'