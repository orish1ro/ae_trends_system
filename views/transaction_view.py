from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QFrame, QRadioButton, QScrollArea, QButtonGroup)
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
        cat_title = QLabel("Product Catalog")
        cat_title.setStyleSheet(f"font-size: 16px; font-weight: bold; margin-top: 4px; color: #2A2421; {RESET}")
        left_col.addWidget(cat_title)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search products...")
        self.search_input.setStyleSheet(
            "padding: 8px 12px; border: 1px solid #CCCCCC; border-radius: 6px; background: white;"
        )
        left_col.addWidget(self.search_input)

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

        cart_title = QLabel("Selected Items")
        cart_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: #2A2421; {RESET}")
        right_layout.addWidget(cart_title)

        self.cart_scroll = QScrollArea()
        self.cart_scroll.setWidgetResizable(True)
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

        self.total_label = QLabel("Total Amount: \u20b10.00")
        self.total_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: #C09E3B; margin: 8px 0; {RESET}")
        right_layout.addWidget(self.total_label)

        pay_title = QLabel("Payment Method")
        pay_title.setStyleSheet(f"font-weight: 600; color: #2A2421; {RESET}")
        right_layout.addWidget(pay_title)

        self.pay_cash = QRadioButton("Cash")
        self.pay_gcash = QRadioButton("GCash")
        self.pay_bank = QRadioButton("Online Banking")
        for rb in (self.pay_cash, self.pay_gcash, self.pay_bank):
            rb.setStyleSheet(RESET)
        self.pay_gcash.setChecked(True)
        right_layout.addWidget(self.pay_cash)
        right_layout.addWidget(self.pay_gcash)
        right_layout.addWidget(self.pay_bank)

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
    def _toggle_delivery_address(self, online_checked):
        for w in self._address_group_widgets:
            w.setVisible(online_checked)

    def populate_catalog(self, products):
        while self.catalog_layout.count():
            item = self.catalog_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, prod in enumerate(products):
            row = QFrame()
            row.setFixedHeight(60)
            row.setStyleSheet(
                f"background: white; border-bottom: 1px solid #F0EAE1;"
                if i < len(products) - 1 else "background: white; border: none;"
            )
            r_layout = QHBoxLayout(row)
            r_layout.setContentsMargins(14, 6, 14, 6)

            info = QLabel(
                f"<b>{prod['name']}</b><br>"
                f"<span style='color:#777;'>{prod['category']} \u2022 {prod['stock_qty']} in stock</span>"
            )
            info.setStyleSheet(RESET)

            price = QLabel(f"\u20b1{prod['price']:,.2f}")
            price.setStyleSheet(f"font-weight: bold; font-size: 14px; color: #2A2421; {RESET}")

            add_btn = QPushButton("Add")
            add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            add_btn.setStyleSheet(
                "background: #C09E3B; color: white; padding: 6px 16px; border-radius: 4px; border: none;"
            )
            add_btn.clicked.connect(lambda ch, p=prod: self.item_added_to_cart.emit(p))

            r_layout.addWidget(info)
            r_layout.addStretch()
            r_layout.addWidget(price)
            r_layout.addWidget(add_btn)
            self.catalog_layout.addWidget(row)

    def add_to_selected(self, product):
        for item in self.cart_items:
            if item['id'] == product['id']:
                item['qty'] += 1
                self.refresh_cart_ui()
                return

        self.cart_items.append({
            'id': product['id'],
            'name': product['name'],
            'price': product['price'],
            'qty': 1
        })
        self.refresh_cart_ui()

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
            box.setStyleSheet(RESET)
            b_layout = QHBoxLayout(box)
            b_layout.setContentsMargins(0, 4, 0, 4)

            name_lbl = QLabel(f"{item['name']}\n\u20b1{item['price']:,.2f} each")
            name_lbl.setStyleSheet(RESET)
            qty_lbl = QLabel(f"x{item['qty']}")
            qty_lbl.setStyleSheet(f"font-weight: bold; color: #C09E3B; {RESET}")
            total_lbl = QLabel(f"\u20b1{line_total:,.2f}")
            total_lbl.setStyleSheet(f"font-weight: bold; {RESET}")

            b_layout.addWidget(name_lbl)
            b_layout.addStretch()
            b_layout.addWidget(qty_lbl)
            b_layout.addWidget(total_lbl)
            self.cart_layout.addWidget(box)

        self.total_label.setText(f"Total Amount: \u20b1{self.current_total:,.2f}")

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