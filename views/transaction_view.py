from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QFrame, QRadioButton, QScrollArea, QButtonGroup,
                             QFileDialog)
from PyQt6.QtCore import pyqtSignal, Qt

# Any QLabel/QRadioButton placed inside a card that has its own
# background/border style will otherwise inherit that same background+
# border on itself individually (Qt cascades non-inherited properties like
# border/background down to children that don't set their own override -
# even from a bare "background:white;border:1px solid ...;" declaration
# with no type selector). Every plain label/radio inside a styled card
# needs this explicit reset, or it renders as its own little box.
RESET = "background: transparent; border: none;"
CAPTION_STYLE = f"font-size: 12px; font-weight: 600; color: #8A8074; {RESET}"
CARD_STYLE = "background: white; border-radius: 10px; border: 1px solid #E5E0D5;"


def field_group(label_text, widget):
    box = QVBoxLayout()
    box.setSpacing(6)
    lbl = QLabel(label_text)
    lbl.setStyleSheet(CAPTION_STYLE)
    box.addWidget(lbl)
    box.addWidget(widget)
    return box


class TransactionView(QWidget):
    item_added_to_cart = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #F7F3EB;")
        self.cart_items = []
        self.current_total = 0.0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(30, 25, 30, 25)
        outer.setSpacing(16)

        # ---- Page header ----
        title = QLabel("Record Transaction")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: #2A2421; {RESET}")
        subtitle = QLabel("Process real-time walk-in and online transactions.")
        subtitle.setStyleSheet(f"font-size: 13px; color: #777777; {RESET}")
        outer.addWidget(title)
        outer.addWidget(subtitle)

        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)
        outer.addLayout(main_layout)

        # ================= LEFT COLUMN =================
        left_col = QVBoxLayout()
        left_col.setSpacing(16)

        # Tabs for Walk-in / Online
        tab_layout = QHBoxLayout()
        self.walkin_tab = QPushButton("Walk-in")
        self.online_tab = QPushButton("Online Orders")
        for btn in [self.walkin_tab, self.online_tab]:
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton { padding: 8px 18px; border-radius: 6px; font-weight: bold; background: #E8E2D5; border: none; }
                QPushButton:checked { background: #C09E3B; color: white; }
            """)
        self.walkin_tab.setChecked(True)
        tab_grp = QButtonGroup(self)
        tab_grp.addButton(self.walkin_tab)
        tab_grp.addButton(self.online_tab)
        self.online_tab.toggled.connect(self._toggle_delivery_address)
        tab_layout.addWidget(self.walkin_tab)
        tab_layout.addWidget(self.online_tab)
        tab_layout.addStretch()
        left_col.addLayout(tab_layout)

        # ---- Customer Information card ----
        cust_box = QFrame()
        cust_box.setObjectName("custCard")
        cust_box.setStyleSheet(f"QFrame#custCard {{ {CARD_STYLE} }}")
        cust_layout = QVBoxLayout(cust_box)
        cust_layout.setContentsMargins(20, 18, 20, 18)
        cust_layout.setSpacing(14)

        cust_title = QLabel("Customer Information")
        cust_title.setStyleSheet(f"font-weight: bold; color: #2A2421; {RESET}")
        cust_layout.addWidget(cust_title)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Maria Santos")
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("e.g. 09171234567")

        name_phone_row = QHBoxLayout()
        name_phone_row.setSpacing(16)
        name_phone_row.addLayout(field_group("Customer Name", self.name_input), 1)
        name_phone_row.addLayout(field_group("Contact Number", self.phone_input), 1)
        cust_layout.addLayout(name_phone_row)

        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Delivery address for online orders...")
        self.address_group = field_group("Delivery Address", self.address_input)
        self._address_group_widgets = [self.address_group.itemAt(i).widget() for i in range(self.address_group.count())]
        cust_layout.addLayout(self.address_group)
        self._toggle_delivery_address(False)  # hidden by default - Walk-in is checked first

        left_col.addWidget(cust_box)

        # ---- Product Catalog ----
        catalog_toolbar = QHBoxLayout()
        cat_title = QLabel("Product Catalog")
        cat_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: #2A2421; {RESET}")
        self.catalog_count = QLabel("0 products")
        self.catalog_count.setStyleSheet(f"font-size: 11px; color: #8A8074; {RESET}")
        catalog_toolbar.addWidget(cat_title)
        catalog_toolbar.addStretch()
        catalog_toolbar.addWidget(self.catalog_count)
        left_col.addLayout(catalog_toolbar)

        catalog_filter_row = QHBoxLayout()
        catalog_filter_row.setSpacing(6)
        self.catalog_filter_buttons = {}
        for category in ("All", "Clothing", "Skincare"):
            filter_btn = QPushButton(category)
            filter_btn.setCheckable(True)
            filter_btn.setChecked(category == "All")
            filter_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            filter_btn.setStyleSheet("""
                QPushButton {
                    background: #FFFDF8;
                    color: #6D6257;
                    border: 1px solid #E5DCCA;
                    border-radius: 5px;
                    padding: 5px 10px;
                    font-size: 11px;
                }
                QPushButton:checked {
                    background: #FFF4C9;
                    color: #9A7415;
                    border: 1px solid #D5AD36;
                }
            """)
            filter_btn.clicked.connect(lambda checked, value=category: self._set_catalog_filter(value))
            self.catalog_filter_buttons[category] = filter_btn
            catalog_filter_row.addWidget(filter_btn)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search product name or SKU")
        self.search_input.setStyleSheet(
            "padding: 7px 10px; border: 1px solid #E5DCCA; border-radius: 5px; background: #FFFDFB;"
        )
        self.search_input.textChanged.connect(self._apply_catalog_filters)
        catalog_filter_row.addWidget(self.search_input, stretch=1)
        left_col.addLayout(catalog_filter_row)

        catalog_card = QFrame()
        catalog_card.setObjectName("catalogCard")
        catalog_card.setStyleSheet(f"QFrame#catalogCard {{ {CARD_STYLE} }}")
        catalog_card_layout = QVBoxLayout(catalog_card)
        catalog_card_layout.setContentsMargins(4, 4, 4, 4)

        self.catalog_scroll = QScrollArea()
        self.catalog_scroll.setWidgetResizable(True)
        self.catalog_scroll.setStyleSheet(f"QScrollArea {{ {RESET} }}")
        self.catalog_container = QWidget()
        self.catalog_container.setStyleSheet(RESET)
        self.catalog_layout = QVBoxLayout(self.catalog_container)
        self.catalog_layout.setSpacing(0)
        self.catalog_layout.setContentsMargins(0, 0, 0, 0)
        self.catalog_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.catalog_scroll.setWidget(self.catalog_container)
        catalog_card_layout.addWidget(self.catalog_scroll)
        left_col.addWidget(catalog_card, stretch=1)

        main_layout.addLayout(left_col, 60)

        # ================= RIGHT COLUMN =================
        right_box = QFrame()
        right_box.setObjectName("cartCard")
        right_box.setStyleSheet(f"QFrame#cartCard {{ {CARD_STYLE} }}")
        right_layout = QVBoxLayout(right_box)
        right_layout.setContentsMargins(20, 18, 20, 18)
        right_layout.setSpacing(10)

        cart_header = QHBoxLayout()
        cart_title_box = QVBoxLayout()
        cart_title = QLabel("Selected Items")
        cart_title.setStyleSheet(f"font-size: 18px; color: #20283A; {RESET}")
        self.cart_summary = QLabel("0 products \u2022 0 units")
        self.cart_summary.setStyleSheet(f"font-size: 11px; color: #7C8798; {RESET}")
        cart_title_box.addWidget(cart_title)
        cart_title_box.addWidget(self.cart_summary)
        cart_header.addLayout(cart_title_box)
        cart_header.addStretch()
        self.cart_count_badge = QLabel("0")
        self.cart_count_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cart_count_badge.setFixedSize(28, 28)
        self.cart_count_badge.setStyleSheet(
            "background: #FFF2C8; color: #B78912; border-radius: 14px; font-weight: bold;"
        )
        cart_header.addWidget(self.cart_count_badge)
        right_layout.addLayout(cart_header)

        self.cart_scroll = QScrollArea()
        self.cart_scroll.setWidgetResizable(True)
        self.cart_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.cart_scroll.setStyleSheet(f"QScrollArea {{ {RESET} }}")
        self.cart_container = QWidget()
        self.cart_container.setStyleSheet(RESET)
        self.cart_layout = QVBoxLayout(self.cart_container)
        self.cart_layout.setSpacing(8)
        self.cart_layout.setContentsMargins(0, 0, 0, 0)
        self.cart_scroll.setWidget(self.cart_container)
        right_layout.addWidget(self.cart_scroll, stretch=1)

        self.empty_cart_label = QLabel("No items selected yet.")
        self.empty_cart_label.setStyleSheet(f"color: #A39B90; font-size: 12px; {RESET}")
        self.empty_cart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cart_layout.addWidget(self.empty_cart_label)

        total_row = QHBoxLayout()
        total_caption = QLabel("Total Amount")
        total_caption.setStyleSheet(f"font-size: 12px; font-weight: 600; color: #6F7B8D; {RESET}")
        self.total_label = QLabel("\u20b10.00")
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.total_label.setStyleSheet(f"font-size: 26px; font-weight: bold; color: #20283A; {RESET}")
        total_row.addWidget(total_caption)
        total_row.addStretch()
        total_row.addWidget(self.total_label)
        right_layout.addLayout(total_row)

        pay_title = QLabel("Payment Method")
        pay_title.setStyleSheet(f"font-weight: 600; color: #2A2421; {RESET}")
        right_layout.addWidget(pay_title)

        self.pay_cash = QRadioButton("Cash")
        self.pay_gcash = QRadioButton("GCash")
        self.pay_bank = QRadioButton("Online Banking")
        for rb in (self.pay_cash, self.pay_gcash, self.pay_bank):
            rb.setMinimumHeight(38)
            rb.setStyleSheet("""
                QRadioButton {
                    background: #FFFDFB;
                    color: #20283A;
                    border: 1px solid #E6DCCB;
                    border-radius: 6px;
                    padding: 0 10px;
                }
                QRadioButton:checked {
                    background: #FFF5D4;
                    border: 1px solid #D5AA27;
                    font-weight: bold;
                }
            """)
        self.pay_gcash.setChecked(True)
        right_layout.addWidget(self.pay_cash)
        right_layout.addWidget(self.pay_gcash)
        right_layout.addWidget(self.pay_bank)

        receipt_title = QLabel("Upload Receipt Image")
        receipt_title.setStyleSheet(f"font-size: 12px; font-weight: 600; color: #20283A; margin-top: 6px; {RESET}")
        right_layout.addWidget(receipt_title)

        receipt_box = QFrame()
        receipt_box.setObjectName("receiptBox")
        receipt_box.setMinimumHeight(62)
        receipt_box.setStyleSheet("""
            QFrame#receiptBox {
                background: #FFF8DD;
                border: 1px dashed #D5AA27;
                border-radius: 7px;
            }
        """)
        receipt_layout = QHBoxLayout(receipt_box)
        receipt_layout.setContentsMargins(12, 8, 8, 8)
        receipt_layout.setSpacing(8)
        self.receipt_status = QLabel("No receipt uploaded")
        self.receipt_status.setStyleSheet(f"font-size: 11px; color: #7C8798; {RESET}")
        upload_btn = QPushButton("Upload")
        upload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        upload_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #B78912;
                border: none;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover { color: #8B6820; }
        """)
        upload_btn.clicked.connect(self._choose_receipt)
        receipt_layout.addWidget(self.receipt_status, stretch=1)
        receipt_layout.addWidget(upload_btn)
        right_layout.addWidget(receipt_box)

        self.confirm_btn = QPushButton("Confirm Transaction")
        self.confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background: #C09E3B;
                color: white;
                font-weight: bold;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover { background: #A9872E; }
        """)
        right_layout.addWidget(self.confirm_btn)

        main_layout.addWidget(right_box, 40)

    # ---------------------------------------------------------------
    def _choose_receipt(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Receipt",
            "",
            "Images (*.png *.jpg *.jpeg);;All Files (*)",
        )
        if file_path:
            self.receipt_status.setText(file_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1])

    def _toggle_delivery_address(self, online_checked):
        for w in self._address_group_widgets:
            w.setVisible(online_checked)

    def _set_catalog_filter(self, category):
        for name, button in self.catalog_filter_buttons.items():
            button.setChecked(name == category)
        self._apply_catalog_filters()

    def _apply_catalog_filters(self):
        category = next(
            (name for name, button in self.catalog_filter_buttons.items() if button.isChecked()),
            "All",
        )
        query = self.search_input.text().strip().lower()
        filtered = [
            product for product in self._catalog_products
            if (category == "All" or category.lower() in product['category'].lower())
            and (not query or query in product['name'].lower() or query in str(product['id']))
        ]
        self._render_catalog(filtered)

    def populate_catalog(self, products):
        self._catalog_products = products
        self.catalog_count.setText(f"{len(products)} products")
        self._apply_catalog_filters()

    def _render_catalog(self, products):
        while self.catalog_layout.count():
            item = self.catalog_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        headers = QFrame()
        headers.setFixedHeight(28)
        headers.setStyleSheet(f"background: #FFFDF8; border: none; {RESET}")
        header_layout = QHBoxLayout(headers)
        header_layout.setContentsMargins(10, 3, 10, 3)
        for text, width in (("PRODUCT", 1), ("STOCK", 0), ("PRICE", 0), ("QUANTITY", 0), ("ACTION", 0)):
            label = QLabel(text)
            label.setStyleSheet(f"font-size: 9px; font-weight: bold; color: #766B60; {RESET}")
            if text == "PRODUCT":
                header_layout.addWidget(label, stretch=1)
            elif text == "QUANTITY":
                label.setFixedWidth(62)
                header_layout.addWidget(label)
            else:
                label.setFixedWidth(70 if text != "ACTION" else 58)
                header_layout.addWidget(label)
        self.catalog_layout.addWidget(headers)

        for i, prod in enumerate(products):
            row = QFrame()
            row.setObjectName("catalogRow")
            row.setFixedHeight(58)
            row.setStyleSheet(f"""
                QFrame#catalogRow {{
                    background: {'#FFFDF8' if i % 2 == 0 else '#F5EFE4'};
                    border-bottom: 1px solid #E8DFD0;
                }}
                QFrame#catalogRow:hover {{ background: #EFE3C9; }}
            """)
            r_layout = QHBoxLayout(row)
            r_layout.setContentsMargins(14, 6, 14, 6)

            info = QLabel(f"<b>{prod['name']}</b><br><span style='color:#8A8074;'>{prod['category']}</span>")
            info.setStyleSheet(RESET)

            price = QLabel(f"\u20b1{prod['price']:,.2f}")
            price.setFixedWidth(70)
            price.setStyleSheet(f"font-weight: bold; font-size: 12px; color: #2A2421; {RESET}")

            stock = QLabel(f"{prod['stock_qty']} pcs")
            stock.setFixedWidth(70)
            stock.setStyleSheet(f"color: {'#C94C4C' if prod['stock_qty'] <= 10 else '#766B60'}; {RESET}")

            quantity_box = QFrame()
            quantity_box.setFixedWidth(62)
            quantity_box.setStyleSheet("background: transparent; border: none;")
            quantity_layout = QHBoxLayout(quantity_box)
            quantity_layout.setContentsMargins(0, 0, 0, 0)
            quantity_layout.setSpacing(0)

            minus_btn = QPushButton("-")
            minus_btn.setFixedSize(20, 24)
            minus_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            minus_btn.setStyleSheet("""
                QPushButton { background: #FFFDF8; color: #756B60; border: 1px solid #E5DCCA; border-radius: 4px 0 0 4px; font-weight: bold; }
                QPushButton:hover { background: #F3E7D3; }
            """)
            minus_btn.clicked.connect(lambda checked, product_id=prod['id']: self.remove_from_selected(product_id))

            qty_lbl = QLabel(str(self._cart_quantity(prod['id'])))
            qty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            qty_lbl.setFixedSize(22, 24)
            qty_lbl.setStyleSheet("background: #FFFDF8; color: #2A2421; border-top: 1px solid #E5DCCA; border-bottom: 1px solid #E5DCCA;")

            plus_btn = QPushButton("+")
            plus_btn.setFixedSize(20, 24)
            plus_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            plus_btn.setStyleSheet("""
                QPushButton { background: #FFFDF8; color: #756B60; border: 1px solid #E5DCCA; border-radius: 0 4px 4px 0; font-weight: bold; }
                QPushButton:hover { background: #F3E7D3; }
            """)
            plus_btn.clicked.connect(lambda checked, product=prod: self.item_added_to_cart.emit(product))
            quantity_layout.addWidget(minus_btn)
            quantity_layout.addWidget(qty_lbl)
            quantity_layout.addWidget(plus_btn)

            add_btn = QPushButton("Add")
            add_btn.setFixedWidth(58)
            add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            add_btn.setStyleSheet(
                "background: #C09E3B; color: white; padding: 6px 8px; border-radius: 4px; border: none;"
            )
            add_btn.clicked.connect(lambda ch, p=prod: self.item_added_to_cart.emit(p))

            r_layout.addWidget(info)
            r_layout.addWidget(stock)
            r_layout.addWidget(price)
            r_layout.addWidget(quantity_box)
            r_layout.addWidget(add_btn)
            self.catalog_layout.addWidget(row)

        self.catalog_layout.addStretch(1)

    def _cart_quantity(self, product_id):
        return next((item['qty'] for item in self.cart_items if item['id'] == product_id), 0)

    def add_to_selected(self, product):
        for item in self.cart_items:
            if item['id'] == product['id']:
                item['qty'] += 1
                self.refresh_cart_ui()
                self._apply_catalog_filters()
                return

        self.cart_items.append({
            'id': product['id'],
            'name': product['name'],
            'price': product['price'],
            'qty': 1
        })
        self.refresh_cart_ui()
        self._apply_catalog_filters()

    def remove_from_selected(self, product_id):
        for item in self.cart_items:
            if item['id'] == product_id:
                item['qty'] -= 1
                if item['qty'] <= 0:
                    self.cart_items.remove(item)
                self.refresh_cart_ui()
                self._apply_catalog_filters()
                return

    def refresh_cart_ui(self):
        while self.cart_layout.count():
            item = self.cart_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.current_total = 0.0

        if not self.cart_items:
            empty = QLabel("No items selected yet.")
            empty.setStyleSheet(f"color: #A39B90; font-size: 12px; {RESET}")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cart_layout.addWidget(empty)

        for item in self.cart_items:
            line_total = item['price'] * item['qty']
            self.current_total += line_total

            box = QFrame()
            box.setStyleSheet(f"border-bottom: 1px solid #E8E0D4; {RESET}")
            b_layout = QHBoxLayout(box)
            b_layout.setContentsMargins(0, 5, 0, 5)

            name_column = QVBoxLayout()
            name_column.setSpacing(1)
            name_lbl = QLabel(item['name'])
            name_lbl.setStyleSheet(f"font-size: 12px; color: #20283A; {RESET}")
            price_lbl = QLabel(f"\u20b1{item['price']:,.2f} each")
            price_lbl.setStyleSheet(f"font-size: 10px; color: #7C8798; {RESET}")
            name_column.addWidget(name_lbl)
            name_column.addWidget(price_lbl)
            qty_lbl = QLabel(f"x{item['qty']}")
            qty_lbl.setFixedWidth(28)
            qty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            qty_lbl.setStyleSheet(f"font-weight: bold; color: #C09E3B; {RESET}")
            total_lbl = QLabel(f"\u20b1{line_total:,.2f}")
            total_lbl.setFixedWidth(76)
            total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            total_lbl.setStyleSheet(f"font-size: 12px; color: #20283A; {RESET}")

            b_layout.addLayout(name_column, stretch=1)
            b_layout.addWidget(qty_lbl)
            b_layout.addWidget(total_lbl)
            self.cart_layout.addWidget(box)

        product_count = len(self.cart_items)
        unit_count = sum(item['qty'] for item in self.cart_items)
        self.cart_summary.setText(f"{product_count} products \u2022 {unit_count} units")
        self.cart_count_badge.setText(str(product_count))
        self.total_label.setText(f"\u20b1{self.current_total:,.2f}")

    def get_selected_payment(self):
        if self.pay_cash.isChecked():
            return "Cash"
        elif self.pay_gcash.isChecked():
            return "GCash"
        return "Online Banking"

    def clear_form(self):
        self.name_input.clear()
        self.phone_input.clear()
        self.address_input.clear()
        self.cart_items = []
        self.refresh_cart_ui()