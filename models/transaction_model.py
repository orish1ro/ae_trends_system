"""MODEL: reads/writes Orders, OrderDetails, Payment (and finds/creates Customer).

Your ERD's Orders table stores CustomerID and PlatformID, not a customer name
or an order_type column directly, so this file joins Customer/Platform and
works out "Online" vs "Walk-in" from the platform used."""
from datetime import datetime


def order_code(order_id):
    return f"ORD-{order_id:04d}"


def nice_date(iso_text):
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(iso_text[:19], fmt).strftime("%b %d, %Y")
        except (ValueError, TypeError):
            continue
    return iso_text or ""


class TransactionModel:
    def __init__(self, db_manager, staff_id=1):
        self.db = db_manager
        self.staff_id = staff_id

    # ---------- reading orders for the Order Status / Dashboard screens ----------
    def get_all_orders(self, filter_type="All Orders", search_name=""):
        query = """
            SELECT o.OrderID, o.OrderDate, o.TotalAmount, o.OrderStatus,
                   c.FullName AS CustomerName, pl.PlatformName
            FROM Orders o
            JOIN Customer c ON c.CustomerID = o.CustomerID
            JOIN Platform pl ON pl.PlatformID = o.PlatformID
            WHERE 1=1
        """
        params = []
        if filter_type == "Online Shipments":
            query += " AND pl.PlatformName != 'Walk-in'"
        elif filter_type == "Walk-in Registers":
            query += " AND pl.PlatformName = 'Walk-in'"
        if search_name:
            query += " AND c.FullName LIKE ?"
            params.append(f"%{search_name}%")
        query += " ORDER BY o.OrderID DESC"

        with self.db.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            {
                "order_code": order_code(r["OrderID"]),
                "customer_name": r["CustomerName"],
                "order_type": "Walk-in" if r["PlatformName"] == "Walk-in" else "Online",
                "order_date": nice_date(r["OrderDate"]),
                "total_amount": r["TotalAmount"],
                "status": r["OrderStatus"],
            }
            for r in rows
        ]

    def get_recent_orders(self, limit=6):
        return self.get_all_orders("All Orders")[:limit]

    # ---------- writing a new order ----------
    def _find_or_create_customer(self, conn, name, phone, address):
        if phone:
            row = conn.execute(
                "SELECT CustomerID FROM Customer WHERE ContactNumber = ?", (phone,)
            ).fetchone()
            if row:
                return row["CustomerID"]
        cur = conn.execute(
            "INSERT INTO Customer (FullName, ContactNumber, Address) VALUES (?, ?, ?)",
            (name, phone or None, address or None),
        )
        return cur.lastrowid

    def _platform_id_for(self, conn, order_type):
        platform_name = {
            "Facebook": "Facebook Live",
            "TikTok": "TikTok Live",
        }.get(order_type, order_type)
        row = conn.execute(
            "SELECT PlatformID FROM Platform WHERE PlatformName = ?",
            (platform_name,),
        ).fetchone()
        if row:
            return row["PlatformID"]
        cur = conn.execute(
            "INSERT INTO Platform (PlatformName) VALUES (?)", (platform_name,)
        )
        return cur.lastrowid

    def create_order(self, customer_name, customer_phone, address, order_type,
                      total, payment_method, cart_items, amount_paid=None,
                      reference_number="", receipt_image=""):
        with self.db.get_connection() as conn:
            customer_id = self._find_or_create_customer(conn, customer_name,
                                                          customer_phone, address)
            platform_id = self._platform_id_for(conn, order_type)
            # Walk-in customers pay and collect on the spot; online orders start
            # as Pending until the staff prepares and ships them.
            initial_status = "Completed" if order_type == "Walk-in" else "Pending"

            cur = conn.execute(
                """INSERT INTO Orders (CustomerID, StaffID, PlatformID, TotalAmount,
                                       OrderStatus, DeliveryAddress)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (customer_id, self.staff_id, platform_id, total, initial_status,
                 address or None),
            )
            order_id = cur.lastrowid

            for item in cart_items:
                subtotal = item["price"] * item["qty"]
                conn.execute(
                    """INSERT INTO OrderDetails (OrderID, ProductID, Quantity,
                                                 UnitPriceAtOrder, Subtotal)
                       VALUES (?, ?, ?, ?, ?)""",
                    (order_id, item["id"], item["qty"], item["price"], subtotal),
                )
                conn.execute(
                    "UPDATE Product SET StockQuantity = StockQuantity - ? WHERE ProductID = ?",
                    (item["qty"], item["id"]),
                )

            conn.execute(
                """INSERT INTO Payment (OrderID, PaymentMethod, AmountPaid,
                                        PaymentStatus, ReferenceNumber,
                                        ReceiptImageURL)
                   VALUES (?, ?, ?, 'Paid', ?, ?)""",
                (order_id, payment_method,
                 total if amount_paid is None else amount_paid,
                 reference_number or None, receipt_image or None),
            )
            conn.commit()
            return order_code(order_id)
