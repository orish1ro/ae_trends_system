from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QStackedWidget, QFrame
from PyQt6.QtCore import pyqtSignal, Qt
from views.dashboard_view import DashboardView
from views.transaction_view import TransactionView
from views.inventory_view import InventoryView
from views.purchase_orders_view import PurchaseOrdersView
from views.order_status_view import OrderStatusView
from views.reports_view import ReportsView

class MainWindow(QMainWindow):
    logout_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AE Trends - Retail POS & Inventory")
        self.resize(1300, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.setup_sidebar()
        self.setup_modules()

    def setup_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(230)
        sidebar.setStyleSheet("background-color: #241E1C; color: #FFFFFF;")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setSpacing(8)

        # Brand Logo Header
        logo = QLabel("AE Trends")
        logo.setStyleSheet("font-size: 20px; font-weight: bold; color: #FFFFFF;")
        tagline = QLabel("Point of Sale")
        tagline.setStyleSheet("font-size: 11px; color: #8F8782; margin-bottom: 20px;")
        layout.addWidget(logo)
        layout.addWidget(tagline)

        # Navigation Items
        self.nav_btns = []
        modules = [
            ("Dashboard", 0),
            ("Record Transaction", 1),
            ("Inventory", 2),
            ("Purchase Orders", 3),
            ("Order Status", 4),
            ("Reports", 5),
        ]

        for text, index in modules:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 12px 16px;
                    border: none;
                    border-radius: 8px;
                    font-size: 13px;
                    color: #A39B95;
                    background: transparent;
                }
                QPushButton:hover {
                    background-color: #312A27;
                    color: #FFFFFF;
                }
                QPushButton:checked {
                    background-color: #C09E3B;
                    color: #FFFFFF;
                    font-weight: bold;
                }
            """)
            btn.clicked.connect(lambda checked, idx=index: self.switch_view(idx))
            layout.addWidget(btn)
            self.nav_btns.append(btn)

        self.nav_btns[0].setChecked(True)
        layout.addStretch()

        # User profile badge & logout
        self.user_lbl = QLabel("Mia Santos\nOwner")
        self.user_lbl.setStyleSheet("color: #A39B95; font-size: 12px; margin-bottom: 5px;")
        layout.addWidget(self.user_lbl)

        logout_btn = QPushButton("Logout")
        logout_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #C09E3B;
                border: 1px solid #C09E3B;
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #C09E3B;
                color: white;
            }
        """)
        logout_btn.clicked.connect(self.logout_requested.emit)
        layout.addWidget(logout_btn)

        self.main_layout.addWidget(sidebar)

    def setup_modules(self):
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        self.dashboard_view = DashboardView()
        self.record_tx_view = TransactionView()
        self.inventory_view = InventoryView()
        self.purchase_orders_view = PurchaseOrdersView()
        self.order_status_view = OrderStatusView()
        self.reports_view = ReportsView()

        self.stacked_widget.addWidget(self.dashboard_view)
        self.stacked_widget.addWidget(self.record_tx_view)
        self.stacked_widget.addWidget(self.inventory_view)
        self.stacked_widget.addWidget(self.purchase_orders_view)
        self.stacked_widget.addWidget(self.order_status_view)
        self.stacked_widget.addWidget(self.reports_view)

    def switch_view(self, index):
        for i, btn in enumerate(self.nav_btns):
            btn.setChecked(i == index)
        self.stacked_widget.setCurrentIndex(index)

    def set_user(self, name, role):
        self.user_lbl.setText(f"{name}\n{role}")
