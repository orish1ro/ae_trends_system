from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QButtonGroup)
from PyQt6.QtCore import pyqtSignal

class OrderStatusView(QWidget):
    filter_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #F7F3EB;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        title = QLabel("Order Status")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #2A2421;")
        sub = QLabel("Manage active fulfillments, delivery tracking, and checkout registers.")
        sub.setStyleSheet("font-size: 13px; color: #777777;")
        layout.addWidget(title)
        layout.addWidget(sub)

        # Filter Tabs
        tab_layout = QHBoxLayout()
        self.btn_all = QPushButton("All Orders")
        self.btn_online = QPushButton("Online Shipments")
        self.btn_walkin = QPushButton("Walk-in Registers")
        
        self.tab_group = QButtonGroup(self)
        for btn in [self.btn_all, self.btn_online, self.btn_walkin]:
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton { padding: 8px 16px; border-radius: 6px; font-weight: bold; background: #E8E2D5; color: #444; }
                QPushButton:checked { background: #C09E3B; color: white; }
            """)
            btn.clicked.connect(self.filter_changed.emit)
            self.tab_group.addButton(btn)
            tab_layout.addWidget(btn)
        self.btn_all.setChecked(True)
        tab_layout.addStretch()
        layout.addLayout(tab_layout)

        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Customer Name...")
        self.search_input.setStyleSheet("padding: 8px 12px; border: 1px solid #CCC; border-radius: 6px; background: white;")
        layout.addWidget(self.search_input)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ORDER ID", "CUSTOMER NAME", "ORDER TYPE", "DATE", "TOTAL AMOUNT", "CURRENT STATUS"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("background: white; border-radius: 8px; border: 1px solid #E5E0D5;")
        layout.addWidget(self.table)

    def get_active_tab(self):
        if self.btn_online.isChecked():
            return "Online Shipments"
        elif self.btn_walkin.isChecked():
            return "Walk-in Registers"
        return "All Orders"

    def display_orders(self, orders):
        self.table.setRowCount(len(orders))
        for row, ord_item in enumerate(orders):
            self.table.setItem(row, 0, QTableWidgetItem(ord_item['order_code']))
            self.table.setItem(row, 1, QTableWidgetItem(ord_item['customer_name']))
            self.table.setItem(row, 2, QTableWidgetItem(ord_item['order_type']))
            self.table.setItem(row, 3, QTableWidgetItem(ord_item['order_date']))
            self.table.setItem(row, 4, QTableWidgetItem(f"₱{ord_item['total_amount']:,.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(ord_item['status']))
