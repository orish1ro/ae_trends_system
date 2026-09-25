from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                             QHeaderView, QDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtCore import pyqtSignal
from datetime import datetime
from views.styled_dropdown import StyledComboBox

RESET = "background: transparent; border: none;"
PLAIN_LABEL_STYLE = f"font-size: 12px; color: #777777; {RESET}"
TABLE_HEAD_STYLE = f"font-size: 11px; color: #8A8074; font-weight: 600; letter-spacing: 0.03em; {RESET}"
FIELD_STYLE = "padding: 9px 10px; font-size: 13px; border: 1px solid #D6CEBC; border-radius: 6px; background: white;"


SupplierComboBox = StyledComboBox


def labeled_field(label_text, widget):
    """Label sits above the input, both in one tidy column. Plain style -
    used for Supplier / Expected Delivery Date, which read as normal form
    fields rather than table columns."""
    box = QVBoxLayout()
    box.setSpacing(3)
    lbl = QLabel(label_text)
    lbl.setStyleSheet(PLAIN_LABEL_STYLE)
    box.addWidget(lbl)
    box.addWidget(widget)
    return box


class PurchaseOrdersView(QWidget):
    order_details_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #F7F3EB;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 28, 30, 24)
        layout.setSpacing(14)

        title = QLabel("Purchase Orders")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: #2A2421; {RESET}")
        sub = QLabel("Create restocking orders and track external supplier history.")
        sub.setStyleSheet(f"font-size: 13px; color: #777777; {RESET}")
        layout.addWidget(title)
        layout.addWidget(sub)

        # ---- Compact card holds the whole form (kept small so the ----
        # ---- History table below gets most of the vertical space)  ----
        form_card = QFrame()
        form_card.setObjectName("poCard")
        form_card.setStyleSheet("""
            QFrame#poCard {
                background: white;
                border-radius: 10px;
                border: 1px solid #E5E0D5;
            }
        """)
        f_layout = QVBoxLayout(form_card)
        f_layout.setContentsMargins(20, 14, 20, 12)
        f_layout.setSpacing(10)

        f_title = QLabel("New Purchase Order")
        f_title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: #2A2421; {RESET}")
        f_layout.addWidget(f_title)

        # Row 1: Supplier + Expected Date (plain form fields)
        row1 = QHBoxLayout()
        row1.setSpacing(14)
        self.supplier_combo = SupplierComboBox()
        self.supplier_combo.addItems(["Select Supplier", "Manila Textile Co.",
                                      "Skincare Lab Ph", "Apparel Prime Inc."])
        self.date_input = QLineEdit()
        self.date_input.setText(datetime.now().strftime("%b %d, %Y"))
        self.date_input.setStyleSheet(FIELD_STYLE)
        row1.addLayout(labeled_field("Supplier", self.supplier_combo), 1)
        row1.addLayout(labeled_field("Expected Delivery Date", self.date_input), 1)
        f_layout.addLayout(row1)

        # ---- Item mini-table: shaded header bar + one input row + clear icon ----
        item_table = QFrame()
        item_table.setObjectName("itemTable")
        item_table.setStyleSheet("""
            QFrame#itemTable {
                background: #FBF7EF;
                border: 1px solid #EFE7D6;
                border-radius: 8px;
            }
        """)
        item_layout = QVBoxLayout(item_table)
        item_layout.setContentsMargins(12, 8, 12, 8)
        item_layout.setSpacing(6)

        head_row = QHBoxLayout()
        head_row.setSpacing(12)
        h_product = QLabel("PRODUCT")
        h_product.setStyleSheet(TABLE_HEAD_STYLE)
        h_qty = QLabel("QUANTITY")
        h_qty.setStyleSheet(TABLE_HEAD_STYLE)
        h_cost = QLabel("UNIT COST (\u20b1)")
        h_cost.setStyleSheet(TABLE_HEAD_STYLE)
        head_row.addWidget(h_product, 3)
        head_row.addWidget(h_qty, 1)
        head_row.addWidget(h_cost, 1)
        head_row.addSpacing(30)  # keeps header aligned with the row's trash-icon column below
        item_layout.addLayout(head_row)

        item_row = QHBoxLayout()
        item_row.setSpacing(12)
        self.item_name = QLineEdit()
        self.item_name.setPlaceholderText("e.g. Basic White Tee")
        self.item_qty = QLineEdit()
        self.item_qty.setPlaceholderText("0")
        self.item_cost = QLineEdit()
        self.item_cost.setPlaceholderText("0.00")
        for field in (self.item_name, self.item_qty, self.item_cost):
            field.setStyleSheet(FIELD_STYLE)

        clear_btn = QPushButton("\U0001F5D1")  # wastebasket glyph - clears this row's fields
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setFixedSize(28, 28)
        clear_btn.setStyleSheet(
            "background: transparent; border: none; color: #B04A4A; font-size: 13px;"
        )
        clear_btn.setToolTip("Clear this line")
        clear_btn.clicked.connect(self._clear_item_row)

        item_row.addWidget(self.item_name, 3)
        item_row.addWidget(self.item_qty, 1)
        item_row.addWidget(self.item_cost, 1)
        item_row.addWidget(clear_btn)
        item_layout.addLayout(item_row)

        f_layout.addWidget(item_table)

        # Divider + bottom bar (subtotal + submit)
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: #EFE9DD; max-height: 1px; border: none;")
        f_layout.addWidget(divider)

        bottom_bar = QHBoxLayout()
        self.subtotal_lbl = QLabel("Estimated Subtotal: \u20b118,000.00")
        self.subtotal_lbl.setStyleSheet(f"font-weight: bold; font-size: 14px; color: #2A2421; {RESET}")

        self.submit_po_btn = QPushButton("Submit Order")
        self.submit_po_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit_po_btn.setStyleSheet("""
            QPushButton {
                background: #C09E3B; color: white; font-weight: bold;
                padding: 9px 20px; border-radius: 6px; border: none;
            }
            QPushButton:hover { background: #A9872E; }
        """)

        bottom_bar.addWidget(self.subtotal_lbl)
        bottom_bar.addStretch()
        bottom_bar.addWidget(self.submit_po_btn)
        f_layout.addLayout(bottom_bar)
        layout.addWidget(form_card)

        # ---- PO History card ----
        history_card = QFrame()
        history_card.setObjectName("historyCard")
        history_card.setStyleSheet("""
            QFrame#historyCard {
                background: #FFFDFB;
                border: 1px solid #E1D7C7;
                border-radius: 9px;
            }
        """)
        history_layout = QVBoxLayout(history_card)
        history_layout.setContentsMargins(0, 0, 0, 0)
        hist_title = QLabel("Purchase Order History")
        hist_title.setStyleSheet(f"font-size: 13px; font-weight: bold; color: #20283A; padding: 12px 14px; {RESET}")
        history_layout.addWidget(hist_title)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels(
            ["PO#", "SUPPLIER", "DATE ORDERED", "TOTAL COST", "STATUS", "ACTION"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.verticalHeader().setDefaultSectionSize(40)
        self.history_table.setShowGrid(True)
        self.history_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.setStyleSheet("""
            QTableWidget {
                background: #FFFDFB;
                border: none;
                gridline-color: #E8DFD0;
                color: #20283A;
                outline: none;
            }
            QTableWidget::item { padding: 7px 10px; border: none; }
            QHeaderView::section {
                background: #F8F2E8;
                color: #7C8798;
                font-weight: bold;
                font-size: 10px;
                border: none;
                border-bottom: 1px solid #E1D7C7;
                padding: 7px 10px;
            }
        """)
        history_layout.addWidget(self.history_table)
        layout.addWidget(history_card, 1)

        self.item_qty.textChanged.connect(self._update_subtotal_preview)
        self.item_cost.textChanged.connect(self._update_subtotal_preview)

    def _clear_item_row(self):
        self.item_name.clear()
        self.item_qty.clear()
        self.item_cost.clear()

    def _update_subtotal_preview(self):
        self.subtotal_lbl.setText(f"Estimated Subtotal: \u20b1{self.get_estimated_total():,.2f}")

    def get_estimated_total(self):
        try:
            qty = int(self.item_qty.text())
            cost = float(self.item_cost.text())
            return qty * cost
        except ValueError:
            return 0.0

    def display_po_history(self, pos):
        self.history_table.setRowCount(len(pos))
        for row, po in enumerate(pos):
            self.history_table.setItem(row, 0, QTableWidgetItem(po['po_number']))
            self.history_table.setItem(row, 1, QTableWidgetItem(po['supplier']))
            self.history_table.setItem(row, 2, QTableWidgetItem(po['date_ordered']))
            self.history_table.setItem(row, 3, QTableWidgetItem(f"\u20b1{po['total_cost']:,.2f}"))

            for column in range(4):
                self.history_table.item(row, column).setTextAlignment(
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignCenter
                )
            self.history_table.item(row, 3).setTextAlignment(
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignCenter
            )

            status_badge = QLabel(po['status'])
            status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_badge.setFixedHeight(22)
            if po['status'] == "Pending":
                status_badge.setStyleSheet(
                    "color: #B45309; background: #FFF9E8; border: 1px solid #C97816; "
                    "border-radius: 5px; padding: 0 7px; font-size: 10px;"
                )
            else:
                status_badge.setStyleSheet(
                    "color: #118443; background: #F2FFF6; border: 1px solid #22A05A; "
                    "border-radius: 5px; padding: 0 7px; font-size: 10px;"
                )
            self.history_table.setCellWidget(row, 4, status_badge)

            details_btn = QPushButton("Order Details")
            details_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            details_btn.setStyleSheet(
                "background: #C09E3B; color: white; font-weight: bold; "
                "padding: 5px 10px; border-radius: 4px; border: none; font-size: 10px;"
            )
            details_btn.clicked.connect(
                lambda checked, po_number=po['po_number']:
                self.order_details_requested.emit(po_number)
            )
            self.history_table.setCellWidget(row, 5, details_btn)

    def show_order_details(self, details):
        dialog = QDialog(self)
        dialog.setWindowTitle("Purchase Order Details")
        dialog.setMinimumSize(760, 500)
        dialog.setStyleSheet("background: #F7F3EB; color: #20283A;")

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        title = QLabel("Purchase Order Details")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #20283A;")
        subtitle = QLabel(f"Latest purchase order from {details['supplier'].upper()}.")
        subtitle.setStyleSheet("font-size: 11px; color: #667085;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #FFFDFB;
                border: 1px solid #E1D7C7;
                border-radius: 9px;
            }
            QLabel { border: none; background: transparent; }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(10)

        order_header = QHBoxLayout()
        order_title = QLabel(f"{details['po_number']} - {details['supplier'].upper()}")
        order_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #20283A;")
        order_header.addWidget(order_title)
        order_header.addStretch()
        order_status = QLabel(details['status'])
        order_status.setStyleSheet(
            "color: #B45309; background: #FFF9E8; border: 1px solid #C97816; "
            "border-radius: 5px; padding: 3px 9px; font-size: 10px;"
        )
        order_header.addWidget(order_status)
        card_layout.addLayout(order_header)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background: #E8DFD0; max-height: 1px; border: none;")
        card_layout.addWidget(divider)

        summary_title = QLabel("Order Summary")
        summary_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #20283A;")
        card_layout.addWidget(summary_title)

        summary_row = QHBoxLayout()
        for label_text, value_text in (
            ("PO ID", details['po_number']),
            ("SUPPLIER", details['supplier']),
            ("ORDER DATE", details['order_date']),
            ("STATUS", details['status']),
            ("TOTAL COST", f"\u20b1{details['total_cost']:,.2f}"),
        ):
            summary_box = QFrame()
            summary_box.setStyleSheet(
                "background: #FBF4E8; border: none; border-radius: 6px;"
            )
            summary_layout = QVBoxLayout(summary_box)
            summary_layout.setContentsMargins(9, 7, 9, 7)
            label = QLabel(label_text)
            label.setStyleSheet("font-size: 8px; color: #7C8798;")
            value = QLabel(value_text)
            value.setStyleSheet("font-size: 11px; font-weight: bold; color: #20283A;")
            summary_layout.addWidget(label)
            summary_layout.addWidget(value)
            summary_row.addWidget(summary_box)
        card_layout.addLayout(summary_row)

        items_table = QTableWidget()
        items_table.setColumnCount(4)
        items_table.setHorizontalHeaderLabels(["ITEM", "QTY", "UNIT COST", "LINE TOTAL"])
        items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        items_table.verticalHeader().setVisible(False)
        items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        items_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        items_table.setStyleSheet("""
            QTableWidget { background: #FFFDFB; border: none; gridline-color: #E8DFD0; }
            QTableWidget::item { padding: 7px 9px; border: none; color: #20283A; }
            QHeaderView::section {
                background: #F8F2E8; color: #7C8798; border: none;
                border-bottom: 1px solid #E1D7C7; padding: 7px 9px;
                font-size: 9px; font-weight: bold;
            }
        """)
        items_table.setRowCount(len(details['items']))
        for row, item in enumerate(details['items']):
            values = [
                item['name'], str(item['quantity']),
                f"\u20b1{item['unit_cost']:,.2f}",
                f"\u20b1{item['line_total']:,.2f}",
            ]
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                cell.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | (
                    Qt.AlignmentFlag.AlignRight if column in (1, 2, 3)
                    else Qt.AlignmentFlag.AlignLeft
                ))
                items_table.setItem(row, column, cell)
        card_layout.addWidget(items_table)

        total_row = QHBoxLayout()
        total_row.addStretch()
        total_box = QFrame()
        total_box.setStyleSheet("background: #FBF4E8; border: 1px solid #E1D7C7; border-radius: 6px;")
        total_layout = QVBoxLayout(total_box)
        total_layout.setContentsMargins(12, 8, 12, 8)
        total_label = QLabel(f"Total                         \u20b1{details['total_cost']:,.2f}")
        total_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #20283A;")
        total_layout.addWidget(total_label)
        total_row.addWidget(total_box)
        card_layout.addLayout(total_row)

        layout.addWidget(card)
        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(
            "background: #C09E3B; color: white; font-weight: bold; "
            "padding: 9px 22px; border: none; border-radius: 5px;"
        )
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
        dialog.exec()