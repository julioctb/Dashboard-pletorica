"""
Catálogo de conceptos de nómina.

Uso:
    from app.core.catalogs import CatalogoConceptosNomina
"""
from app.core.catalogs.nomina.conceptos import CatalogoConceptosNomina, ConceptoNominaDef
from app.core.catalogs.nomina.enums import CategoriaConcepto

__all__ = [
    "CatalogoConceptosNomina",
    "ConceptoNominaDef",
    "CategoriaConcepto",
]
