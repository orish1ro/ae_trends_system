from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtCore import QByteArray
from views.styled_dropdown import StyledComboBox

# Every label placed inside a white card MUST get both "background: transparent"
# and "border: none" explicitly, or it can pick up the card's own border/background
# instead of blending into it. That was the cause of the boxed-up look.
LABEL_RESET = "background: transparent; border: none;"

class ClickableCard(QFrame):
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class DashboardChart(QFrame):
    filter_changed = pyqtSignal(str)
    empty_action_requested = pyqtSignal()

    def __init__(self, title, chart_type):
        super().__init__()
        self.title = title
        self.chart_type = chart_type
        self.values = []
        self.setMinimumHeight(220)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName("dashboardChart")
        self.setStyleSheet("""
            QFrame#dashboardChart {
                background-color: #FFFFFF;
                border: 1px solid #E5E0D5;
                border-radius: 8px;
            }
        """)
        self.empty_state = QSvgWidget(self)
        self.empty_state.setStyleSheet("background: transparent; border: none;")
        self.empty_state.load(QByteArray(self._empty_svg(chart_type)))
        self.empty_action = QPushButton("+ Record Sale" if chart_type == "bars" else "Change Filter", self)
        self.empty_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.empty_action.setStyleSheet("QPushButton { color: #A9872E; background: transparent; border: none; font-size: 10px; font-weight: bold; } QPushButton:hover { color: #7F641E; }")
        self.empty_action.clicked.connect(self.empty_action_requested)
        self.filter_combo = StyledComboBox(self)
        self.filter_combo.addItems(["Today", "This Week", "This Month"])
        self.filter_combo.setFixedWidth(112)
        self.filter_combo.currentTextChanged.connect(self.filter_changed.emit)

    @staticmethod
    def _empty_svg(chart_type):
        if chart_type == "bars":
            message = "No sales recorded"
            axis_label = "Sales amount"
        else:
            message = "No orders recorded"
            axis_label = "Order count"
        return f'''<svg width="250" height="180" viewBox="0 0 250 180" xmlns="http://www.w3.org/2000/svg">
            <g fill="none" stroke="#CFC4B2" stroke-width="2">
                <path d="M42 126V42M42 126H224"/>
                <rect x="88" y="70" width="92" height="38" rx="5" stroke="#E2D9CB" stroke-dasharray="5 5"/>
            </g>
            <text x="133" y="94" text-anchor="middle" fill="#A39B90" font-family="Arial" font-size="10">{message}</text>
            <text x="133" y="151" text-anchor="middle" fill="#A39B90" font-family="Arial" font-size="10">{axis_label}</text>
            <text x="133" y="171" text-anchor="middle" fill="#B0A79C" font-family="Arial" font-size="10">Select another date range</text>
        </svg>'''.encode("utf-8")

    def resizeEvent(self, event):
        self.filter_combo.move(self.width() - self.filter_combo.width() - 14, 10)
        self.empty_state.setGeometry(max(0, (self.width() - 250) // 2), 42, 250, 180)
        self.empty_action.setGeometry((self.width() - 130) // 2, self.height() - 31, 130, 22)
        super().resizeEvent(event)

    def set_values(self, values):
        self.values = values
        self.empty_state.setVisible(not values)
        self.empty_action.setVisible(not values)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor("#2A2421"))
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.drawText(18, 28, self.title)

        if not self.values:
            painter.end()
            return

        if self.chart_type == "bars":
            self._draw_sales_bars(painter)
        else:
            self._draw_status_donut(painter)
        painter.end()

    def _draw_sales_bars(self, painter):
        left, top, width, height = 42, 62, self.width() - 64, 120
        maximum = max(value for _, value in self.values) or 1
        bar_width = max(14, min(48, (width - 12 * (len(self.values) - 1)) // len(self.values)))
        painter.setPen(QPen(QColor("#B8AA92"), 1))
        painter.drawLine(left, top, left, top + height)
        painter.drawLine(left, top + height, left + width, top + height)
        painter.setFont(QFont("Arial", 8))
        painter.setPen(QColor("#8B8176"))
        painter.drawText(8, top + 6, "PHP")
        for index, (label, value) in enumerate(self.values):
            x = left + index * ((width - bar_width) // max(1, len(self.values) - 1)) if len(self.values) > 1 else left + (width - bar_width) // 2
            bar_height = int((value / maximum) * (height - 20))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#C09E3B"))
            painter.drawRoundedRect(x, top + height - bar_height, bar_width, bar_height, 4, 4)
            painter.setPen(QColor("#777777"))
            painter.drawText(x - 10, top + height + 17, bar_width + 20, 16, Qt.AlignmentFlag.AlignCenter, label)
            painter.setPen(QColor("#2A2421"))
            painter.drawText(x - 10, top + height - bar_height - 6, bar_width + 20, 16, Qt.AlignmentFlag.AlignCenter, f"₱{value:,.0f}")

    def _draw_status_donut(self, painter):
        total = sum(value for _, value in self.values) or 1
        colors = ["#6D9F71", "#C09E3B", "#C9795D", "#8C7AAE"]
        center_x, center_y = 110, 130
        outer = 54
        start_angle = 90 * 16
        painter.setPen(Qt.PenStyle.NoPen)
        for index, (label, value) in enumerate(self.values):
            span_angle = int(value / total * 360 * 16)
            painter.setBrush(QColor(colors[index % len(colors)]))
            painter.drawPie(center_x - outer, center_y - outer, outer * 2, outer * 2, start_angle, span_angle)
            start_angle += span_angle
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(center_x - 30, center_y - 30, 60, 60)
        painter.setPen(QColor("#2A2421"))
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.drawText(center_x - 28, center_y - 4, 56, 18, Qt.AlignmentFlag.AlignCenter, str(int(total)))
        painter.setFont(QFont("Arial", 8))
        painter.setPen(QColor("#8B8176"))
        painter.drawText(center_x - 35, center_y + 10, 70, 14, Qt.AlignmentFlag.AlignCenter, "orders")
        for index, (label, value) in enumerate(self.values):
            y = 78 + index * 25
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(colors[index % len(colors)]))
            painter.drawRoundedRect(190, y, 9, 9, 2, 2)
            painter.setPen(QColor("#5E554C"))
            painter.drawText(205, y + 9, 100, 14, Qt.AlignmentFlag.AlignLeft, f"{label}: {value} ({value / total * 100:.0f}%)")


class DashboardView(QWidget):
    new_transaction_requested = pyqtSignal()
    inventory_requested = pyqtSignal()
    order_status_requested = pyqtSignal()
    expiring_requested = pyqtSignal()
    reports_requested = pyqtSignal()
    view_all_requested = pyqtSignal()
    date_range_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #F7F3EB;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setContentsMargins(0, 0, 12, 0)
        title_box.setSpacing(5)
        title = QLabel("Dashboard")
        title.setStyleSheet(f"font-size: 26px; font-weight: bold; color: #2A2421; {LABEL_RESET}")
        sub = QLabel("Welcome back, Admin. Here's a snapshot of today's retail operations.")
        sub.setStyleSheet(f"font-size: 13px; color: #777777; {LABEL_RESET}")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        self.date_range = StyledComboBox()
        self.date_range.addItems(["Today", "This Week", "This Month"])
        self.date_range.setToolTip("Choose the dashboard reporting period")
        self.date_range.setFixedWidth(122)
        self.date_range.currentTextChanged.connect(self._on_global_range_changed)

        self.notification_btn = QPushButton("Alerts: 0")
        self.notification_btn.setToolTip("Stock and expiry alerts")
        self.notification_btn.setStyleSheet("QPushButton { background: #FFFDFB; color: #6D5A27; border: 1px solid #D6CEBC; border-radius: 6px; padding: 8px 12px; font-weight: bold; }")

        self.new_transaction_btn = QPushButton("+ New Transaction")
        self.new_transaction_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_transaction_btn.setStyleSheet("QPushButton { background: #C09E3B; color: white; border: none; border-radius: 6px; padding: 9px 14px; font-weight: bold; } QPushButton:hover { background: #A9872E; }")
        self.new_transaction_btn.clicked.connect(self.new_transaction_requested)
        header.addWidget(self.date_range)
        header.addWidget(self.notification_btn)
        header.addWidget(self.new_transaction_btn)
        layout.addLayout(header)

        # 4 Stat Cards
        cards_layout = QHBoxLayout()
        cards_layout.setContentsMargins(0, 10, 0, 4)
        cards_layout.setSpacing(16)
        self.card_sales = self.create_card("Today's Sales", "₱0.00", "No sales today")
        self.card_low = self.create_card("Low Stock Items", "0 items", "Requires immediate PO")
        self.card_pending = self.create_card("Pending Orders", "0 orders", "In queue for fulfillment")
        self.card_expiring = self.create_card("Expiring Products", "0 products", "Skincare batch near date")

        cards_layout.addWidget(self.card_sales)
        cards_layout.addWidget(self.card_low)
        cards_layout.addWidget(self.card_pending)
        cards_layout.addWidget(self.card_expiring)
        self.card_sales.clicked.connect(self.reports_requested)
        self.card_low.clicked.connect(self.inventory_requested)
        self.card_pending.clicked.connect(self.order_status_requested)
        self.card_expiring.clicked.connect(self.expiring_requested)
        layout.addLayout(cards_layout)

        charts_layout = QHBoxLayout()
        charts_layout.setContentsMargins(0, 4, 0, 4)
        charts_layout.setSpacing(16)
        self.sales_chart = DashboardChart("Sales by Order (PHP)", "bars")
        self.status_chart = DashboardChart("Order Status (Orders)", "status")
        self.sales_chart.filter_changed.connect(self._on_chart_range_changed)
        self.status_chart.filter_changed.connect(self._on_chart_range_changed)
        self.sales_chart.empty_action_requested.connect(self.new_transaction_requested)
        self.status_chart.empty_action_requested.connect(self._open_global_filter)
        charts_layout.addWidget(self.sales_chart)
        charts_layout.addWidget(self.status_chart)
        charts_title = QLabel("Performance Overview")
        charts_title.setStyleSheet(f"font-size: 16px; font-weight: bold; margin-top: 15px; color: #2A2421; {LABEL_RESET}")
        layout.addWidget(charts_title)
        layout.addLayout(charts_layout)

        # Recent Transactions
        transactions_header = QHBoxLayout()
        transactions_header.setContentsMargins(0, 10, 0, 0)
        sec_title = QLabel("Recent Transactions")
        sec_title.setStyleSheet(f"font-size: 16px; font-weight: bold; margin-top: 15px; color: #2A2421; {LABEL_RESET}")
        view_all = QPushButton("View All")
        view_all.setCursor(Qt.CursorShape.PointingHandCursor)
        view_all.setStyleSheet(f"color: #A9872E; font-size: 12px; font-weight: bold; {LABEL_RESET}")
        view_all.clicked.connect(self.view_all_requested)
        transactions_header.addWidget(sec_title)
        transactions_header.addStretch()
        transactions_header.addWidget(view_all)
        layout.addLayout(transactions_header)

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

    def _on_global_range_changed(self, preset):
        for chart in (self.sales_chart, self.status_chart):
            if chart.filter_combo.currentText() != preset:
                chart.filter_combo.blockSignals(True)
                chart.filter_combo.setCurrentText(preset)
                chart.filter_combo.blockSignals(False)
        self.date_range_changed.emit(preset)

    def _on_chart_range_changed(self, preset):
        if self.date_range.currentText() != preset:
            self.date_range.blockSignals(True)
            self.date_range.setCurrentText(preset)
            self.date_range.blockSignals(False)
        self.date_range_changed.emit(preset)

    def _open_global_filter(self):
        self.date_range.setFocus()
        self.date_range.showPopup()

    def create_card(self, title_text, val, sub_text):
        frame = ClickableCard()
        frame.setCursor(Qt.CursorShape.PointingHandCursor)
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

        # Top row: small title
        top_row = QHBoxLayout()
        lbl_t = QLabel(title_text)
        lbl_t.setStyleSheet(f"font-size: 12px; color: #888888; {LABEL_RESET}")
        top_row.addWidget(lbl_t)
        top_row.addStretch()
        outer.addLayout(top_row)

        lbl_v = QLabel(val)
        lbl_v.setStyleSheet(f"font-size: 22px; font-weight: bold; color: #2A2421; {LABEL_RESET}")
        outer.addWidget(lbl_v)

        lbl_s = QLabel(sub_text)
        lbl_s.setStyleSheet(f"font-size: 11px; color: #A39B90; {LABEL_RESET}")
        outer.addWidget(lbl_s)

        frame.val_label = lbl_v
        frame.sub_label = lbl_s
        return frame

    def update_metrics(self, sales, low_stock, pending, expiring, sales_change=None):
        self.card_sales.val_label.setText(f"₱{sales:,.2f}")
        self.card_low.val_label.setText(f"{low_stock} items")
        self.card_pending.val_label.setText(f"{pending} orders")
        self.card_expiring.val_label.setText(f"{expiring} products")
        if sales <= 0:
            self.card_sales.sub_label.setText("No sales today")
        elif sales_change is None:
            self.card_sales.sub_label.setText("Sales recorded today")
        else:
            prefix = "+" if sales_change >= 0 else ""
            self.card_sales.sub_label.setText(f"{prefix}{sales_change:.0f}% from yesterday")
        self.notification_btn.setText(f"Alerts: {low_stock + expiring}")

    def update_charts(self, transactions):
        sales_values = [(row.get("chart_label", row["date"]), row["total"]) for row in transactions[:7]]
        status_counts = {}
        for row in transactions:
            status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
        self.sales_chart.set_values(list(reversed(sales_values)))
        self.status_chart.set_values(sorted(status_counts.items(), key=lambda item: item[0]))

    def display_recent_transactions(self, transactions):
        if not transactions:
            self.table.clearSpans()
            self.table.setRowCount(1)
            empty = QTableWidgetItem("No transactions recorded for this period.")
            empty.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setSpan(0, 0, 1, self.table.columnCount())
            self.table.setItem(0, 0, empty)
            return
        self.table.clearSpans()
        self.table.setRowCount(len(transactions))
        for row, txn in enumerate(transactions):
            self.table.setItem(row, 0, QTableWidgetItem(txn['order_code']))
            self.table.setItem(row, 1, QTableWidgetItem(txn['order_date']))
            self.table.setItem(row, 2, QTableWidgetItem(txn['customer_name']))
            self.table.setItem(row, 3, QTableWidgetItem(f"₱{txn['total_amount']:,.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(txn['status']))