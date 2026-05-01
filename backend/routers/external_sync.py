from fastapi import APIRouter
from backend.services.external import sync_external_products

router = APIRouter()


@router.post("/external-products/sync")
def post_sync_external_products():
    """_summary_: rota para sincronizar os produtos da API externa com o banco de dados local. A rota chama a função sync_external_products() para realizar a sincronização dos produtos, e retorna um dicionário indicando o número total de produtos processados (inseridos ou atualizados) no banco de dados após a sincronização com a API externa. Se ocorrer algum erro durante o processo, a rota deve lançar uma exceção apropriada.

    Returns:
        _type_: _description_: dicionário indicando o número total de produtos processados (inseridos ou atualizados) no banco de dados após a sincronização com a API externa. O campo "synced" contém o número total de produtos processados. Se ocorrer algum erro durante o processo, a rota deve lançar uma exceção apropriada.
    """
    count = sync_external_products()
    return {"synced": count}
