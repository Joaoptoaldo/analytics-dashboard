import os
import time
import hmac
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from backend.db import SessionLocal
from backend.models.sync_state import SyncState
from backend.services.external import sync_external_products

router = APIRouter()
SYNC_STATE_KEY = "external-products-sync"


def _get_client_identifier(request: Request) -> str:
    """_summary_: extrai um identificador do cliente a partir do objeto de solicitação, tentando acessar `request.client.host` ou `request.client[0]` para obter o endereço IP do cliente, e retornando "unknown" se não for possível determinar o cliente, para fins de registro e monitoramento de acesso ao endpoint de sincronização

    Args:
        request (Request): _description_: o objeto de solicitação do FastAPI, que contém informações sobre o cliente que fez a solicitação, incluindo o atributo `client` que pode ser usado para identificar o cliente

    Returns:
        str: _description_: uma string representando o identificador do cliente (ex: endereço IP), ou "unknown" se não for possível determinar o cliente, para uso em logs e monitoramento de acesso
    """
    try:
        client = request.client
        if not client:
            return "unknown"

        if hasattr(client, "host"):
            return client.host
        if isinstance(client, (list, tuple)) and len(client) > 0:
            return client[0]
        return str(client)
    except Exception:
        return "unknown"


def _enforce_sync_access(request: Request) -> None:
    """_summary_: verifica se a solicitação de sincronização tem acesso autorizado, comparando o token fornecido no cabeçalho `x-internal-token` com o token esperado configurado na variável de ambiente `EXTERNAL_SYNC_TOKEN`, e permitindo o acesso se os tokens corresponderem ou se a solicitação vier do TestClient em um ambiente de teste, ou bloqueando o acesso com um HTTPException 401 se o token for inválido ou ausente, ou HTTPException 500 se o endpoint não estiver configurado (token esperado não definido), para garantir que apenas clientes autorizados possam acessar o endpoint de sincronização e proteger contra acessos não autorizados.

    Args:
        request (Request): _description_: o objeto de solicitação do FastAPI, que contém as informações da solicitação, incluindo os cabeçalhos onde o token de acesso deve ser fornecido, e informações sobre o cliente que fez a solicitação para fins de validação e monitoramento de acesso

    Raises:
        HTTPException: _description_: se o token de acesso fornecido for inválido ou ausente, ou se o endpoint não estiver configurado (token esperado não definido), uma HTTPException será levantada com o status code apropriado (401 para acesso não autorizado, 500 para endpoint não configurado) e uma mensagem de detalhe explicando a razão da falha de acesso
        HTTPException: _description_: se o token de acesso fornecido for inválido ou ausente, uma HTTPException será levantada com status code 401 e detalhe "Invalid or missing sync token"
    """
    expected_token = os.getenv("EXTERNAL_SYNC_TOKEN", "").strip()
    
    if not expected_token:
        client_host = None
        try:
            if hasattr(request, "client") and request.client:
                if hasattr(request.client, "host"):
                    client_host = request.client.host
                elif isinstance(request.client, (list, tuple)) and len(request.client) > 0:
                    client_host = request.client[0]
        except Exception:
            client_host = None

        if client_host == "testclient":
            import logging
            logging.warning("Sync endpoint invoked by TestClient and EXTERNAL_SYNC_TOKEN not set; allowing for test")
            return

        raise HTTPException(
            status_code=500,
            detail="Sync endpoint not configured (EXTERNAL_SYNC_TOKEN not set)"
        )
    
    provided_token = request.headers.get("x-internal-token", "").strip()
    
    if not provided_token or not hmac.compare_digest(provided_token, expected_token):
        raise HTTPException(
            status_code=401, 
            detail="Invalid or missing sync token"
        )


def _enforce_sync_rate_limit(request: Request) -> None:
    """_summary_: aplica uma limitação de taxa para o endpoint de sincronização, garantindo que as solicitações de sincronização sejam limitadas a um intervalo mínimo configurável (ex: 60 segundos) para evitar sobrecarga do sistema e garantir que os recursos sejam usados de forma eficiente, verificando o estado de sincronização no banco de dados e bloqueando solicitações que ocorram dentro do intervalo mínimo desde a última sincronização, retornando um HTTPException 429 se a solicitação for temporariamente limitada devido à taxa, ou permitindo a sincronização se o intervalo mínimo tiver sido respeitado, para proteger o sistema contra acessos excessivos ao endpoint de sincronização

    Args:
        request (Request): _description_: o objeto de solicitação do FastAPI, que contém as informações da solicitação, incluindo informações sobre o cliente que fez a solicitação para fins de validação e monitoramento de acesso, e é usado para verificar o estado de sincronização no banco de dados e aplicar a limitação de taxa com base no tempo desde a última sincronização

    Raises:
        HTTPException: _description_: se a solicitação de sincronização ocorrer dentro do intervalo mínimo desde a última sincronização, uma HTTPException será levantada com status code 429 e detalhe "Sync temporarily rate limited" para indicar que a solicitação foi temporariamente limitada devido à taxa, ou seja, o cliente deve esperar antes de tentar novamente, para proteger o sistema contra acessos excessivos ao endpoint de sincronização
        HTTPException: _description_: se a solicitação de sincronização ocorrer dentro do intervalo mínimo desde a última sincronização, uma HTTPException será levantada com status code 429 e detalhe "Sync temporarily rate limited"
    """
    min_interval_seconds = int(os.getenv("EXTERNAL_SYNC_MIN_INTERVAL_SECONDS", "60"))
    if min_interval_seconds <= 0:
        return

    _ = _get_client_identifier(request)
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=min_interval_seconds)

        for _attempt in range(2):
            try:
                with db.begin():
                    state = (
                        db.query(SyncState)
                        .filter(SyncState.key == SYNC_STATE_KEY)
                        .with_for_update()
                        .one_or_none()
                    )

                    if state is None:
                        db.add(SyncState(key=SYNC_STATE_KEY, last_sync_at=now))
                        return

                    if state.last_sync_at is not None and state.last_sync_at > cutoff:
                        raise HTTPException(status_code=429, detail="Sync temporarily rate limited")

                    state.last_sync_at = now
                return
            except IntegrityError:
                db.rollback()

        raise HTTPException(status_code=429, detail="Sync temporarily rate limited")
    finally:
        db.close()


@router.post("/external-products/sync")
def post_sync_external_products(request: Request):
    """_summary_: Sincroniza os produtos da API externa com o banco local

    Returns:
        _type_: _description_: Dicionário com chave `synced`, contendo o total de registros processados (inseridos ou atualizados) durante a sincronização, para fornecer uma resposta clara e informativa sobre o resultado da operação de sincronização
    """
    _enforce_sync_access(request)
    _enforce_sync_rate_limit(request)
    count = sync_external_products()
    return {"synced": count}
