from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QDateEdit, QFileDialog,
    QMessageBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal

RESET = "background: transparent; border: none;"


class ReportsView(QWidget):
    filters_changed = pyqtSignal(str, str)
    export_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #F7F3EB;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Reports")
        title.setStyleSheet(f"font-size: 22px; font-weight: bold; color: #20283A; {RESET}")
        subtitle = QLabel("Sales performance, order activity, and inventory health.")
        subtitle.setStyleSheet(f"font-size: 11px; color: #667085; {RESET}")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()
        self.export_btn = QPushButton("Export CSV")
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.setStyleSheet(self._gold_button())
        self.export_btn.clicked.connect(self._choose_export_path)
        header.addWidget(self.export_btn)
        layout.addLayout(header)

        filters = QHBoxLayout()
        filters.setSpacing(8)
        from_label = QLabel("From")
        to_label = QLabel("To")
        for label in (from_label, to_label):
            label.setStyleSheet(f"font-size: 11px; color: #667085; {RESET}")
        self.from_date = QDateEdit(QDate.currentDate().addMonths(-1))
        self.to_date = QDateEdit(QDate.currentDate())
        for date_edit in (self.from_date, self.to_date):
            date_edit.setCalendarPopup(True)
            date_edit.setDisplayFormat("MMM d, yyyy")
            date_edit.setFixedHeight(30)
            date_edit.setStyleSheet(self._date_style())
        apply_btn = QPushButton("Apply Filter")
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.setStyleSheet(self._gold_button())
        apply_btn.clicked.connect(self._emit_filters)
        filters.addWidget(from_label)
        filters.addWidget(self.from_date)
        filters.addWidget(to_label)
        filters.addWidget(self.to_date)
        filters.addWidget(apply_btn)
        filters.addStretch()
        layout.addLayout(filters)

        metrics = QHBoxLayout()
        self.metric_sales = self._metric_card(metrics, "TOTAL SALES", "₱0.00")
        self.metric_orders = self._metric_card(metrics, "ORDERS", "0")
        self.metric_units = self._metric_card(metrics, "UNITS SOLD", "0")
        self.metric_low_stock = self._metric_card(metrics, "LOW STOCK", "0")
        layout.addLayout(metrics)

        sales_card = QFrame()
        sales_card.setStyleSheet(self._card_style())
        sales_layout = QVBoxLayout(sales_card)
        sales_layout.setContentsMargins(0, 0, 0, 0)
        sales_title = QLabel("Sales and Order Activity")
        sales_title.setStyleSheet(f"font-size: 13px; font-weight: bold; padding: 11px 14px; color: #20283A; {RESET}")
        sales_layout.addWidget(sales_title)
        self.sales_table = self._table(["ORDER", "DATE", "CUSTOMER", "TYPE", "ITEMS", "TOTAL", "STATUS"])
        sales_layout.addWidget(self.sales_table)
        layout.addWidget(sales_card, 1)

        low_title = QLabel("Inventory Health")
        low_title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: #20283A; {RESET}")
        layout.addWidget(low_title)
        self.table = self._table(["PRODUCT NAME", "CATEGORY", "CURRENT STOCK", "REORDER LEVEL", "ALERT STATUS"])
        self.table.setMinimumHeight(100)
        layout.addWidget(self.table)

    @staticmethod
    def _gold_button():
        return """
            QPushButton { background: #C09E3B; color: white; font-weight: bold;
                padding: 7px 14px; border-radius: 5px; border: none; }
            QPushButton:hover { background: #A9872E; }
        """

    @staticmethod
    def _date_style():
        return "QDateEdit { padding: 5px 8px; border: 1px solid #DCCFBC; border-radius: 5px; background: #FFFDFB; color: #344054; font-size: 11px; }"

    @staticmethod
    def _card_style():
        return "QFrame { background: #FFFDFB; border: 1px solid #E1D7C7; border-radius: 9px; }"

    @staticmethod
    def _table(headers):
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setFixedHeight(28)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(34)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setStyleSheet("""
            QTableWidget { background: #FFFDFB; border: 1px solid #E1D7C7;
                border-radius: 8px; gridline-color: #E8DFD0; color: #20283A; }
            QTableWidget::item { padding: 6px 8px; border: none; }
            QHeaderView::section { background: #F8F2E8; color: #7C8798;
                border: none; border-bottom: 1px solid #E1D7C7;
                padding: 6px 8px; font-size: 9px; font-weight: bold; }
        """)
        return table

    def _metric_card(self, parent_layout, label, value):
        card = QFrame()
        card.setStyleSheet(self._card_style())
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 8, 12, 8)
        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"font-size: 9px; color: #7C8798; {RESET}")
        value_widget = QLabel(value)
        value_widget.setStyleSheet(f"font-size: 17px; font-weight: bold; color: #20283A; {RESET}")
        card_layout.addWidget(label_widget)
        card_layout.addWidget(value_widget)
        parent_layout.addWidget(card)
        return value_widget

    def _emit_filters(self):
        if self.from_date.date() > self.to_date.date():
            QMessageBox.warning(self, "Invalid Date Range", "The From date cannot be after the To date.")
            return
        self.filters_changed.emit(
            self.from_date.date().toString("yyyy-MM-dd"),
            self.to_date.date().toString("yyyy-MM-dd"),
        )

    def _choose_export_path(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Report", "sales_report.csv", "CSV Files (*.csv)")
        if path:
            self.export_requested.emit(path)

    def display_report(self, rows, total_sales, order_count, units_sold, low_stock_count):
        self.metric_sales.setText(f"₱{total_sales:,.2f}")
        self.metric_orders.setText(str(order_count))
        self.metric_units.setText(str(units_sold))
        self.metric_low_stock.setText(str(low_stock_count))
        self.sales_table.setRowCount(len(rows))
        for row, data in enumerate(rows):
            values = [data["order"], data["date"], data["customer"], data["type"], str(data["items"]), f"₱{data['total']:,.2f}", data["status"]]
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                cell.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | (Qt.AlignmentFlag.AlignRight if column == 5 else Qt.AlignmentFlag.AlignLeft))
                self.sales_table.setItem(row, column, cell)

    def display_low_stock(self, items):
        self.table.setRowCount(len(items))
        for row, prod in enumerate(items):
            values = [prod['name'], prod['category'], f"{prod['stock_qty']} pcs", f"{prod['reorder_level']} pcs", "Critical" if prod['stock_qty'] <= 3 else "Low"]
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))
