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
    "180d": "week",
    "1y": "month",
}


def _response(state: str, data: list[dict] | None = None, reason: str | None = None) -> dict:
    """_summary_: função auxiliar para formatar as respostas dos métodos de análise, garantindo uma estrutura consistente que inclui o estado do resultado (valid, no_data ou error), os dados resultantes (quando aplicável) e uma razão detalhada para casos de no_data ou error. Esta função centraliza a formatação das respostas, facilitando a manutenção e a padronização dos retornos dos métodos de análise em todo o código. O campo "data" é incluído apenas quando o estado é "valid", enquanto o campo "reason" é incluído para fornecer contexto adicional em casos de "no_data" ou "error". Esta abordagem melhora a clareza e a utilidade das respostas, permitindo que os consumidores da API entendam facilmente o resultado de cada chamada e as razões por trás de estados específicos.

    Args:
        state (str): _description_: estado do resultado (valid, no_data ou error)
        data (list[dict] | None, optional): _description_. Defaults to None.: dados resultantes (quando aplicável)
        reason (str | None, optional): _description_. Defaults to None.: razão detalhada para casos de no_data ou error


    Returns:
        dict: _description_: dicionário contendo o estado do resultado (valid, no_data ou error), os dados resultantes (quando aplicável) e uma razão detalhada para casos de no_data ou error. O campo "data" é incluído apenas quando o estado é "valid", enquanto o campo "reason" é incluído para fornecer contexto adicional em casos de "no_data" ou "error". Esta estrutura padronizada facilita a compreensão dos resultados das análises e a identificação de problemas ou situações específicas que possam ter ocorrido durante a execução dos métodos de análise.
    """
    payload = {"state": state, "data": data or []}
    if reason:
        payload["reason"] = reason
    return payload


def _month_bucket_expr(db):
    """_summary_: função auxiliar para criar uma expressão de bucketização por mês, que é utilizada em consultas SQL para agrupar os produtos por mês com base no campo date. A função detecta o tipo de banco de dados em uso e retorna a expressão apropriada para extrair o ano e o mês do campo date

    Args:
        db (_type_): _description_: sessão do banco de dados para realizar as consultas


    Returns:
        _type_: _description_: expressão de bucketização por mês
    """
    dialect_name = db.bind.dialect.name if db.bind is not None else "sqlite"
    if dialect_name == "postgresql":
        return func.to_char(Product.date, "YYYY-MM")
    return func.strftime("%Y-%m", Product.date)


def _trend_bucket_start(day: date, range_value: str) -> date:
    """_summary_: função auxiliar para determinar a data de início de um bucket de tendência, baseada em um dia e um intervalo de tempo.

    Args:
        day (date): _description_: dia para calcular o início do bucket de tendência
        range_value (str): _description_: intervalo de tempo para determinar o início do bucket de tendência


    Returns:
        date: _description_: data de início do bucket de tendência
    """
    granularity = TREND_RANGE_GRANULARITY[range_value]
    if granularity == "day":
        return day
    if granularity == "week":
        return day - timedelta(days=day.weekday())
    return day.replace(day=1)


def _trend_period_label(bucket_start: date, range_value: str) -> str:
    """_summary_: função auxiliar para formatar o rótulo de um período de tendência, baseado na data de início do bucket e no intervalo de tempo. O rótulo é formatado de acordo com a granularidade do intervalo: para buckets diários, o rótulo é a data no formato YYYY-MM-DD; para buckets semanais, o rótulo é o ano seguido da semana no formato YYYY-Www; para buckets mensais, o rótulo é o ano e mês no formato YYYY-MM.

    Args:
        bucket_start (date): _description_: data de início do bucket de tendência
        range_value (str): _description_: intervalo de tempo para determinar o formato do rótulo do período de tendência

    Returns:
        str: _description_: rótulo de período de tendência formatado
    """
    granularity = TREND_RANGE_GRANULARITY[range_value]
    if granularity == "day":
        return bucket_start.isoformat()
    if granularity == "week":
        return f"{bucket_start.isocalendar().year}-W{bucket_start.isocalendar().week:02d}"
    return bucket_start.strftime("%Y-%m")


def _trend_bucket_step(bucket_start: date, range_value: str) -> date:
    """_summary_: função auxiliar para calcular a data de início do próximo bucket de tendência, baseado na data de início do bucket atual e no intervalo de tempo.

    Args:
        bucket_start (date): _description_: data de início do bucket atual
        range_value (str): _description_: intervalo de tempo para determinar o passo para o próximo bucket de tendência

    Returns:
        date: _description_: data de início do próximo bucket de tendência
    """
    granularity = TREND_RANGE_GRANULARITY[range_value]
    if granularity == "day":
        return bucket_start + timedelta(days=1)
    if granularity == "week":
        return bucket_start + timedelta(days=7)
    if bucket_start.month == 12:
        return bucket_start.replace(year=bucket_start.year + 1, month=1, day=1)
    return bucket_start.replace(month=bucket_start.month + 1, day=1)


