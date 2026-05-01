import logging
from datetime import date, timedelta

from sqlalchemy import asc, desc, or_

from backend.db import SessionLocal
from backend.models.product import Product
from backend.schemas.products import ProductItem, ProductsResponse


def _get_period_reference_date(db) -> date:
    latest_date = db.query(Product.date).order_by(Product.date.desc()).limit(1).scalar()
    if latest_date is not None:
        return latest_date
    return date.today()


def get_products_service(period, category, region, status, search, page, page_size, sort_by, sort_order):
    """_summary_: Serviço para buscar produtos com filtros, ordenação e paginação.

    Args:
        period (_type_): _description_: Filtro de período (`30d`, `90d`, `180d`, `365d` ou `all`).
        category (_type_): _description_: Categoria específica ou `all`.
        region (_type_): _description_: Campo legado (ignorado na consulta).
        status (_type_): _description_: Status específico ou `all`.
        search (_type_): _description_: Busca textual parcial em `client` e `category`.
        page (_type_): _description_: Página atual (mínimo 1).
        page_size (_type_): _description_: Tamanho da página (mínimo 1, máximo 50).
        sort_by (_type_): _description_: Campo de ordenação (`id`, `client`, `revenue`, `date`, `category`).
        sort_order (_type_): _description_: Direção da ordenação (`asc` ou `desc`).

    Returns:
        _type_: _description_: ProductsResponse com itens paginados e metadados (`total`, `page`, `page_size`, `total_pages`).
    """
    allowed_sort = ["id", "client", "revenue", "date", "category"]
    sort_field = sort_by if sort_by in allowed_sort else "date"

    if region != "all":
        logging.warning("[DEPRECATED] region filter ignored")

    db = SessionLocal()
    try:
        query = db.query(Product)

        # Filtros
        if period != "all":
            days_map = {"30d": 30, "90d": 90, "180d": 180, "365d": 365}
            days = days_map.get(period, 365)
            reference_date = _get_period_reference_date(db)
            min_date = reference_date - timedelta(days=days)
            query = query.filter(Product.date >= min_date)
        if category != "all":
            query = query.filter(Product.category == category)
        if status != "all":
            query = query.filter(Product.status == status)
        if search:
            search_term = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    Product.client.ilike(search_term),
                    Product.category.ilike(search_term),
                )
            )

        # Ordenação
        sort_attr = getattr(Product, sort_field)
        if sort_order == "desc":
            query = query.order_by(desc(sort_attr))
        else:
            query = query.order_by(asc(sort_attr))

        # Paginação
        total = query.count()
        total_pages = max((total + page_size - 1) // page_size, 1)
        if page > total_pages:
            page = total_pages
        if page < 1:
            page = 1
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return ProductsResponse(
            items=[ProductItem(**p.to_dict()) for p in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    finally:
        db.close()
