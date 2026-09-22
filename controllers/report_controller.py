import csv

from models.inventory_model import compute_status
from models.transaction_model import TransactionModel, nice_date


class ReportController:
    def __init__(self, db, report_view, dashboard_view):
        self.db = db
        self.report_view = report_view
        self.dashboard_view = dashboard_view
        self.txn_model = TransactionModel(db)
        self.current_rows = []
        self.report_view.filters_changed.connect(self.load_reports)
        self.report_view.export_requested.connect(self.export_report)

    def load_reports(self, from_date=None, to_date=None):
        if from_date is None:
            from_date = self.report_view.from_date.date().toString("yyyy-MM-dd")
        if to_date is None:
            to_date = self.report_view.to_date.date().toString("yyyy-MM-dd")

        with self.db.get_connection() as conn:
            order_rows = conn.execute(
                """
                SELECT o.OrderID, o.OrderDate, o.TotalAmount, o.OrderStatus,
                       c.FullName AS CustomerName, pl.PlatformName,
                       COALESCE(SUM(od.Quantity), 0) AS UnitsSold
                FROM Orders o
                JOIN Customer c ON c.CustomerID = o.CustomerID
                JOIN Platform pl ON pl.PlatformID = o.PlatformID
                LEFT JOIN OrderDetails od ON od.OrderID = o.OrderID
                WHERE date(o.OrderDate) BETWEEN date(?) AND date(?)
                GROUP BY o.OrderID
                ORDER BY o.OrderID DESC
                """,
                (from_date, to_date),
            ).fetchall()
            products = [dict(row) for row in conn.execute("SELECT * FROM Product")]

        rows = []
        for order in order_rows:
            rows.append({
                "order": f"ORD-{order['OrderID']:04d}",
                "date": nice_date(order["OrderDate"]),
                "customer": order["CustomerName"],
                "type": "Walk-in" if order["PlatformName"] == "Walk-in" else "Online",
                "items": order["UnitsSold"],
                "total": order["TotalAmount"] or 0.0,
                "status": order["OrderStatus"],
            })

        total_sales = sum(row["total"] for row in rows)
        units_sold = sum(row["items"] for row in rows)
        low_stock_items = []
        expiring_count = 0
        for product in products:
            status = compute_status(product["StockQuantity"], product["ExpirationDate"])
            if status in ("Low Stock", "Expired", "Expiring Soon"):
                low_stock_items.append({
                    "name": product["ProductName"],
                    "category": product["Category"] or "",
                    "stock_qty": product["StockQuantity"],
                    "reorder_level": 10,
                })
            if status in ("Expiring Soon", "Expired"):
                expiring_count += 1

        self.current_rows = rows
        self.report_view.display_report(
            rows, total_sales, len(rows), units_sold, len(low_stock_items)
        )
        self.report_view.display_low_stock(low_stock_items)
        self.dashboard_view.display_recent_transactions(self.txn_model.get_recent_orders(6))
        self.dashboard_view.update_metrics(
            total_sales, len(low_stock_items),
            sum(1 for row in rows if row["status"] == "Pending"),
            expiring_count,
        )

    def export_report(self, path):
        headers = ["Order", "Date", "Customer", "Type", "Items", "Total", "Status"]
        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
            for row in self.current_rows:
                writer.writerow({
                    "Order": row["order"],
                    "Date": row["date"],
                    "Customer": row["customer"],
                    "Type": row["type"],
                    "Items": row["items"],
                    "Total": f"{row['total']:.2f}",
                    "Status": row["status"],
                })