def get_sales_monthly() -> dict:
    """_summary_: método para obter a distribuição mensal de vendas, agrupando por mês e somando a receita total e contando o número de pedidos para cada mês. O método retorna um dicionário contendo o estado do resultado (valid, no_data ou error), uma lista de meses com a receita total e contagem de pedidos para cada mês (se o estado for valid), ou uma razão detalhada para o estado no_data ou error. O campo "data" contém a lista de meses, receitas e contagens apenas quando o estado é "valid". Se o estado for "no_data", o campo "reason" explica a ausência de dados válidos para calcular a distribuição mensal de vendas. Se o estado for "error", o campo "reason" fornece detalhes sobre a falha na consulta ou processamento.

    Returns:
        dict: _description_: dicionário contendo o estado do resultado (valid, no_data ou error), uma lista de meses com a receita total e contagem de pedidos para cada mês (se o estado for valid), ou uma razão detalhada para o estado no_data ou error. O campo "data" contém a lista de meses, receitas e contagens apenas quando o estado é "valid". Se o estado for "no_data", o campo "reason" explica a ausência de dados válidos para calcular a distribuição mensal de vendas. Se o estado for "error", o campo "reason" fornece detalhes sobre a falha na consulta ou processamento.
    """
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


def get_sales_trend(range_value: str = "30d") -> dict:
    """_summary_: método para obter a tendência de vendas em um determinado intervalo de tempo, agrupando os produtos em buckets diários, semanais ou mensais com base no intervalo selecionado. O método retorna um dicionário contendo o estado do resultado (valid, no_data ou error), uma lista de períodos com a receita total e contagem de pedidos para cada período (se o estado for valid), ou uma razão detalhada para o estado no_data ou error. O campo "data" contém a lista de períodos, receitas e contagens apenas quando o estado é "valid". Se o estado for "no_data", o campo "reason" explica a ausência de dados válidos para calcular a tendência de vendas. Se o estado for "error", o campo "reason" fornece detalhes sobre a falha na consulta ou processamento.

    Args:
        range_value (str, optional): _description_. Defaults to "30d".: intervalo de tempo para calcular a tendência de vendas, podendo ser "30d" para 30 dias, "90d" para 90 dias, "180d" para 180 dias ou "1y" para 1 ano. O intervalo selecionado determina a granularidade dos buckets (diário, semanal ou mensal) e o período de tempo considerado para a análise da tendência de vendas.

    Returns:
        dict: _description_: dicionário contendo o estado do resultado (valid, no_data ou error), uma lista de períodos com a receita total e contagem de pedidos para cada período (se o estado for valid), ou uma razão detalhada para o estado no_data ou error. O campo "data" contém a lista de períodos, receitas e contagens apenas quando o estado é "valid". Se o estado for "no_data", o campo "reason" explica a ausência de dados válidos para calcular a tendência de vendas. Se o estado for "error", o campo "reason" fornece detalhes sobre a falha na consulta ou processamento.
    """
    db = SessionLocal()
    try:
        if range_value not in TREND_RANGE_DAYS:
            logging.info(f"[ANALYTICS][sales/trend] invalid range: {range_value}")
            return _response("error", reason="invalid_range")

        rows = (
            db.query(Product.date.label("date"), Product.revenue.label("revenue"))
            .filter(Product.date.isnot(None))
            .filter(Product.revenue.isnot(None))
            .all()
        )

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
        granularity = TREND_RANGE_GRANULARITY[range_value]

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

        if granularity == "day":
            start_bucket = cutoff_date
        elif granularity == "week":
            start_bucket = cutoff_date - timedelta(days=cutoff_date.weekday())
        else:
            start_bucket = cutoff_date.replace(day=1)

        end_bucket = _trend_bucket_start(latest_date, range_value)
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
    except Exception:
        logging.exception("[ANALYTICS][sales/trend] error")
        return {"state": "error", "range": range_value, "reason": "query_failed", "data": []}
    finally:
        db.close()


