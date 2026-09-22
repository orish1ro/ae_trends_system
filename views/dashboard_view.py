from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt

# Every label placed inside a white card MUST get both "background: transparent"
# and "border: none" explicitly, or it can pick up the card's own border/background
# instead of blending into it. That was the cause of the boxed-up look.
LABEL_RESET = "background: transparent; border: none;"

CARD_ICONS = {
    "Today's Sales": "\U0001F6D2",       # shopping cart
    "Low Stock Items": "\U0001F4E6",     # package
    "Pending Orders": "\u23F3",          # hourglass
    "Expiring Products": "\u23F0",       # alarm clock
}


class DashboardView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #F7F3EB;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Title
        title = QLabel("Dashboard")
        title.setStyleSheet(f"font-size: 26px; font-weight: bold; color: #2A2421; {LABEL_RESET}")
        sub = QLabel("Welcome back, Admin. Here's a snapshot of today's retail operations.")
        sub.setStyleSheet(f"font-size: 13px; color: #777777; {LABEL_RESET}")
        layout.addWidget(title)
        layout.addWidget(sub)

        # 4 Stat Cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        self.card_sales = self.create_card("Today's Sales", "₱0.00", "+14% from yesterday")
        self.card_low = self.create_card("Low Stock Items", "0 items", "Requires immediate PO")
        self.card_pending = self.create_card("Pending Orders", "0 orders", "In queue for fulfillment")
        self.card_expiring = self.create_card("Expiring Products", "0 products", "Skincare batch near date")

        cards_layout.addWidget(self.card_sales)
        cards_layout.addWidget(self.card_low)
        cards_layout.addWidget(self.card_pending)
        cards_layout.addWidget(self.card_expiring)
        layout.addLayout(cards_layout)

        # Recent Transactions
        sec_title = QLabel("Recent Transactions")
        sec_title.setStyleSheet(f"font-size: 16px; font-weight: bold; margin-top: 15px; color: #2A2421; {LABEL_RESET}")
        layout.addWidget(sec_title)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["TRANSACTION ID", "DATE", "CUSTOMER", "TOTAL", "STATUS"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                background: white;
                border-radius: 8px;
                border: 1px solid #E5E0D5;
                gridline-color: #F0EAE1;
            }
        """)
        layout.addWidget(self.table)

    def create_card(self, title_text, val, sub_text):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 10px;
                border: 1px solid #E9E2D3;
            }
        """)
        outer = QVBoxLayout(frame)
        outer.setContentsMargins(18, 16, 18, 16)
        outer.setSpacing(6)

        # Top row: small title on the left, icon badge on the right
        top_row = QHBoxLayout()
        lbl_t = QLabel(title_text)
        lbl_t.setStyleSheet(f"font-size: 12px; color: #888888; {LABEL_RESET}")

        icon_badge = QLabel(CARD_ICONS.get(title_text, ""))
        icon_badge.setFixedSize(30, 30)
        icon_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_badge.setStyleSheet("""
            background-color: #F6EAC9;
            border: none;
            border-radius: 8px;
            font-size: 14px;
        """)

        top_row.addWidget(lbl_t)
        top_row.addStretch()
        top_row.addWidget(icon_badge)
        outer.addLayout(top_row)

        lbl_v = QLabel(val)
        lbl_v.setStyleSheet(f"font-size: 22px; font-weight: bold; color: #2A2421; {LABEL_RESET}")
        outer.addWidget(lbl_v)

        lbl_s = QLabel(sub_text)
        lbl_s.setStyleSheet(f"font-size: 11px; color: #A39B90; {LABEL_RESET}")
        outer.addWidget(lbl_s)

        frame.val_label = lbl_v
        return frame

    def update_metrics(self, sales, low_stock, pending, expiring):
        self.card_sales.val_label.setText(f"₱{sales:,.2f}")
        self.card_low.val_label.setText(f"{low_stock} items")
        self.card_pending.val_label.setText(f"{pending} orders")
        self.card_expiring.val_label.setText(f"{expiring} products")

    def display_recent_transactions(self, transactions):
        self.table.setRowCount(len(transactions))
        for row, txn in enumerate(transactions):
            self.table.setItem(row, 0, QTableWidgetItem(txn['order_code']))
            self.table.setItem(row, 1, QTableWidgetItem(txn['order_date']))
            self.table.setItem(row, 2, QTableWidgetItem(txn['customer_name']))
            self.table.setItem(row, 3, QTableWidgetItem(f"₱{txn['total_amount']:,.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(txn['status']))