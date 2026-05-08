from typing import Any, Literal
from pydantic import BaseModel, Field


class AnalyticsResponse(BaseModel):
    """_summary_: modelo de resposta para endpoints de análise, que inclui o estado da resposta (válida, sem dados ou erro), uma mensagem de motivo opcional, e os dados da análise em formato de lista de dicionários, para fornecer uma estrutura consistente para as respostas de análise na API

    Args:
        BaseModel (_type_): _description_: a classe base do Pydantic para validação e modelagem de dados, que permite definir os campos da resposta, seus tipos, valores padrão, e realizar validação automática dos dados de resposta
    """
    state: Literal["valid", "no_data", "error"]
    reason: str | None = None
    data: list[dict[str, Any]] = Field(default_factory=list)


class SalesTrendPoint(BaseModel):
    """_summary_: modelo para representar um ponto de tendência de vendas, que inclui o período (ex: "2024-05"), a receita total para aquele período, e o número de pedidos, para fornecer uma estrutura clara e consistente para os dados de tendência de vendas retornados pela API

    Args:
        BaseModel (_type_): _description_: a classe base do Pydantic para validação e modelagem de dados, que permite definir os campos do ponto de tendência, seus tipos, valores padrão, e realizar validação automática dos dados
    """
    period: str
    revenue: float | None = None
    orders: int | None = None


class SalesTrendResponse(BaseModel):
    """_summary_: modelo de resposta para o endpoint de tendência de vendas, que inclui o estado da resposta (válida, sem dados ou erro), o período da tendência (ex: "30d", "90d", "180d", "1y"), uma mensagem de motivo opcional, e os dados da tendência em formato de lista de pontos de tendência, para fornecer uma estrutura consistente e clara para as respostas de análise de tendência de vendas na API

    Args:
        BaseModel (_type_): _description_: a classe base do Pydantic para validação e modelagem de dados, que permite definir os campos da resposta de tendência de vendas, seus tipos, valores padrão, e realizar validação automática dos dados de resposta
    """
    state: Literal["valid", "no_data", "error"]
    range: Literal["30d", "90d", "180d", "1y"]
    reason: str | None = None
    data: list[SalesTrendPoint] = Field(default_factory=list)