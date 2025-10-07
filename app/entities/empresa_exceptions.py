"""
Excepciones específicas del dominio de Empresa.
"""


class EmpresaDomainException(Exception):
    """Excepción base para el dominio de Empresa"""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code or self.__class__.__name__
        super().__init__(self.message)


class EmpresaNoEncontrada(EmpresaDomainException):
    """Cuando no se encuentra una empresa solicitada"""
    def __init__(self, empresa_id: int = None, rfc: str = None):
        if empresa_id:
            message = f"Empresa con ID {empresa_id} no encontrada"
        elif rfc:
            message = f"Empresa con RFC {rfc} no encontrada"
        else:
            message = "Empresa no encontrada"
        super().__init__(message, "EMPRESA_NOT_FOUND")


class EmpresaDuplicada(EmpresaDomainException):
    """Cuando se intenta crear una empresa con RFC duplicado"""
    def __init__(self, rfc: str):
        message = f"Ya existe una empresa con RFC {rfc}"
        super().__init__(message, "EMPRESA_DUPLICATED")


class EmpresaInactiva(EmpresaDomainException):
    """Cuando se intenta operar con una empresa inactiva"""
    def __init__(self, empresa_id: int, operacion: str):
        message = f"No se puede {operacion} porque la empresa {empresa_id} está inactiva"
        super().__init__(message, "EMPRESA_INACTIVE")


class EmpresaTipoInvalido(EmpresaDomainException):
    """Cuando el tipo de empresa no permite cierta operación"""
    def __init__(self, tipo_actual: str, operacion: str):
        message = f"Empresa de tipo {tipo_actual} no puede {operacion}"
        super().__init__(message, "INVALID_EMPRESA_TYPE")


class EmpresaValidacionError(EmpresaDomainException):
    """Error de validación en datos de empresa"""
    def __init__(self, campo: str, valor: str, regla: str):
        message = f"Campo '{campo}' con valor '{valor}' no cumple: {regla}"
        super().__init__(message, "VALIDATION_ERROR")


class EmpresaOperacionNoPermitida(EmpresaDomainException):
    """Cuando se intenta una operación no permitida"""
    def __init__(self, operacion: str, razon: str):
        message = f"Operación '{operacion}' no permitida: {razon}"
        super().__init__(message, "OPERATION_NOT_ALLOWED")


# Excepciones de infraestructura
class EmpresaInfrastructureException(Exception):
    """Excepción base para errores de infraestructura"""
    pass


class EmpresaConexionError(EmpresaInfrastructureException):
    """Error de conexión con la base de datos"""
    def __init__(self, detalle: str = None):
        message = f"Error de conexión con base de datos"
        if detalle:
            message += f": {detalle}"
        super().__init__(message)


class EmpresaTimeoutError(EmpresaInfrastructureException):
    """Timeout en operación de base de datos"""
    def __init__(self, operacion: str, timeout: int):
        message = f"Timeout en operación '{operacion}' después de {timeout} segundos"
        super().__init__(message)