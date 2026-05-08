from pydantic import BaseModel
from typing import List

class ProductItem(BaseModel):
    """_summary_: modelo de item de produto, que inclui os campos `id`, `client`, `category`, `revenue`, `status`, e `date`, para representar um produto na resposta da API, permitindo uma estrutura clara e consistente para os dados de produtos retornados pelos endpoints relacionados a produtos

    Args:
        BaseModel (_type_): _description_: a classe base do Pydantic para validação e modelagem de dados, que permite definir os campos do item de produto, seus tipos, valores padrão, e realizar validação automática dos dados de resposta
    """
    id: int
    client: str
    category: str
    revenue: float
    status: str
    date: str | None

class ProductsResponse(BaseModel):
    """_summary_: modelo de resposta para o endpoint de produtos, que inclui uma lista de itens de produto, informações de paginação e o total de produtos, para fornecer uma estrutura consistente e clara para as respostas de produtos na API

    Args:
        BaseModel (_type_): _description_: a classe base do Pydantic para validação e modelagem de dados, que permite definir os campos da resposta de produtos, seus tipos, valores padrão, e realizar validação automática dos dados de resposta
    """
    items: List[ProductItem]
    total: int
    page: int
    page_size: int
    total_pages: int
