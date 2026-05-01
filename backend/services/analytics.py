import logging

from sqlalchemy import desc, func, nullslast

from backend.db import SessionLocal
from backend.models.product import Product

DATE_SOURCE = "external.meta.createdAt"


def _response(state: str, data: list[dict] | None = None, reason: str | None = None) -> dict:
    payload = {"state": state, "data": data or []}
    if reason:
        payload["reason"] = reason
    return payload


def _month_bucket_expr(db):
    dialect_name = db.bind.dialect.name if db.bind is not None else "sqlite"
    if dialect_name == "postgresql":
        return func.to_char(Product.date, "YYYY-MM")
    return func.strftime("%Y-%m", Product.date)


def get_sales_monthly() -> dict:
    db = SessionLocal()
    try:
        valid_count = db.query(func.count(Product.id)).filter(Product.date.isnot(None)).scalar() or 0
        logging.info(f"[ANALYTICS][sales/monthly] valid_count: {valid_count}")
        if valid_count == 0:
            logging.info("[ANALYTICS][sales/monthly] no_data: no records with valid date")
            return _response("no_data", reason="no_valid_date")

        month_expr = _month_bucket_expr(db)
        rows = (
            db.query(
                month_expr.label("month"),
                func.sum(Product.revenue).label("revenue"),
                func.count(Product.id).label("orders"),
            )
            .filter(Product.date.isnot(None))
            .group_by(month_expr)
            .order_by(month_expr.asc())
            .all()
        )
        logging.info(f"[ANALYTICS][sales/monthly] rows after grouping: {len(rows)}")

        if not rows:
            logging.info("[ANALYTICS][sales/monthly] no_data: grouped query returned no rows")
            return _response("no_data", reason="no_grouped_rows")

        data = [
            {
                "month": row.month,
                "revenue": float(row.revenue) if row.revenue is not None else None,
                "orders": int(row.orders) if row.orders is not None else None,
                "date_source": DATE_SOURCE,
            }
            for row in rows
        ]
        return _response("valid", data=data)
    except Exception:
        logging.exception("[ANALYTICS][sales/monthly] error")
        return _response("error", reason="query_failed")
    finally:
        db.close()


def get_distribution_category() -> dict:
    db = SessionLocal()
    try:
        valid_count = db.query(func.count(Product.id)).scalar() or 0
        if valid_count == 0:
            logging.info("[ANALYTICS][distribution/category] no_data: empty dataset")
            return _response("no_data", reason="empty_dataset")

        rows = (
            db.query(
                Product.category.label("category"),
                func.count(Product.id).label("count"),
            )
            .group_by(Product.category)
            .order_by(nullslast(desc(func.count(Product.id))))
            .all()
        )

        if not rows:
            logging.info("[ANALYTICS][distribution/category] no_data: grouped query returned no rows")
            return _response("no_data", reason="no_grouped_rows")

        data = [
            {
                "category": row.category,
                "count": int(row.count),
            }
            for row in rows
        ]
        return _response("valid", data=data)
    except Exception:
        logging.exception("[ANALYTICS][distribution/category] error")
        return _response("error", reason="query_failed")
    finally:
        db.close()


def get_top_products(limit: int = 10) -> dict:
    db = SessionLocal()
    try:
        valid_count = db.query(func.count(Product.id)).filter(Product.revenue.isnot(None)).scalar() or 0
        if valid_count == 0:
            logging.info("[ANALYTICS][top/products] no_data: no records with valid revenue")
            return _response("no_data", reason="no_valid_revenue")

        rows = (
            db.query(
                Product.id.label("product_id"),
                Product.client.label("product_name"),
                Product.category.label("category"),
                Product.revenue.label("revenue"),
                Product.status.label("status"),
                Product.date.label("date"),
            )
            .filter(Product.revenue.isnot(None))
            .order_by(
                nullslast(desc(Product.revenue)),
                nullslast(desc(Product.date)),
                Product.id.asc(),
            )
            .limit(limit)
            .all()
        )

        if not rows:
            logging.info("[ANALYTICS][top/products] no_data: sorted query returned no rows")
            return _response("no_data", reason="no_grouped_rows")

        data = [
            {
                "product_id": row.product_id,
                "product_name": row.product_name,
                "category": row.category,
                "revenue": float(row.revenue) if row.revenue is not None else None,
                "status": row.status,
                "date": row.date.strftime("%Y-%m-%d") if row.date else None,
                "date_source": DATE_SOURCE if row.date else None,
            }
            for row in rows
        ]
        return _response("valid", data=data)
    except Exception:
        logging.exception("[ANALYTICS][top/products] error")
        return _response("error", reason="query_failed")
    finally:
        db.close()


def get_ticket_average() -> dict:
    db = SessionLocal()
    try:
        avg_value = (
            db.query(func.avg(Product.revenue))
            .filter(Product.revenue.isnot(None))
            .scalar()
        )
        valid_count = db.query(func.count(Product.id)).filter(Product.revenue.isnot(None)).scalar() or 0

        if avg_value is None or valid_count == 0:
            logging.info("[ANALYTICS][metrics/ticket-average] no_data: no revenue available")
            return _response("no_data", reason="no_valid_revenue")

        data = [
            {
                "ticket_average": round(float(avg_value), 2),
                "records": int(valid_count),
            }
        ]
        return _response("valid", data=data)
    except Exception:
        logging.exception("[ANALYTICS][metrics/ticket-average] error")
        return _response("error", reason="query_failed")
    finally:
        db.close()


def get_customers_monthly() -> dict:
    logging.warning(
        "[ANALYTICS][customers/monthly] semantically invalid: 'client' represents product name, not a real customer"
    )
    return _response(
        "error",
        reason="semantically_invalid: client_is_product_name",
    )