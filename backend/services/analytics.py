import logging
from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import desc, func, nullslast

from backend.db import SessionLocal
from backend.models.product import Product

DATE_SOURCE = "external.meta.createdAt"
TREND_RANGE_DAYS = {
    "30d": 30,
    "90d": 90,
    "180d": 180,
    "1y": 365,
}
TREND_RANGE_GRANULARITY = {
    "30d": "day",
    "90d": "day",
    "180d": "day",
    "1y": "day",
}


def _response(state: str, data: list[dict] | None = None, reason: str | None = None) -> dict:
    """_summary_: Formata respostas padronizadas das funcoes de analytics.

    Args:
        state (str): _description_: Estado da operacao (`valid`, `no_data` ou `error`).
        data (list[dict] | None, optional): _description_. Lista de itens de resposta. Defaults to None.
        reason (str | None, optional): _description_. Motivo detalhado para `no_data` ou `error`. Defaults to None.

    Returns:
        dict: _description_: Dicionario no formato `{"state": state, "data": [...]}` e, quando informado, o campo `reason`.
    """
    payload = {"state": state, "data": data or []}
    if reason:
        payload["reason"] = reason
    return payload


def _month_bucket_expr(db):
    """_summary_: Cria expressao SQL para agrupar datas por mes.

    Args:
        db (_type_): _description_: Sessao/engine usada para detectar o dialeto do banco.

    Returns:
        _type_: _description_: Expressao SQL equivalente a `YYYY-MM` para PostgreSQL ou SQLite.
    """
    dialect_name = db.bind.dialect.name if db.bind is not None else "sqlite"
    if dialect_name == "postgresql":
        return func.to_char(Product.date, "YYYY-MM")
    return func.strftime("%Y-%m", Product.date)


def _trend_bucket_start(day: date, range_value: str) -> date:
    """_summary_: Calcula o inicio do bucket temporal conforme a granularidade do range.

    Args:
        day (date): _description_: Data de referencia.
        range_value (str): _description_: Intervalo (`30d`, `90d`, `180d`, `1y`).

    Returns:
        date: _description_: Data de inicio do bucket (dia, semana ou mes).
    """
    granularity = TREND_RANGE_GRANULARITY[range_value]
    if granularity == "day":
        return day
    return day


def _trend_period_label(bucket_start: date, range_value: str) -> str:
    """_summary_: Formata o rotulo do bucket para retorno da serie de tendencia.

    Args:
        bucket_start (date): _description_: Data de inicio do bucket.
        range_value (str): _description_: Intervalo (`30d`, `90d`, `180d`, `1y`).

    Returns:
        str: _description_: Rotulo no formato `YYYY-MM-DD`, `YYYY-Www` ou `YYYY-MM`.
    """
    granularity = TREND_RANGE_GRANULARITY[range_value]
    if granularity == "day":
        return bucket_start.isoformat()
    return bucket_start.isoformat()


def _trend_bucket_step(bucket_start: date, range_value: str) -> date:
    """_summary_: Avanca para o proximo bucket temporal da serie de tendencia.

    Args:
        bucket_start (date): _description_: Data de inicio do bucket atual.
        range_value (str): _description_: Intervalo (`30d`, `90d`, `180d`, `1y`).

    Returns:
        date: _description_: Data de inicio do proximo bucket.
    """
    granularity = TREND_RANGE_GRANULARITY[range_value]
    if granularity == "day":
        return bucket_start + timedelta(days=1)
    return bucket_start + timedelta(days=1)


