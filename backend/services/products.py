from backend.schemas.products import ProductsResponse, ProductItem
from backend.db import SessionLocal
from backend.models.product import Product
from sqlalchemy import or_, desc, asc
from datetime import datetime, timedelta
import logging

def get_products_service(period, category, region, status, search, page, page_size, sort_by, sort_order):
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
            min_date = datetime.now().date() - timedelta(days=days)
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
