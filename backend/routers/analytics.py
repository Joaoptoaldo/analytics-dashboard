from fastapi import APIRouter, Query

from backend.schemas.analytics import AnalyticsResponse
from backend.services.analytics import (
    get_customers_monthly,
    get_distribution_category,
    get_sales_monthly,
    get_ticket_average,
    get_top_products,
)

router = APIRouter()


@router.get("/sales/monthly", response_model=AnalyticsResponse)
def sales_monthly_router():
    return get_sales_monthly()


@router.get("/distribution/category", response_model=AnalyticsResponse)
def distribution_category_router():
    return get_distribution_category()


@router.get("/top/products", response_model=AnalyticsResponse)
def top_products_router(limit: int = Query(default=10, ge=1, le=50)):
    return get_top_products(limit=limit)


@router.get("/metrics/ticket-average", response_model=AnalyticsResponse)
def ticket_average_router():
    return get_ticket_average()


@router.get("/customers/monthly", response_model=AnalyticsResponse)
def customers_monthly_router():
    return get_customers_monthly()
