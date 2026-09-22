from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QColor, QBrush


class FilterComboBox(QComboBox):
    def showPopup(self):
        popup_view = self.view()
        popup_view.setMinimumWidth(self.width())
        popup_view.setMaximumHeight(140)
        super().showPopup()
        QTimer.singleShot(0, self._move_popup_below)

    def _move_popup_below(self):
        popup = self.view().window()
        popup.move(self.mapToGlobal(QPoint(0, self.height())))


class InventoryView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #F7F3EB;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 16)
        layout.setSpacing(14)

        # Header Title and Action
        top_bar = QHBoxLayout()
        header_layout = QVBoxLayout()
        title = QLabel("Inventory")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #20283A; margin: 0;")
        sub = QLabel("Manage store stocks, skincare shelf-life, and apparel sizing.")
        sub.setStyleSheet("font-size: 11px; color: #667085; margin: 0;")
        header_layout.addWidget(title)
        header_layout.addWidget(sub)
        top_bar.addLayout(header_layout)

        top_bar.addStretch()
        self.add_product_btn = QPushButton("+ Add New Product")
        self.add_product_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_product_btn.setStyleSheet("""
            QPushButton {
                background: #C09E3B;
                color: white;
                font-weight: bold;
                padding: 8px 14px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover { background: #A9872E; }
        """)
        top_bar.addWidget(self.add_product_btn)
        layout.addLayout(top_bar)

        # Filter Bar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(12)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search product inventory...")
        self.search_input.setFixedHeight(30)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 5px 10px;
                border: 1px solid #DCCFBC;
                border-radius: 5px;
                background: #FFFDFB;
                color: #344054;
                font-size: 11px;
            }
            QLineEdit:focus { border: 1px solid #C09E3B; }
        """)
        
        self.category_filter = FilterComboBox()
        self.category_filter.addItems(["Category: All", "Clothing", "Skincare"])
        self.category_filter.setFixedHeight(30)
        self.category_filter.setStyleSheet("""
            QComboBox {
                padding: 5px 4px;
                border: 1px solid #DCCFBC;
                border-radius: 5px;
                background: #FFFDFB;
                color: #344054;
                font-size: 11px;
            }
            QComboBox::drop-down { border: none; width: 18px; }
            QComboBox QAbstractItemView {
                background: #FFFDFB;
                color: #344054;
                border: none;
                selection-background-color: #FFF2C8;
                selection-color: #8B6820;
                outline: none;
                padding: 3px;
            }
            QComboBox QAbstractItemView::item {
                min-height: 27px;
                padding: 4px 8px;
                border-radius: 3px;
            }
            QComboBox QAbstractItemView::item:hover {
                background: #F5E8C4;
            }
        """)

        self.status_filter = FilterComboBox()
        self.status_filter.addItems(["Status: All Stock", "In Stock", "Low Stock", "Expiring Soon"])
        self.status_filter.setFixedHeight(30)
        self.status_filter.setStyleSheet("""
            QComboBox {
                padding: 5px 4px;
                border: 1px solid #DCCFBC;
                border-radius: 5px;
                background: #FFFDFB;
                color: #344054;
                font-size: 11px;
            }
            QComboBox::drop-down { border: none; width: 18px; }
            QComboBox QAbstractItemView {
                background: #FFFDFB;
                color: #344054;
                border: none;
                selection-background-color: #FFF2C8;
                selection-color: #8B6820;
                outline: none;
                padding: 3px;
            }
            QComboBox QAbstractItemView::item {
                min-height: 27px;
                padding: 4px 8px;
                border-radius: 3px;
            }
            QComboBox QAbstractItemView::item:hover {
                background: #F5E8C4;
            }
        """)

        filter_bar.addWidget(self.search_input, 0)
        filter_bar.addWidget(self.category_filter, 0)
        filter_bar.addWidget(self.status_filter, 0)
        self.search_input.setFixedWidth(230)
        self.category_filter.setFixedWidth(108)
        self.status_filter.setFixedWidth(124)
        filter_bar.addStretch()
        layout.addLayout(filter_bar)

        # Inventory Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["PRODUCT NAME", "CATEGORY", "PRICE", "STOCK QTY", "EXPIRATION DATE", "STATUS"])
        self.table.setShowGrid(True)
        self.table.setAlternatingRowColors(False)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(42)
        self.table.horizontalHeader().setFixedHeight(30)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setStyleSheet("""
            QTableWidget {
                background: #FFFDFB;
                border: 1px solid #E1D7C7;
                border-radius: 9px;
                gridline-color: #E8DFD0;
                color: #20283A;
                outline: none;
            }
            QTableWidget::item {
                padding: 8px 10px;
                border: none;
            }
            QHeaderView::section {
                background: #FFF9EE;
                color: #7C8798;
                border: none;
                border-bottom: 1px solid #E1D7C7;
                padding: 7px 10px;
                font-size: 10px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.table)

    def display_products(self, products):
        self.table.setRowCount(len(products))
        for row, prod in enumerate(products):
            values = [
                prod['name'],
                prod['category'],
                f"₱{prod['price']:,.2f}",
                str(prod['stock_qty']),
                prod['expiration_date'],
                prod['status'],
            ]
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                cell.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | (
                    Qt.AlignmentFlag.AlignRight if column in (2, 3) else Qt.AlignmentFlag.AlignLeft
                ))
                self.table.setItem(row, column, cell)

            row_color = QColor("#FBE8E2") if prod['status'] == "Low Stock" else (
                QColor("#F8EDCC") if prod['status'] == "Expiring Soon" else QColor("#FFFDFB")
            )
            for column in range(6):
                self.table.item(row, column).setBackground(QBrush(row_color))

            status_cell = self.table.item(row, 5)
            status_cell.setText("")
            badge = QLabel(prod['status'])
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setFixedHeight(22)
            if prod['status'] == "In Stock":
                badge.setStyleSheet(
                    "color: #118443; background: #F2FFF6; border: 1px solid #22A05A; "
                    "border-radius: 5px; padding: 0 7px; font-size: 10px;"
                )
            elif prod['status'] == "Low Stock":
                badge.setStyleSheet(
                    "color: #C2410C; background: #FFF5F0; border: 1px solid #EA6A36; "
                    "border-radius: 5px; padding: 0 7px; font-size: 10px;"
                )
            else:
                badge.setStyleSheet(
                    "color: #B45309; background: #FFF9E8; border: 1px solid #C97816; "
                    "border-radius: 5px; padding: 0 7px; font-size: 10px;"
                )
            self.table.setCellWidget(row, 5, badge)
