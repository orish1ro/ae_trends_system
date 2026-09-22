from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                             QHeaderView, QComboBox)
from PyQt6.QtCore import Qt
from datetime import datetime

RESET = "background: transparent; border: none;"
PLAIN_LABEL_STYLE = f"font-size: 12px; color: #777777; {RESET}"
TABLE_HEAD_STYLE = f"font-size: 11px; color: #8A8074; font-weight: 600; letter-spacing: 0.03em; {RESET}"
FIELD_STYLE = "padding: 9px 10px; font-size: 13px; border: 1px solid #D6CEBC; border-radius: 6px; background: white;"


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
        self.supplier_combo = QComboBox()
        self.supplier_combo.addItems(["Select Supplier", "Manila Textile Co.",
                                      "Skincare Lab Ph", "Apparel Prime Inc."])
        self.supplier_combo.setStyleSheet(FIELD_STYLE)
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

        # ---- PO History: gets all the remaining vertical space ----
        hist_title = QLabel("Purchase Order History")
        hist_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: #2A2421; {RESET}")
        layout.addWidget(hist_title)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels(
            ["PO#", "SUPPLIER", "DATE ORDERED", "TOTAL COST", "STATUS", "ACTION"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.verticalHeader().setDefaultSectionSize(36)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.setStyleSheet("""
            QTableWidget {
                background: white;
                border-radius: 8px;
                border: 1px solid #E5E0D5;
                gridline-color: #F0EAE1;
            }
            QHeaderView::section {
                background: #FBF7EF;
                color: #8A8074;
                font-weight: 600;
                font-size: 11px;
                border: none;
                border-bottom: 1px solid #E5E0D5;
                padding: 8px;
            }
        """)
        # Stretch factor of 1 means this table absorbs all the extra
        # vertical space freed up by shrinking the form card above.
        layout.addWidget(self.history_table, 1)

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
            self.history_table.setItem(row, 4, QTableWidgetItem(po['status']))

            details_btn = QPushButton("Order Details")
            details_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            details_btn.setStyleSheet(
                "background: #C09E3B; color: white; font-weight: bold; "
                "padding: 4px 10px; border-radius: 4px; border: none; font-size: 11px;"
            )
            self.history_table.setCellWidget(row, 5, details_btn)