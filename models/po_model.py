"""MODEL: reads/writes PurchaseOrder and PurchaseOrderDetails.

The Purchase Orders screen currently takes one quick item line (name, qty,
unit cost) per PO, so each PO here gets exactly one PurchaseOrderDetails row."""
from datetime import datetime


def po_number(po_id):
    return f"PO-{po_id:04d}"


def nice_date(iso_text):
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(iso_text[:19], fmt).strftime("%b %d, %Y")
        except (ValueError, TypeError):
            continue
    return iso_text or ""


class POModel:
    def __init__(self, db_manager, staff_id=1):
        self.db = db_manager
        self.staff_id = staff_id

    def get_all_po(self):
        query = """
            SELECT po.PurchaseOrderID, po.OrderDate, po.TotalCost, po.Status,
                   s.SupplierName
            FROM PurchaseOrder po
            JOIN Supplier s ON s.SupplierID = po.SupplierID
            ORDER BY po.PurchaseOrderID DESC
        """
        with self.db.get_connection() as conn:
            rows = conn.execute(query).fetchall()
        return [
            {
                "po_number": po_number(r["PurchaseOrderID"]),
                "supplier": r["SupplierName"],
                "date_ordered": nice_date(r["OrderDate"]),
                "total_cost": r["TotalCost"],
                "status": r["Status"],
            }
            for r in rows
        ]

    def _get_or_create_supplier(self, conn, supplier_name):
        row = conn.execute(
            "SELECT SupplierID FROM Supplier WHERE SupplierName = ?", (supplier_name,)
        ).fetchone()
        if row:
            return row["SupplierID"]
        cur = conn.execute(
            "INSERT INTO Supplier (SupplierName) VALUES (?)", (supplier_name,)
        )
        return cur.lastrowid

    def _get_or_create_product(self, conn, product_name, unit_cost):
        row = conn.execute(
            "SELECT ProductID FROM Product WHERE ProductName = ?", (product_name,)
        ).fetchone()
        if row:
            return row["ProductID"]
        supplier_id = self._get_or_create_supplier(conn, "General Supplier")
        cur = conn.execute(
            """INSERT INTO Product (SupplierID, StaffID, ProductName, Price, StockQuantity)
               VALUES (?, ?, ?, ?, 0)""",
            (supplier_id, self.staff_id, product_name, unit_cost),
        )
        return cur.lastrowid

    def create_po(self, supplier, date_expected, total_cost,
                  item_name=None, item_qty=0, item_cost=0.0):
        with self.db.get_connection() as conn:
            supplier_id = self._get_or_create_supplier(conn, supplier)
            cur = conn.execute(
                """INSERT INTO PurchaseOrder (StaffID, SupplierID, ExpectedDeliveryDate,
                                              Status, TotalCost)
                   VALUES (?, ?, ?, 'Pending', ?)""",
                (self.staff_id, supplier_id, date_expected, total_cost),
            )
            po_id = cur.lastrowid

            if item_name and item_qty > 0:
                product_id = self._get_or_create_product(conn, item_name, item_cost)
                conn.execute(
                    """INSERT INTO PurchaseOrderDetails (PurchaseOrderID, ProductID,
                                                          Quantity, UnitCost)
                       VALUES (?, ?, ?, ?)""",
                    (po_id, product_id, item_qty, item_cost),
                )
            conn.commit()
            return po_number(po_id)
