"""CONTROLLER: builds the Dashboard and Reports screens from real tables."""
from models.inventory_model import compute_status
from models.transaction_model import TransactionModel


class ReportController:
    def __init__(self, db, report_view, dashboard_view):
        self.db = db
        self.report_view = report_view
        self.dashboard_view = dashboard_view
        self.txn_model = TransactionModel(db)  # only used for read-only reporting

    def load_reports(self):
        with self.db.get_connection() as conn:
            products = [dict(r) for r in conn.execute("SELECT * FROM Product")]
            total_sales = conn.execute(
                "SELECT COALESCE(SUM(TotalAmount), 0) FROM Orders"
            ).fetchone()[0]
            pending_orders = conn.execute(
                "SELECT COUNT(*) FROM Orders WHERE OrderStatus = 'Pending'"
            ).fetchone()[0]

        low_stock_items = []
        expiring_count = 0
        for p in products:
            status = compute_status(p["StockQuantity"], p["ExpirationDate"])
            if status in ("Low Stock", "Expired", "Expiring Soon"):
                low_stock_items.append({
                    "name": p["ProductName"],
                    "category": p["Category"] or "",
                    "stock_qty": p["StockQuantity"],
                    "reorder_level": 10,  # see the note in inventory_model.py
                })
            if status in ("Expiring Soon", "Expired"):
                expiring_count += 1

        recent_orders = self.txn_model.get_recent_orders(6)

        self.dashboard_view.update_metrics(
            total_sales, len(low_stock_items), pending_orders, expiring_count
        )
        self.dashboard_view.display_recent_transactions(recent_orders)
        self.report_view.display_low_stock(low_stock_items)
