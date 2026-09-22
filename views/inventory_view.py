from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox)

class InventoryView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #F7F3EB;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        # Header Title and Action
        top_bar = QHBoxLayout()
        header_layout = QVBoxLayout()
        title = QLabel("Inventory")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #2A2421;")
        sub = QLabel("Manage store stocks, skincare shelf-life, and apparel sizing.")
        sub.setStyleSheet("font-size: 13px; color: #777777;")
        header_layout.addWidget(title)
        header_layout.addWidget(sub)
        top_bar.addLayout(header_layout)

        top_bar.addStretch()
        self.add_product_btn = QPushButton("+ Add New Product")
        self.add_product_btn.setStyleSheet("""
            QPushButton {
                background: #C09E3B;
                color: white;
                font-weight: bold;
                padding: 10px 18px;
                border-radius: 6px;
            }
            QPushButton:hover { background: #A9872E; }
        """)
        top_bar.addWidget(self.add_product_btn)
        layout.addLayout(top_bar)

        # Filter Bar
        filter_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search product inventory...")
        self.search_input.setStyleSheet("padding: 8px 12px; border: 1px solid #CCC; border-radius: 6px; background: white;")
        
        self.category_filter = QComboBox()
        self.category_filter.addItems(["Category: All", "Clothing", "Skincare"])
        self.category_filter.setStyleSheet("padding: 8px; border: 1px solid #CCC; border-radius: 6px; background: white;")

        self.status_filter = QComboBox()
        self.status_filter.addItems(["Status: All Stock", "In Stock", "Low Stock", "Expiring Soon"])
        self.status_filter.setStyleSheet("padding: 8px; border: 1px solid #CCC; border-radius: 6px; background: white;")

        filter_bar.addWidget(self.search_input, 60)
        filter_bar.addWidget(self.category_filter, 20)
        filter_bar.addWidget(self.status_filter, 20)
        layout.addLayout(filter_bar)

        # Inventory Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["PRODUCT NAME", "CATEGORY", "PRICE", "STOCK QTY", "EXPIRATION DATE", "STATUS"])
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

    def display_products(self, products):
        self.table.setRowCount(len(products))
        for row, prod in enumerate(products):
            self.table.setItem(row, 0, QTableWidgetItem(prod['name']))
            self.table.setItem(row, 1, QTableWidgetItem(prod['category']))
            self.table.setItem(row, 2, QTableWidgetItem(f"₱{prod['price']:,.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(str(prod['stock_qty'])))
            self.table.setItem(row, 4, QTableWidgetItem(prod['expiration_date']))
            self.table.setItem(row, 5, QTableWidgetItem(prod['status']))
