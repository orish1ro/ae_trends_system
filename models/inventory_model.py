"""MODEL: reads/writes the Product table.

NOTE: your ERD's Product table has no "reorder_level" or "status" column,
so this file computes a stock status on the fly instead of storing one.
Change REORDER_LEVEL below if you want a different low-stock threshold."""
from datetime import datetime, timedelta

REORDER_LEVEL = 10          # below or equal to this = "Low Stock"
EXPIRING_WITHIN_DAYS = 60    # within this many days = "Expiring Soon"


def compute_status(stock_qty, expiration_date):
    """Decide a display-only status: Expired > Expiring Soon > Low Stock > In Stock."""
    if expiration_date and expiration_date not in ("-", ""):
        try:
            exp = datetime.strptime(expiration_date[:10], "%Y-%m-%d")
            days_left = (exp - datetime.now()).days
            if days_left < 0:
                return "Expired"
            if days_left <= EXPIRING_WITHIN_DAYS:
                return "Expiring Soon"
        except ValueError:
            pass  # not a recognizable date - just skip the expiry check
    return "Low Stock" if stock_qty <= REORDER_LEVEL else "In Stock"


class InventoryModel:
    def __init__(self, db_manager, staff_id=1):
        self.db = db_manager
        self.staff_id = staff_id  # who is logged in; used when adding a product

    def get_all_products(self, search="", category="All", status="All"):
        query = "SELECT * FROM Product WHERE 1=1"
        params = []
        if search:
            query += " AND ProductName LIKE ?"
            params.append(f"%{search}%")
        if category not in ("All", "Category: All"):
            query += " AND Category LIKE ?"
            params.append(f"%{category}%")
        query += " ORDER BY ProductName"

        with self.db.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()

        products = []
        for r in rows:
            computed_status = compute_status(r["StockQuantity"], r["ExpirationDate"])
            if status not in ("All", "Status: All Stock") and computed_status != status:
                continue
            products.append({
                "id": r["ProductID"],
                "name": r["ProductName"],
                "category": r["Category"] or "",
                "price": r["Price"],
                "stock_qty": r["StockQuantity"],
                "expiration_date": r["ExpirationDate"] or "-",
                "status": computed_status,
            })
        return products

    def _get_or_create_supplier(self, conn):
        """Products need a SupplierID. If none exists yet, make a placeholder."""
        row = conn.execute("SELECT SupplierID FROM Supplier LIMIT 1").fetchone()
        if row:
            return row["SupplierID"]
        cur = conn.execute(
            "INSERT INTO Supplier (SupplierName, Location) VALUES ('General Supplier', '')"
        )
        return cur.lastrowid

    def add_product(self, name, category, price, stock, reorder, exp_date):
        # 'reorder' is accepted for compatibility with the dialog, but is not
        # stored (see the note at the top of this file).
        with self.db.get_connection() as conn:
            supplier_id = self._get_or_create_supplier(conn)
            conn.execute(
                """INSERT INTO Product (SupplierID, StaffID, ProductName, Category,
                                        Price, StockQuantity, ExpirationDate)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (supplier_id, self.staff_id, name, category, price, stock,
                 None if exp_date in ("-", "") else exp_date),
            )
            conn.commit()

    def update_stock(self, product_id, qty_change):
        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE Product SET StockQuantity = StockQuantity + ? WHERE ProductID = ?",
                (qty_change, product_id),
            )
            conn.commit()