def get_distribution_category() -> dict:
    """_summary_: método para obter a distribuição de produtos por categoria, agrupando os produtos por categoria e contando o número de produtos em cada categoria. O método retorna um dicionário contendo o estado do resultado (valid, no_data ou error), uma lista de categorias com a contagem de produtos para cada categoria (se o estado for valid), ou uma razão detalhada para o estado no_data ou error. O campo "data" contém a lista de categorias e contagens apenas quando o estado é "valid". Se o estado for "no_data", o campo "reason" explica a ausência de dados válidos para calcular a distribuição por categoria. Se o estado for "error", o campo "reason" fornece detalhes sobre a falha na consulta ou processamento.

    Returns:
        dict: _description_: dicionário contendo o estado do resultado (valid, no_data ou error), uma lista de categorias com a contagem de produtos para cada categoria (se o estado for valid), ou uma razão detalhada para o estado no_data ou error. O campo "data" contém a lista de categorias e contagens apenas quando o estado é "valid". Se o estado for "no_data", o campo "reason" explica a ausência de dados válidos para calcular a distribuição por categoria. Se o estado for "error", o campo "reason" fornece detalhes sobre a falha na consulta ou processamento.
    """
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
    """_summary_: método para obter os produtos com maior receita, ordenando por receita de forma decrescente e utilizando o campo date como critério de desempate (mais recente primeiro). O método retorna uma lista dos top N produtos, onde N é definido pelo parâmetro limit. Cada produto na lista inclui os campos product_id, product_name, category, revenue, status, date e date_source. Se não houver registros com receita válida, ou se a consulta falhar, o método retorna um estado apropriado indicando a situação (no_data ou error) junto com uma razão detalhada.

    Args:
        limit (int, optional): _description_. Defaults to 10.: número de produtos a serem retornados na lista dos top produtos, ordenados por receita. O valor deve ser um inteiro positivo, e o método deve garantir que o resultado contenha no máximo esse número de produtos. Se o valor fornecido for inválido (por exemplo, negativo ou zero), o método deve retornar um estado de erro com uma razão indicando "invalid_limit".

    Returns:
        dict: _description_: dicionário contendo o estado do resultado (valid, no_data ou error), uma lista de produtos com os campos product_id, product_name, category, revenue, status, date e date_source (se o estado for valid), ou uma razão detalhada para o estado no_data ou error. O campo "data" contém a lista de produtos apenas quando o estado é "valid". Se o estado for "no_data", o campo "reason" explica a ausência de dados válidos. Se o estado for "error", o campo "reason" fornece detalhes sobre a falha na consulta ou processamento.
    """
    db = SessionLocal()
    try:
        if limit <= 0:
            return _response("error", reason="invalid_limit")

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
    """_summary_: método para calcular o ticket médio dos produtos, que é definido como a média da receita (revenue) dos produtos. O método consulta o banco de dados para obter os valores de receita, calcula a média e retorna um dicionário contendo o valor do ticket médio, o estado do resultado (valid, no_data ou error), e uma razão detalhada em caso de no_data ou error. Se não houver registros com receita válida, o método retorna um estado de no_data com uma razão indicando "no_valid_revenue". Se ocorrer algum erro durante a consulta ou processamento, o método retorna um estado de error com uma razão indicando "query_failed". O campo "data" contém o valor do ticket médio apenas quando o estado é "valid".

    Returns:
        dict: _description_: dicionário contendo o valor do ticket médio, o estado do resultado (valid, no_data ou error), e uma razão detalhada em caso de no_data ou error. Se o estado for "valid", o campo "data" é uma lista com um único dicionário contendo a chave "ticket_average" com o valor do ticket médio calculado, e a chave "records" indicando o número de registros considerados no cálculo. Se o estado for "no_data", o campo "reason" explica a ausência de dados válidos para calcular o ticket médio. Se o estado for "error", o campo "reason" fornece detalhes sobre a falha na consulta ou processamento.
    """
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
    """_summary_: método para obter a distribuição mensal de clientes, agrupando por mês e contando o número de clientes distintos (baseado no campo client) para cada mês. O método retorna um dicionário contendo o estado do resultado (valid, no_data ou error), uma lista de meses com a contagem de clientes para cada mês (se o estado for valid), ou uma razão detalhada para o estado no_data ou error. O campo "data" contém a lista de meses e contagens apenas quando o estado é "valid". Se o estado for "no_data", o campo "reason" explica a ausência de dados válidos para calcular a distribuição mensal de clientes. Se o estado for "error", o campo "reason" fornece detalhes sobre a falha na consulta ou processamento. Este método é semanticamente inválido, pois o campo client representa o nome do produto e não um cliente real, portanto, ele retorna um estado de error com uma razão indicando "semantically_invalid: client_is_product_name".

    Returns:
        dict: _description_: dicionário contendo o estado do resultado (valid, no_data ou error), uma lista de meses com a contagem de clientes para cada mês (se o estado for valid), ou uma razão detalhada para o estado no_data ou error. O campo "data" contém a lista de meses e contagens apenas quando o estado é "valid". Se o estado for "no_data", o campo "reason" explica a ausência de dados válidos para calcular a distribuição mensal de clientes. Se o estado for "error", o campo "reason" fornece detalhes sobre a falha na consulta ou processamento. Este método é semanticamente inválido, pois o campo client representa o nome do produto e não um cliente real, portanto, ele retorna um estado de error com uma razão indicando "semantically_invalid: client_is_product_name".
    """
    logging.warning(
        "[ANALYTICS][customers/monthly] semantically invalid: 'client' represents product name, not a real customer"
    )
    return _response(
        "error",
        reason="semantically_invalid: client_is_product_name",
    )