def get_sales_monthly(period: str = "all", category: str = "all", status: str = "all", search: str = "") -> dict:
    """_summary_: Calcula a receita mensal agregada por mes com contagem de pedidos.

    Returns:
        dict: _description_: Resposta padronizada com `state` e `data`. Quando `valid`, cada item de `data` contem `month`, `revenue`, `orders` e `date_source`.
    """
    db = SessionLocal()
    try:
        # build base query and apply filters (period, category, status, search)
        # Always exclude synthetic (test) data by default
        base_query = db.query(Product).filter(Product.date.isnot(None), Product.is_synthetic == False)
        if period != "all":
            days_map = {"30d": 30, "90d": 90, "180d": 180, "1y": 365, "365d": 365}
            days = days_map.get(period, 365)
            latest_date = db.query(func.max(Product.date)).scalar()
            if latest_date is not None:
                min_date = latest_date - timedelta(days=days - 1)
                base_query = base_query.filter(Product.date >= min_date)
        if category != "all":
            base_query = base_query.filter(Product.category == category)
        if status != "all":
            base_query = base_query.filter(Product.status == status)
        if search:
            search_term = f"%{search.strip().lower()}%"
            base_query = base_query.filter(
                Product.client.ilike(search_term) | Product.category.ilike(search_term)
            )

        valid_count = base_query.with_entities(func.count(Product.id)).scalar() or 0
        logging.info(f"[ANALYTICS][sales/monthly] valid_count: {valid_count}")
        if valid_count == 0:
            logging.info("[ANALYTICS][sales/monthly] no_data: no records with valid date")
            return _response("no_data", reason="no_valid_date")

        month_expr = _month_bucket_expr(db)
        rows = (
            base_query.with_entities(
                month_expr.label("month"),
                func.sum(Product.revenue).label("revenue"),
                func.count(Product.id).label("orders"),
            )
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
    except Exception as exc:
        logging.error(f"[ANALYTICS][sales/monthly] error: {exc.__class__.__name__}", exc_info=False)
        return _response("error", reason="query_failed")
    finally:
        db.close()


def get_sales_trend(range_value: str = "30d", period: str = "all", category: str = "all", status: str = "all", search: str = "") -> dict:
    """_summary_: Calcula serie de tendencia de receita/pedidos para uma janela temporal.

    Args:
        range_value (str, optional): _description_. Intervalo (`30d`, `90d`, `180d`, `1y`). Defaults to "30d".

    Returns:
        dict: _description_: Objeto com `state`, `range` e serie em `data` (`period`, `revenue`, `orders`).
    """
    db = SessionLocal()
    try:
        if range_value not in TREND_RANGE_DAYS:
            logging.info(f"[ANALYTICS][sales/trend] invalid range: {range_value}")
            return _response("error", reason="invalid_range")

    
        base_query = db.query(Product.date.label("date"), Product.revenue.label("revenue")).filter(Product.date.isnot(None)).filter(Product.revenue.isnot(None)).filter(Product.is_synthetic == False)
        if period != "all":
            days_map = {"30d": 30, "90d": 90, "180d": 180, "1y": 365, "365d": 365}
            days = days_map.get(period, 365)
            latest_date = db.query(func.max(Product.date)).scalar()
            if latest_date is not None:
                min_date = latest_date - timedelta(days=days - 1)
                base_query = base_query.filter(Product.date >= min_date)
        if category != "all":
            base_query = base_query.filter(Product.category == category)
        if status != "all":
            base_query = base_query.filter(Product.status == status)
        if search:
            search_term = f"%{search.strip().lower()}%"
            base_query = base_query.filter(Product.client.ilike(search_term) | Product.category.ilike(search_term))

        rows = base_query.all()

        if not rows:
            logging.info("[ANALYTICS][sales/trend] no_data: no valid rows in database")
            return {"state": "no_data", "range": range_value, "reason": "no_valid_data_in_range", "data": []}

        dates = [row.date for row in rows if row.date is not None]
        if not dates:
            logging.info("[ANALYTICS][sales/trend] no_data: date list is empty after filtering")
            return {"state": "no_data", "range": range_value, "reason": "no_valid_data_in_range", "data": []}

        latest_date = max(dates)
        window_days = TREND_RANGE_DAYS[range_value]
        cutoff_date = latest_date - timedelta(days=window_days - 1)
        buckets: dict[date, dict[str, float | int]] = defaultdict(lambda: {"revenue": 0.0, "orders": 0})
        for row in rows:
            if row.date is None:
                continue
            if row.date < cutoff_date or row.date > latest_date:
                continue

            bucket_start = _trend_bucket_start(row.date, range_value)
            bucket = buckets[bucket_start]
            bucket["revenue"] = float(bucket["revenue"] or 0.0) + float(row.revenue or 0.0)
            bucket["orders"] = int(bucket["orders"] or 0) + 1

        if not buckets:
            logging.info("[ANALYTICS][sales/trend] no_data: no rows inside selected range")
            return {"state": "no_data", "range": range_value, "reason": "no_valid_data_in_range", "data": []}

        start_bucket = cutoff_date
        end_bucket = latest_date
        data = []
        current_bucket = start_bucket
        while current_bucket <= end_bucket:
            bucket = buckets.get(current_bucket, {"revenue": 0.0, "orders": 0})
            data.append(
                {
                    "period": _trend_period_label(current_bucket, range_value),
                    "revenue": round(float(bucket["revenue"] or 0.0), 2),
                    "orders": int(bucket["orders"] or 0),
                }
            )
            current_bucket = _trend_bucket_step(current_bucket, range_value)

        if len(data) <= 1:
            logging.info("[ANALYTICS][sales/trend] no_data: continuous series collapsed to one point")
            return {"state": "no_data", "range": range_value, "reason": "no_valid_data_in_range", "data": []}

        return {"state": "valid", "range": range_value, "data": data}
    except Exception as exc:
        logging.error(f"[ANALYTICS][sales/trend] error: {exc.__class__.__name__}", exc_info=False)
        return {"state": "error", "range": range_value, "reason": "query_failed", "data": []}
    finally:
        db.close()


def get_distribution_category() -> dict:
    """_summary_: Agrupa registros por categoria e retorna a distribuicao de frequencia.

    Returns:
        dict: _description_: Resposta padronizada com `state` e `data`. Quando `valid`, cada item contem `category` e `count`.
    """
    db = SessionLocal()
    try:
        valid_count = db.query(func.count(Product.id)).filter(Product.is_synthetic == False).scalar() or 0
        if valid_count == 0:
            logging.info("[ANALYTICS][distribution/category] no_data: empty dataset")
            return _response("no_data", reason="empty_dataset")

        rows = (
            db.query(
                Product.category.label("category"),
                func.count(Product.id).label("count"),
            )
            .filter(Product.is_synthetic == False)
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
    except Exception as exc:
        logging.error(f"[ANALYTICS][distribution/category] error: {exc.__class__.__name__}", exc_info=False)
        return _response("error", reason="query_failed")
    finally:
        db.close()


def get_top_products(limit: int = 10) -> dict:
    """_summary_: Retorna os itens de maior receita ordenados de forma decrescente.

    Args:
        limit (int, optional): _description_. Quantidade maxima de registros retornados. Defaults to 10.

    Returns:
        dict: _description_: Resposta padronizada com `state` e `data`. Quando `valid`, cada item contem `product_id`, `product_name`, `category`, `revenue`, `status`, `date` e `date_source`.
    """
    db = SessionLocal()
    try:
        if limit <= 0:
            return _response("error", reason="invalid_limit")

        valid_count = db.query(func.count(Product.id)).filter(Product.revenue.isnot(None), Product.is_synthetic == False).scalar() or 0
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
            .filter(Product.revenue.isnot(None), Product.is_synthetic == False)
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
    except Exception as exc:
        logging.error(f"[ANALYTICS][top/products] error: {exc.__class__.__name__}", exc_info=False)
        return _response("error", reason="query_failed")
    finally:
        db.close()


def get_ticket_average() -> dict:
    """_summary_: Calcula o TICKET REAL mensal = SUM(revenue) / COUNT(DISTINCT client).
    
    O ticket real representa a receita média por cliente único no mês.
    Fórmula: Ticket Real = SUM(revenue) / COUNT(DISTINCT clients)

    Returns:
        dict: _description_: Resposta padronizada com `state` e `data`. Quando `valid`, cada item contem `month`, `avg_ticket` (ticket real), `distinct_clients`, `orders` e `date_source`.
    """
    db = SessionLocal()
    try:
        valid_count = (
            db.query(func.count(Product.id))
            .filter(Product.date.isnot(None))
            .filter(Product.revenue.isnot(None))
            .scalar()
            or 0
        )
        if valid_count == 0:
            logging.info("[ANALYTICS][metrics/ticket-average] no_data: no records with valid date and revenue")
            return _response("no_data", reason="no_valid_date_or_revenue")

        month_expr = _month_bucket_expr(db)
        rows = (
            db.query(
                month_expr.label("month"),
                func.sum(Product.revenue).label("total_revenue"),
                func.count(func.distinct(Product.client)).label("distinct_clients"),
                func.count(Product.id).label("orders"),
            )
            .filter(Product.date.isnot(None))
            .filter(Product.revenue.isnot(None))
            .group_by(month_expr)
            .order_by(month_expr.asc())
            .all()
        )

        if not rows:
            logging.info("[ANALYTICS][metrics/ticket-average] no_data: grouped query returned no rows")
            return _response("no_data", reason="no_grouped_rows")

        data = [
            {
                "month": row.month,
                "avg_ticket": round(
                    float(row.total_revenue) / int(row.distinct_clients), 2
                ) if (row.total_revenue is not None and row.distinct_clients and row.distinct_clients > 0) else None,
                "distinct_clients": int(row.distinct_clients) if row.distinct_clients is not None else 0,
                "orders": int(row.orders) if row.orders is not None else None,
                "date_source": DATE_SOURCE,
            }
            for row in rows
        ]
        return _response("valid", data=data)
    except Exception as exc:
        logging.error(f"[ANALYTICS][metrics/ticket-average] error: {exc.__class__.__name__}", exc_info=False)
        return _response("error", reason="query_failed")
    finally:
        db.close()


def get_customers_monthly() -> dict:
    """_summary_: Endpoint semantico invalido no contexto atual dos dados.

    Returns:
        dict: _description_: Resposta em estado `error` com reason `semantically_invalid: client_is_product_name`, pois `client` representa nome de produto.
    """
    logging.warning(
        "[ANALYTICS][customers/monthly] semantically invalid: 'client' represents product name, not a real customer"
    )
    return _response(
        "error",
        reason="semantically_invalid: client_is_product_name",
    )
