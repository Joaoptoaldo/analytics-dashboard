import json
import sqlite3
import sys
from pathlib import Path
from statistics import mean, pstdev

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.services.analytics import get_sales_monthly, get_ticket_average


def main() -> None:
    sales = get_sales_monthly()
    ticket = get_ticket_average()

    print("SALES_STATE", sales.get("state"))
    print("TICKET_STATE", ticket.get("state"))

    sales_data = sales.get("data") or []
    ticket_data = ticket.get("data") or []
    print("SALES_POINTS", len(sales_data))
    print("TICKET_POINTS", len(ticket_data))

    conn = sqlite3.connect("backend.db")
    cur = conn.cursor()

    cur.execute(
        """
        SELECT strftime('%Y-%m', date) AS month, ROUND(SUM(revenue), 2) AS revenue, COUNT(id) AS orders
        FROM products
        WHERE date IS NOT NULL AND revenue IS NOT NULL
        GROUP BY strftime('%Y-%m', date)
        ORDER BY strftime('%Y-%m', date)
        """
    )
    raw_sales = cur.fetchall()

    cur.execute(
        """
        SELECT strftime('%Y-%m', date) AS month, ROUND(AVG(revenue), 2) AS avg_ticket, COUNT(id) AS orders
        FROM products
        WHERE date IS NOT NULL AND revenue IS NOT NULL
        GROUP BY strftime('%Y-%m', date)
        ORDER BY strftime('%Y-%m', date)
        """
    )
    raw_ticket = cur.fetchall()
    conn.close()

    sales_mismatch = []
    for index, row in enumerate(sales_data):
        if index >= len(raw_sales):
            sales_mismatch.append({"extra_endpoint_row": row})
            continue

        month, revenue, orders = raw_sales[index]
        endpoint_month = row.get("month")
        endpoint_revenue = row.get("revenue")
        endpoint_orders = row.get("orders")

        if (
            endpoint_month != month
            or (endpoint_revenue is not None and round(float(endpoint_revenue), 2) != float(revenue))
            or (endpoint_orders is not None and int(endpoint_orders) != int(orders))
        ):
            sales_mismatch.append(
                {
                    "endpoint": row,
                    "raw": {"month": month, "revenue": revenue, "orders": orders},
                }
            )

    if len(raw_sales) > len(sales_data):
        for index in range(len(sales_data), len(raw_sales)):
            sales_mismatch.append({"missing_endpoint_row": raw_sales[index]})

    ticket_mismatch = []
    for index, row in enumerate(ticket_data):
        if index >= len(raw_ticket):
            ticket_mismatch.append({"extra_endpoint_row": row})
            continue

        month, avg_ticket, orders = raw_ticket[index]
        endpoint_month = row.get("month")
        endpoint_avg_ticket = row.get("avg_ticket")
        endpoint_orders = row.get("orders")

        if (
            endpoint_month != month
            or (endpoint_avg_ticket is not None and round(float(endpoint_avg_ticket), 2) != float(avg_ticket))
            or (endpoint_orders is not None and int(endpoint_orders) != int(orders))
        ):
            ticket_mismatch.append(
                {
                    "endpoint": row,
                    "raw": {"month": month, "avg_ticket": avg_ticket, "orders": orders},
                }
            )

    if len(raw_ticket) > len(ticket_data):
        for index in range(len(ticket_data), len(raw_ticket)):
            ticket_mismatch.append({"missing_endpoint_row": raw_ticket[index]})

    revenues = [float(row[1]) for row in raw_sales if row[1] is not None]
    if revenues:
        metric_mean = mean(revenues)
        metric_std = pstdev(revenues) if len(revenues) > 1 else 0.0
        metric_cagr = None
        if len(revenues) >= 2 and revenues[0] > 0:
            years = max((len(revenues) - 1) / 12, 1 / 12)
            metric_cagr = (revenues[-1] / revenues[0]) ** (1 / years) - 1

        print("METRIC_MEAN_REVENUE", round(metric_mean, 2))
        print("METRIC_STD_REVENUE", round(metric_std, 2))
        print("METRIC_CAGR", "NA" if metric_cagr is None else round(metric_cagr * 100, 2))

    print("SALES_MISMATCH_COUNT", len(sales_mismatch))
    print("TICKET_MISMATCH_COUNT", len(ticket_mismatch))
    if sales_mismatch:
        print("SALES_MISMATCH_SAMPLE", json.dumps(sales_mismatch[:3], ensure_ascii=False))
    if ticket_mismatch:
        print("TICKET_MISMATCH_SAMPLE", json.dumps(ticket_mismatch[:3], ensure_ascii=False))


if __name__ == "__main__":
    main()