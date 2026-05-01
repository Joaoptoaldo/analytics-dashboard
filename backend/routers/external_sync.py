from fastapi import APIRouter

from backend.services.external import sync_external_products

router = APIRouter()


@router.post("/external-products/sync")
def post_sync_external_products():
    """_summary_: Sincroniza os produtos da API externa com o banco local.

    Returns:
        _type_: _description_: Dicionário com chave `synced`, contendo o total de registros processados (inseridos ou atualizados).
    """
    count = sync_external_products()
    return {"synced": count}
