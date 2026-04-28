from fastapi import APIRouter
from backend.services.external import sync_external_products

router = APIRouter()


@router.post("/external-products/sync")
def post_sync_external_products():
    count = sync_external_products()
    return {"synced": count}
