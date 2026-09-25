from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                             QHeaderView, QDialog, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from datetime import datetime
from views.styled_dropdown import StyledComboBox

RESET = "background: transparent; border: none;"
PLAIN_LABEL_STYLE = f"font-size: 12px; color: #777777; {RESET}"
TABLE_HEAD_STYLE = f"font-size: 11px; color: #8A8074; font-weight: 600; letter-spacing: 0.03em; {RESET}"
FIELD_STYLE = "padding: 9px 10px; font-size: 13px; border: 1px solid #D6CEBC; border-radius: 6px; background: white;"

SupplierComboBox = StyledComboBox


def labeled_field(label_text, widget):
    box = QVBoxLayout()
    box.setSpacing(3)
    lbl = QLabel(label_text)
    lbl.setStyleSheet(PLAIN_LABEL_STYLE)
    box.addWidget(lbl)
    box.addWidget(widget)
    return box


class PurchaseOrdersView(QWidget):
    order_details_requested = pyqtSignal(str)
    mark_received_requested = pyqtSignal(str)
    submit_order_requested = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.item_rows = [] 
        
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

        form_card = QFrame()
        form_card.setObjectName("poCard")
        form_card.setStyleSheet("""
            QFrame#poCard { background: white; border-radius: 10px; border: 1px solid #E5E0D5; }
        """)
        f_layout = QVBoxLayout(form_card)
        f_layout.setContentsMargins(20, 14, 20, 12)
        f_layout.setSpacing(10)

        f_title = QLabel("New Purchase Order")
        f_title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: #2A2421; {RESET}")
        f_layout.addWidget(f_title)

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

        action_row = QHBoxLayout()
        self.auto_fill_btn = QPushButton("⚡ Auto-Fill Low Stock")
        self.new_prod_btn = QPushButton("➕ Register New Product")
        for btn in (self.auto_fill_btn, self.new_prod_btn):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton { background: #F8F2E8; color: #C09E3B; font-weight: bold; 
                              padding: 6px 12px; border-radius: 5px; border: 1px solid #E5E0D5; font-size: 11px;}
                QPushButton:hover { background: #EFE9DD; }
            """)
        action_row.addWidget(self.auto_fill_btn)
        action_row.addStretch()
        action_row.addWidget(self.new_prod_btn)
        f_layout.addLayout(action_row)

        item_table = QFrame()
        item_table.setObjectName("itemTable")
        item_table.setStyleSheet("""
            QFrame#itemTable { background: #FBF7EF; border: 1px solid #EFE7D6; border-radius: 8px; }
        """)
        item_container = QVBoxLayout(item_table)
        item_container.setContentsMargins(12, 8, 12, 8)
        item_container.setSpacing(6)

        head_row = QHBoxLayout()
        head_row.setSpacing(12)
        h_product = QLabel("PRODUCT")
        h_qty = QLabel("QTY")
        h_cost = QLabel("UNIT COST (\u20b1)")
        h_total = QLabel("LINE TOTAL (\u20b1)")
        for h in (h_product, h_qty, h_cost, h_total):
            h.setStyleSheet(TABLE_HEAD_STYLE)
            
        head_row.addWidget(h_product, 3)
        head_row.addWidget(h_qty, 1)
        head_row.addWidget(h_cost, 1)
        head_row.addWidget(h_total, 1)
        head_row.addSpacing(30)
        item_container.addLayout(head_row)

        self.dynamic_items_layout = QVBoxLayout()
        self.dynamic_items_layout.setSpacing(8)
        item_container.addLayout(self.dynamic_items_layout)
        
        self.add_item_row()

        self.add_row_btn = QPushButton("➕ Add Another Item")
        self.add_row_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_row_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #7C8798; font-weight: bold; font-size: 11px; text-align: left; padding: 4px 0px;}
            QPushButton:hover { color: #20283A; }
        """)
        self.add_row_btn.clicked.connect(self.add_item_row)
        item_container.addWidget(self.add_row_btn)

        f_layout.addWidget(item_table)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: #EFE9DD; max-height: 1px; border: none;")
        f_layout.addWidget(divider)

        bottom_bar = QHBoxLayout()
        self.subtotal_lbl = QLabel("Estimated Subtotal: \u20b10.00")
        self.subtotal_lbl.setStyleSheet(f"font-weight: bold; font-size: 14px; color: #2A2421; {RESET}")

        self.submit_po_btn = QPushButton("Submit Order")
        self.submit_po_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit_po_btn.setStyleSheet("""
            QPushButton { background: #C09E3B; color: white; font-weight: bold; padding: 9px 20px; border-radius: 6px; border: none; }
            QPushButton:hover { background: #A9872E; }
        """)
        self.submit_po_btn.clicked.connect(self._validate_and_submit)

        bottom_bar.addWidget(self.subtotal_lbl)
        bottom_bar.addStretch()
        bottom_bar.addWidget(self.submit_po_btn)
        f_layout.addLayout(bottom_bar)
        layout.addWidget(form_card)

        history_card = QFrame()
        history_card.setObjectName("historyCard")
        history_card.setStyleSheet("QFrame#historyCard { background: #FFFDFB; border: 1px solid #E1D7C7; border-radius: 9px; }")
        history_layout = QVBoxLayout(history_card)
        history_layout.setContentsMargins(0, 0, 0, 0)
        hist_title = QLabel("Purchase Order History")
        hist_title.setStyleSheet(f"font-size: 13px; font-weight: bold; color: #20283A; padding: 12px 14px; {RESET}")
        history_layout.addWidget(hist_title)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels(["PO#", "SUPPLIER", "DATE ORDERED", "TOTAL COST", "STATUS", "ACTION"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.verticalHeader().setDefaultSectionSize(40)
        self.history_table.setShowGrid(True)
        self.history_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.setStyleSheet("""
            QTableWidget { background: #FFFDFB; border: none; gridline-color: #E8DFD0; color: #20283A; outline: none; }
            QTableWidget::item { padding: 7px 10px; border: none; }
            QHeaderView::section { background: #F8F2E8; color: #7C8798; font-weight: bold; font-size: 10px; border: none; border-bottom: 1px solid #E1D7C7; padding: 7px 10px; }
        """)
        history_layout.addWidget(self.history_table)
        layout.addWidget(history_card, 1)

    def add_item_row(self):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(12)

        prod_combo = StyledComboBox()
        prod_combo.setEditable(True)
        prod_combo.addItems(["Select Product...", "Luxe Organix Soothing Gel", "Dermorepubliq Serum", "Argan Oil", "Blue Tee"])
        
        qty_input = QLineEdit()
        qty_input.setPlaceholderText("0")
        qty_input.setStyleSheet(FIELD_STYLE)
        
        cost_input = QLineEdit()
        cost_input.setPlaceholderText("0.00")
        cost_input.setStyleSheet(FIELD_STYLE)
        
        line_total_lbl = QLabel("\u20b10.00")
        line_total_lbl.setStyleSheet(f"font-size: 13px; font-weight: bold; color: #20283A; {RESET}")

        del_btn = QPushButton("\U0001F5D1") 
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setFixedSize(28, 28)
        del_btn.setStyleSheet("background: transparent; border: none; color: #B04A4A; font-size: 13px;")

        row_layout.addWidget(prod_combo, 3)
        row_layout.addWidget(qty_input, 1)
        row_layout.addWidget(cost_input, 1)
        row_layout.addWidget(line_total_lbl, 1)
        row_layout.addWidget(del_btn)

        row_data = {
            'widget': row_widget,
            'combo': prod_combo,
            'qty': qty_input,
            'cost': cost_input,
            'line_lbl': line_total_lbl
        }
        
        qty_input.textChanged.connect(self._recalculate_totals)
        cost_input.textChanged.connect(self._recalculate_totals)
        del_btn.clicked.connect(lambda: self._remove_item_row(row_data))

        self.dynamic_items_layout.addWidget(row_widget)
        self.item_rows.append(row_data)

    def _remove_item_row(self, row_data):
        if len(self.item_rows) > 1:
            self.dynamic_items_layout.removeWidget(row_data['widget'])
            row_data['widget'].deleteLater()
            self.item_rows.remove(row_data)
            self._recalculate_totals()
        else:
            row_data['combo'].setCurrentIndex(0)
            row_data['qty'].clear()
            row_data['cost'].clear()

    def _recalculate_totals(self):
        grand_total = 0.0
        for row in self.item_rows:
            try:
                qty_text = row['qty'].text().strip()
                cost_text = row['cost'].text().strip()
                qty = int(qty_text) if qty_text else 0
                cost = float(cost_text) if cost_text else 0.0
                line_total = qty * cost
                row['line_lbl'].setText(f"\u20b1{line_total:,.2f}")
                grand_total += line_total
            except ValueError:
                row['line_lbl'].setText("\u20b10.00")
                
        self.subtotal_lbl.setText(f"Estimated Subtotal: \u20b1{grand_total:,.2f}")

    def _validate_and_submit(self):
        try:
            supplier = self.supplier_combo.currentText()
            if supplier == "Select Supplier" or not supplier.strip():
                QMessageBox.warning(self, "Validation Error", "Please select a supplier.")
                return

            delivery_date = self.date_input.text().strip()
            if not delivery_date:
                QMessageBox.warning(self, "Validation Error", "Please enter an expected delivery date.")
                return

            items_to_order = []
            for row in self.item_rows:
                prod_name = row['combo'].currentText()
                if prod_name == "Select Product..." or not prod_name.strip():
                    continue 

                try:
                    qty = int(row['qty'].text().strip())
                    if qty <= 0:
                        raise ValueError
                except ValueError:
                    QMessageBox.warning(self, "Validation Error", f"Please enter a valid quantity greater than 0 for '{prod_name}'.")
                    return

                try:
                    cost = float(row['cost'].text().strip())
                    if cost < 0:
                        raise ValueError
                except ValueError:
                    QMessageBox.warning(self, "Validation Error", f"Please enter a valid unit cost for '{prod_name}'.")
                    return

                items_to_order.append({
                    'product': prod_name,
                    'quantity': qty,
                    'unit_cost': cost,
                    'line_total': qty * cost
                })

            if not items_to_order:
                QMessageBox.warning(self, "Validation Error", "Please add at least one valid product to the order.")
                return

            order_data = {
                'supplier': supplier,
                'expected_date': delivery_date,
                'items': items_to_order
            }
            
            self.submit_order_requested.emit(order_data)
            
            # Optional: Clear the form after a successful validation/emit
            # self.supplier_combo.setCurrentIndex(0)
            # while len(self.item_rows) > 1:
            #     self._remove_item_row(self.item_rows[-1])
            # self._remove_item_row(self.item_rows[0])
            
        except Exception as e:
            QMessageBox.critical(self, "System Error", f"An unexpected error occurred during submission:\n{str(e)}")

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
            QFrame { background: #FFFDFB; border: 1px solid #E1D7C7; border-radius: 9px; }
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
        
        if details['status'] == "Pending":
            order_status.setStyleSheet("color: #B45309; background: #FFF9E8; border: 1px solid #C97816; border-radius: 5px; padding: 3px 9px; font-size: 10px;")
        else:
            order_status.setStyleSheet("color: #118443; background: #F2FFF6; border: 1px solid #22A05A; border-radius: 5px; padding: 3px 9px; font-size: 10px;")
            
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
            summary_box.setStyleSheet("background: #FBF4E8; border: none; border-radius: 6px;")
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
                border-bottom: 1px solid #E1D7C7; padding: 7px 9px; font-size: 9px; font-weight: bold;
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
                    Qt.AlignmentFlag.AlignRight if column in (1, 2, 3) else Qt.AlignmentFlag.AlignLeft
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
        
        btn_row = QHBoxLayout()
        
        if details['status'] == "Pending":
            receive_btn = QPushButton("Mark as Received")
            receive_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            receive_btn.setStyleSheet("background: #118443; color: white; font-weight: bold; padding: 9px 22px; border: none; border-radius: 5px;")
            receive_btn.clicked.connect(lambda: self.mark_received_requested.emit(details['po_number']))
            receive_btn.clicked.connect(dialog.accept) 
            btn_row.addWidget(receive_btn)

        btn_row.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("background: #C09E3B; color: white; font-weight: bold; padding: 9px 22px; border: none; border-radius: 5px;")
        close_btn.clicked.connect(dialog.accept)
        btn_row.addWidget(close_btn)
        
        layout.addLayout(btn_row)
        dialog.exec()