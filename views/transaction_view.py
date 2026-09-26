import base64

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QFrame, QRadioButton, QScrollArea, QButtonGroup,
                             QFileDialog, QDialog, QMessageBox)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPainter, QPixmap
from views.styled_dropdown import StyledComboBox

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
FIELD_STYLE = "padding: 8px 10px; font-size: 12px; border: 1px solid #D6CEBC; border-radius: 6px; background: #FFFDFB; color: #2A2421;"
ERROR_FIELD_STYLE = "padding: 8px 10px; font-size: 12px; border: 1.5px solid #C94C4C; border-radius: 6px; background: #FDF1EF; color: #2A2421;"


PlatformComboBox = StyledComboBox


class CatalogRow(QFrame):
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class QuantitySelector(QFrame):
    """Compact, theme-styled quantity control shared by catalog rows."""

    value_changed = pyqtSignal(int)

    def __init__(self, value=0, maximum=999, parent=None):
        super().__init__(parent)
        self.maximum = maximum
        self.setFixedSize(86, 28)
        self.setObjectName("quantitySelector")
        self.setStyleSheet("""
            QFrame#quantitySelector {
                background: #FFFDF8;
                border: 1px solid #D6CEBC;
                border-radius: 7px;
            }
            QFrame#quantitySelector QPushButton {
                background: transparent;
                color: #6D6257;
                border: none;
                font-size: 14px;
                font-weight: bold;
                padding: 0;
            }
            QFrame#quantitySelector QPushButton:hover { background: #F3E7D3; color: #6D5A27; }
            QFrame#quantitySelector QPushButton:pressed { background: #EADCB9; }
            QFrame#quantitySelector QLineEdit {
                background: transparent;
                color: #2A2421;
                border: none;
                padding: 0;
                font-size: 12px;
                selection-background-color: #FFF2C8;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 1, 2, 1)
        layout.setSpacing(0)
        self.minus_button = QPushButton("-")
        self.plus_button = QPushButton("+")
        self.value_input = QLineEdit()
        self.minus_button.setFixedSize(24, 24)
        self.plus_button.setFixedSize(24, 24)
        self.value_input.setFixedSize(32, 24)
        self.value_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_input.setText(str(value))
        self.value_input.editingFinished.connect(self._commit_input)
        self.minus_button.clicked.connect(lambda: self.set_value(self.value - 1))
        self.plus_button.clicked.connect(lambda: self.set_value(self.value + 1))
        layout.addWidget(self.minus_button)
        layout.addWidget(self.value_input)
        layout.addWidget(self.plus_button)

    @property
    def value(self):
        try:
            return int(self.value_input.text())
        except ValueError:
            return 0

    def _commit_input(self):
        self.set_value(self.value)

    def set_value(self, value):
        value = max(0, min(self.maximum, int(value)))
        self.value_input.setText(str(value))
        self.minus_button.setEnabled(value > 0)
        self.plus_button.setEnabled(value < self.maximum)
        self.value_changed.emit(value)


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
        self.walk_in_cart = []
        self.online_cart = []
        self._mode_forms = {
            "walkin": self._empty_form_state(),
            "online": self._empty_form_state(),
        }
        self._catalog_products = []
        self._filtered_catalog_products = []
        self._catalog_page = 1
        self._catalog_page_size = 5
        self.current_total = 0.0
        self._active_transaction_mode = "walkin"

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
        self.online_tab.toggled.connect(self._handle_transaction_mode_change)
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
        self.name_input.setStyleSheet(FIELD_STYLE)
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("e.g. 09171234567")
        self.phone_input.setStyleSheet(FIELD_STYLE)

        name_phone_row = QHBoxLayout()
        name_phone_row.setSpacing(16)
        name_phone_row.addLayout(field_group("Customer Name", self.name_input), 1)
        name_phone_row.addLayout(field_group("Contact Number", self.phone_input), 1)
        cust_layout.addLayout(name_phone_row)
        self.name_input.textChanged.connect(lambda: self.name_input.setStyleSheet(FIELD_STYLE))
        self.phone_input.textChanged.connect(lambda: self.phone_input.setStyleSheet(FIELD_STYLE))

        self.platform_combo = PlatformComboBox()
        self.platform_combo.addItems(["Shopee", "TikTok Shop", "Lazada", "FB/IG", "Direct"])
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Delivery address for online orders...")
        self.address_input.setStyleSheet(FIELD_STYLE)
        self.address_group = field_group("Delivery Address", self.address_input)
        self.name_label = name_phone_row.itemAt(0).layout().itemAt(0).widget()
        self.phone_label = name_phone_row.itemAt(1).layout().itemAt(0).widget()
        self._address_group_widgets = [self.address_group.itemAt(i).widget() for i in range(self.address_group.count())]
        self.address_label = self.address_group.itemAt(0).widget()
        self.platform_group = field_group("Platform", self.platform_combo)
        self._platform_group_widgets = [self.platform_group.itemAt(i).widget() for i in range(self.platform_group.count())]
        self.platform_label = self.platform_group.itemAt(0).widget()
        online_details_row = QHBoxLayout()
        online_details_row.setSpacing(16)
        online_details_row.addLayout(self.address_group, 1)
        online_details_row.addLayout(self.platform_group, 1)
        cust_layout.addLayout(online_details_row)
        self.address_input.textChanged.connect(lambda: self.address_input.setStyleSheet(FIELD_STYLE))
        self._toggle_delivery_address(False)  # hidden by default - Walk-in is checked first

        self.form_error = QLabel()
        self.form_error.setWordWrap(True)
        self.form_error.setVisible(False)
        self.form_error.setStyleSheet("color: #A33F35; background: #FBE8E2; border: 1px solid #E9B8AE; border-radius: 5px; padding: 7px 9px; font-size: 11px;")
        cust_layout.addWidget(self.form_error)

        left_col.addWidget(cust_box)

        # ---- Product Catalog ----
        catalog_toolbar = QHBoxLayout()
        cat_title = QLabel("Product Catalog")
        cat_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: #2A2421; {RESET}")
        self.catalog_count = QLabel("0 products")
        self.catalog_count.setStyleSheet(f"font-size: 11px; color: #8A8074; {RESET}")
        catalog_toolbar.addWidget(cat_title)
        catalog_toolbar.addStretch()
        self.refresh_catalog_btn = QPushButton("Refresh")
        self.refresh_catalog_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_catalog_btn.setFixedHeight(28)
        self.refresh_catalog_btn.setStyleSheet("QPushButton { background: #F6EEDC; color: #6D5A27; border: 1px solid #D6CEBC; border-radius: 5px; padding: 4px 10px; font-size: 11px; } QPushButton:hover { background: #EADCB9; }")
        catalog_toolbar.addWidget(self.refresh_catalog_btn)
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
        self.search_input.textChanged.connect(lambda text: self._apply_catalog_filters(reset_page=True))
        QTimer.singleShot(0, self.search_input.setFocus)
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

        pagination = QHBoxLayout()
        pagination.setContentsMargins(8, 6, 8, 2)
        self.previous_page_btn = QPushButton("Previous")
        self.next_page_btn = QPushButton("Next")
        self.catalog_page_label = QLabel("Page 1 of 1")
        self.catalog_page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.catalog_page_label.setStyleSheet(f"font-size: 11px; color: #7C8798; {RESET}")
        for button in (self.previous_page_btn, self.next_page_btn):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setStyleSheet("QPushButton { background: #FFFDF8; color: #6D6257; border: 1px solid #E5DCCA; border-radius: 5px; padding: 5px 10px; } QPushButton:hover:enabled { background: #F3E7D3; } QPushButton:disabled { color: #B8AEA2; background: #F6F1E8; }")
        self.previous_page_btn.clicked.connect(lambda: self._change_catalog_page(-1))
        self.next_page_btn.clicked.connect(lambda: self._change_catalog_page(1))
        pagination.addWidget(self.previous_page_btn)
        pagination.addStretch()
        pagination.addWidget(self.catalog_page_label)
        pagination.addStretch()
        pagination.addWidget(self.next_page_btn)
        catalog_card_layout.addLayout(pagination)
        left_col.addWidget(catalog_card, stretch=1)

        main_layout.addLayout(left_col, 60)

        # ================= RIGHT COLUMN =================
        right_box = QFrame()
        right_box.setObjectName("cartCard")
        right_box.setStyleSheet(f"QFrame#cartCard {{ {CARD_STYLE} }}")
        right_layout = QVBoxLayout(right_box)
        right_layout.setContentsMargins(22, 20, 22, 20)
        right_layout.setSpacing(16)  # matches left_col's 16px rhythm for a consistent feel

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
        self.cart_layout.addStretch(1)
        self.cart_layout.addWidget(self.empty_cart_label)
        self.cart_layout.addStretch(1)

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

        divider1 = QFrame()
        divider1.setFixedHeight(1)
        divider1.setStyleSheet("background-color: #EFE9DD; border: none;")
        right_layout.addWidget(divider1)

        pay_title = QLabel("Payment Method")
        pay_title.setStyleSheet(f"font-weight: 600; color: #2A2421; {RESET}")
        right_layout.addWidget(pay_title)

        payment_row = QHBoxLayout()
        payment_row.setSpacing(8)
        self.pay_cash = QRadioButton("Cash")
        self.pay_gcash = QRadioButton("GCash")
        self.pay_bank = QRadioButton("Online Banking")
        for rb in (self.pay_cash, self.pay_gcash, self.pay_bank):
            rb.setMinimumHeight(34)
            rb.setStyleSheet("""
                QRadioButton {
                    background: #FFFDFB;
                    color: #6D6257;
                    border: 1px solid #E6DCCB;
                    border-radius: 6px;
                    padding: 0 12px;
                }
                QRadioButton::indicator { width: 0; height: 0; }
                QRadioButton:checked {
                    background: #FFF5D4;
                    color: #8B6820;
                    border: 1px solid #D5AA27;
                    font-weight: bold;
                }
            """)
            payment_row.addWidget(rb, stretch=1)
        self.pay_gcash.setChecked(True)
        right_layout.addLayout(payment_row)

        self.payment_details = QFrame()
        self.payment_details.setStyleSheet(f"background: #FBF7EF; border: 1px solid #E8DFD0; border-radius: 7px; {RESET}")
        payment_layout = QVBoxLayout(self.payment_details)
        payment_layout.setContentsMargins(10, 8, 10, 8)
        payment_layout.setSpacing(5)
        self.payment_label = QLabel()
        self.payment_label.setStyleSheet(f"font-size: 11px; font-weight: 600; color: #6F6255; {RESET}")
        payment_layout.addWidget(self.payment_label)
        self.amount_paid_input = QLineEdit()
        self.amount_paid_input.setPlaceholderText("0.00")
        self.amount_paid_input.setStyleSheet(FIELD_STYLE)
        self.amount_paid_input.textChanged.connect(self._update_change)
        self.amount_paid_input.textChanged.connect(lambda: self.amount_paid_input.setStyleSheet(FIELD_STYLE))
        self.change_label = QLabel("Change: ₱0.00")
        self.change_label.setStyleSheet(f"font-size: 12px; font-weight: bold; color: #6D9F71; {RESET}")
        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText("Enter reference number")
        self.reference_input.setStyleSheet(FIELD_STYLE)
        self.reference_input.textChanged.connect(lambda: self.reference_input.setStyleSheet(FIELD_STYLE))
        payment_layout.addWidget(self.amount_paid_input)
        payment_layout.addWidget(self.change_label)
        payment_layout.addWidget(self.reference_input)
        right_layout.addWidget(self.payment_details)
        self.pay_cash.toggled.connect(self._update_payment_fields)
        self.pay_gcash.toggled.connect(self._update_payment_fields)
        self.pay_bank.toggled.connect(self._update_payment_fields)

        self.receipt_title = QLabel("Upload Receipt Image")
        self.receipt_title.setStyleSheet(f"font-size: 12px; font-weight: 600; color: #20283A; margin-top: 6px; {RESET}")
        right_layout.addWidget(self.receipt_title)

        self.receipt_box = QFrame()
        self.receipt_box.setObjectName("receiptBox")
        self.receipt_box.setMinimumHeight(62)
        self.receipt_box.setStyleSheet("""
            QFrame#receiptBox {
                background: #FFF8DD;
                border: 1px dashed #D5AA27;
                border-radius: 7px;
            }
        """)
        receipt_layout = QHBoxLayout(self.receipt_box)
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
        right_layout.addWidget(self.receipt_box)
        self._update_payment_fields()

        divider2 = QFrame()
        divider2.setFixedHeight(1)
        divider2.setStyleSheet("background-color: #EFE9DD; border: none; margin-top: 4px;")
        right_layout.addWidget(divider2)

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

    def _update_payment_fields(self):
        is_cash = self.pay_cash.isChecked()
        is_walkin = self.walkin_tab.isChecked()
        show_reference = not is_cash and not is_walkin
        self.payment_label.setText("Amount Paid" if is_cash else "Reference Number")
        self.amount_paid_input.setVisible(is_cash)
        self.change_label.setVisible(is_cash)
        self.reference_input.setVisible(show_reference)
        self.payment_label.setVisible(is_cash or show_reference)
        self.payment_details.setVisible(is_cash or show_reference)
        self.receipt_title.setVisible(is_walkin or not is_cash)
        self.receipt_box.setVisible(is_walkin or not is_cash)
        self._update_change()

    def _update_change(self):
        if not self.pay_cash.isChecked():
            return
        try:
            amount_paid = float(self.amount_paid_input.text() or 0)
        except ValueError:
            amount_paid = 0
        change = max(0, amount_paid - self.current_total)
        self.change_label.setText(f"Change: ₱{change:,.2f}")

    def get_payment_details(self):
        if self.pay_cash.isChecked():
            try:
                amount_paid = float(self.amount_paid_input.text() or 0)
            except ValueError:
                amount_paid = 0
            return {
                "method": "Cash",
                "amount_paid": amount_paid,
                "reference_number": "",
                "receipt_image": "",
            }
        return {
            "method": self.get_selected_payment(),
            "amount_paid": self.current_total,
            "reference_number": self.reference_input.text().strip(),
            "receipt_image": self.receipt_status.text() if self.receipt_status.text() != "No receipt uploaded" else "",
        }

    def _toggle_delivery_address(self, online_checked):
        required_suffix = " <span style='color:#C94C4C;'>*</span>"
        optional_suffix = "  <span style='color:#9A9184; font-weight:400;'>(Optional)</span>"
        self.name_label.setText("Customer Name" + (required_suffix if online_checked else optional_suffix))
        self.phone_label.setText("Contact Number" + (required_suffix if online_checked else optional_suffix))
        self.address_label.setText("Delivery Address" + required_suffix)
        self.platform_label.setText("Platform" + required_suffix)
        for w in self._address_group_widgets:
            w.setVisible(online_checked)
        for w in self._platform_group_widgets:
            w.setVisible(online_checked)
        if not online_checked:
            self.platform_combo.setCurrentIndex(0)
        if hasattr(self, "payment_details"):
            self._update_payment_fields()
        self._clear_field_errors()

    @staticmethod
    def _empty_form_state():
        return {
            "name": "",
            "phone": "",
            "address": "",
            "platform_index": 0,
            "payment": "GCash",
            "amount_paid": "",
            "reference": "",
            "receipt": "No receipt uploaded",
        }

    @property
    def cart_items(self):
        return self.walk_in_cart if self._active_transaction_mode == "walkin" else self.online_cart

    @cart_items.setter
    def cart_items(self, items):
        if self._active_transaction_mode == "walkin":
            self.walk_in_cart = items
        else:
            self.online_cart = items

    def _save_mode_form_state(self):
        self._mode_forms[self._active_transaction_mode] = {
            "name": self.name_input.text(),
            "phone": self.phone_input.text(),
            "address": self.address_input.text(),
            "platform_index": self.platform_combo.currentIndex(),
            "payment": self.get_selected_payment(),
            "amount_paid": self.amount_paid_input.text(),
            "reference": self.reference_input.text(),
            "receipt": self.receipt_status.text(),
        }

    def _load_mode_form_state(self):
        state = self._mode_forms[self._active_transaction_mode]
        self.name_input.setText(state["name"])
        self.phone_input.setText(state["phone"])
        self.address_input.setText(state["address"])
        self.platform_combo.setCurrentIndex(state["platform_index"])
        payment_buttons = {
            "Cash": self.pay_cash,
            "GCash": self.pay_gcash,
            "Online Banking": self.pay_bank,
        }
        payment_buttons.get(state["payment"], self.pay_gcash).setChecked(True)
        self.amount_paid_input.setText(state["amount_paid"])
        self.reference_input.setText(state["reference"])
        self.receipt_status.setText(state["receipt"])

    def _handle_transaction_mode_change(self, online_checked):
        next_mode = "online" if online_checked else "walkin"
        if next_mode != self._active_transaction_mode:
            self._save_mode_form_state()
            self._active_transaction_mode = next_mode
            self._load_mode_form_state()
        self._toggle_delivery_address(online_checked)
        self.refresh_cart_ui()
        self._apply_catalog_filters()

    def _reset_active_mode_state(self):
        self.cart_items = []
        self.name_input.clear()
        self.phone_input.clear()
        self.address_input.clear()
        self.platform_combo.setCurrentIndex(0)
        self.pay_gcash.setChecked(True)
        self.amount_paid_input.clear()
        self.reference_input.clear()
        self.receipt_status.setText("No receipt uploaded")
        self.form_error.clear()
        self.form_error.setVisible(False)
        self._clear_field_errors()
        self.refresh_cart_ui()
        self._apply_catalog_filters()

    def _set_catalog_filter(self, category):
        for name, button in self.catalog_filter_buttons.items():
            button.setChecked(name == category)
        self._apply_catalog_filters(reset_page=True)

    def _apply_catalog_filters(self, reset_page=False):
        if reset_page:
            self._catalog_page = 1
        category = next(
            (name for name, button in self.catalog_filter_buttons.items() if button.isChecked()),
            "All",
        )
        query = self.search_input.text().strip().lower()
        self._filtered_catalog_products = [
            product for product in self._catalog_products
            if (category == "All" or category.lower() in product['category'].lower())
            and (not query or query in product['name'].lower() or query in str(product['id']))
        ]
        self._render_catalog()

    def populate_catalog(self, products):
        """Filters out any product record missing a field the catalog needs
        to render, instead of letting one bad row (e.g. a product added
        without a price) crash the entire Record Transaction page."""
        required_fields = ("id", "name", "category", "price", "stock_qty")
        valid_products = []
        skipped = 0
        for product in products or []:
            try:
                if all(field in product for field in required_fields):
                    valid_products.append(product)
                else:
                    skipped += 1
            except TypeError:
                skipped += 1  # product wasn't even dict-like

        self._catalog_products = valid_products
        count_text = f"{len(valid_products)} products"
        if skipped:
            count_text += f" ({skipped} hidden - missing data)"
        self.catalog_count.setText(count_text)
        self._catalog_page = 1
        self._apply_catalog_filters()

    def _change_catalog_page(self, direction):
        page_count = max(1, (len(self._filtered_catalog_products) + self._catalog_page_size - 1) // self._catalog_page_size)
        self._catalog_page = max(1, min(page_count, self._catalog_page + direction))
        self._render_catalog()

    def _product_thumbnail(self, product, size=38):
        thumbnail = QLabel()
        thumbnail.setFixedSize(size, size)
        thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_path = product.get("image_path", "")
        pixmap = QPixmap()
        if image_path.startswith("data:image/"):
            try:
                pixmap.loadFromData(base64.b64decode(image_path.split(",", 1)[1]))
            except (ValueError, IndexError):
                pixmap = QPixmap()
        elif image_path:
            pixmap = QPixmap(image_path)
        if pixmap.isNull():
            pixmap = QPixmap(size, size)
            pixmap.fill(QColor("#F3E7D3"))
            painter = QPainter(pixmap)
            painter.setPen(QColor("#8B6820"))
            painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            initials = "".join(part[0] for part in product["name"].split()[:2]).upper()
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, initials)
            painter.end()
        thumbnail.setPixmap(pixmap.scaled(size - 2, size - 2, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        thumbnail.setStyleSheet("background: #F3E7D3; border: 1px solid #E5DCCA; border-radius: 5px;")
        return thumbnail

    def _render_catalog(self):
        page_count = max(1, (len(self._filtered_catalog_products) + self._catalog_page_size - 1) // self._catalog_page_size)
        self._catalog_page = min(self._catalog_page, page_count)
        start = (self._catalog_page - 1) * self._catalog_page_size
        products = self._filtered_catalog_products[start:start + self._catalog_page_size]
        self.catalog_page_label.setText(f"Page {self._catalog_page} of {page_count}")
        self.previous_page_btn.setEnabled(self._catalog_page > 1)
        self.next_page_btn.setEnabled(self._catalog_page < page_count)
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
                label.setFixedWidth(86)
                header_layout.addWidget(label)
            else:
                label.setFixedWidth(70 if text != "ACTION" else 58)
                header_layout.addWidget(label)
        self.catalog_layout.addWidget(headers)

        rendered = 0
        for prod in products:
            try:
                row = self._build_catalog_row(prod, rendered)
            except (KeyError, TypeError, ValueError):
                continue  # skip this one row rather than crash the whole catalog
            self.catalog_layout.addWidget(row)
            rendered += 1

        self.catalog_layout.addStretch(1)

    def _build_catalog_row(self, prod, index):
        """Builds one catalog row widget. Raising here (missing/bad field)
        is caught by _render_catalog, which just skips that product."""
        row = CatalogRow()
        row.setObjectName("catalogRow")
        row.setFixedHeight(58)
        row.setStyleSheet(f"""
            QFrame#catalogRow {{
                background: {'#FFFDF8' if index % 2 == 0 else '#F5EFE4'};
                border-bottom: 1px solid #E8DFD0;
            }}
            QFrame#catalogRow:hover {{ background: #EFE3C9; }}
        """)
        r_layout = QHBoxLayout(row)
        r_layout.setContentsMargins(14, 6, 14, 6)

        r_layout.addWidget(self._product_thumbnail(prod))
        info = QLabel(f"<b>{prod['name']}</b><br><span style='color:#8A8074;'>{prod['category']}</span>")
        info.setStyleSheet(RESET)

        price = QLabel(f"\u20b1{prod['price']:,.2f}")
        price.setFixedWidth(70)
        price.setStyleSheet(f"font-weight: bold; font-size: 12px; color: #2A2421; {RESET}")

        stock = QLabel(f"{prod['stock_qty']} pcs")
        stock.setFixedWidth(70)
        stock.setStyleSheet(f"color: {'#C94C4C' if prod['stock_qty'] <= 10 else '#766B60'}; {RESET}")

        quantity_box = QuantitySelector(
            value=self._cart_quantity(prod['id']),
            maximum=max(0, prod.get('stock_qty', 0)),
        )
        quantity_box.value_changed.connect(
            lambda value, product_id=prod['id'], product=prod: self._set_catalog_quantity(product_id, value, product)
        )

        add_btn = QPushButton("Add")
        add_btn.setFixedWidth(58)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(
            "background: #C09E3B; color: white; padding: 6px 8px; border-radius: 4px; border: none;"
        )
        add_btn.clicked.connect(lambda ch, p=prod: self.item_added_to_cart.emit(p))
        row.clicked.connect(lambda p=prod: self.item_added_to_cart.emit(p))

        r_layout.addWidget(info)
        r_layout.addWidget(stock)
        r_layout.addWidget(price)
        r_layout.addWidget(quantity_box)
        r_layout.addWidget(add_btn)
        return row

    def _cart_quantity(self, product_id):
        return next((item['qty'] for item in self.cart_items if item['id'] == product_id), 0)

    def _set_catalog_quantity(self, product_id, quantity, product):
        current = self._cart_quantity(product_id)
        if quantity > current:
            for _ in range(quantity - current):
                self.add_to_selected(product)
        elif quantity < current:
            for _ in range(current - quantity):
                self.remove_from_selected(product_id)

    def add_to_selected(self, product):
        try:
            product_id = product['id']
            product_name = product['name']
            product_price = float(product['price'])
        except (KeyError, TypeError, ValueError):
            self.show_form_error("This product is missing required data and can't be added.")
            return

        stock_qty = product.get("stock_qty", 0)
        if stock_qty <= 0:
            self.show_form_error("This product is out of stock.")
            return

        for item in self.cart_items:
            if item['id'] == product_id:
                if item['qty'] >= stock_qty:
                    self.show_form_error("Quantity cannot exceed available stock.")
                    return
                item['qty'] += 1
                self.refresh_cart_ui()
                self._apply_catalog_filters()
                return

        self.cart_items.append({
            'id': product_id,
            'name': product_name,
            'price': product_price,
            'stock_qty': stock_qty,
            'image_path': product.get('image_path', ''),
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
        # Clean out the old items and spaces
        while self.cart_layout.count():
            item = self.cart_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.current_total = 0.0

        # If cart is empty, show the empty label centered
        if not self.cart_items:
            empty = QLabel("No items selected yet.")
            empty.setStyleSheet(f"color: #A39B90; font-size: 12px; {RESET}")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cart_layout.addStretch(1)
            self.cart_layout.addWidget(empty)
            self.cart_layout.addStretch(1)

        # Build the text-only cart items
        for item in self.cart_items:
            line_total = item['price'] * item['qty']
            self.current_total += line_total

            box = QFrame()
            box.setStyleSheet("QFrame { background: transparent; border-bottom: 1px solid #E8E0D4; }")
            b_layout = QHBoxLayout(box)
            b_layout.setContentsMargins(0, 9, 0, 9)
            b_layout.setSpacing(10)

            # Left column: Name and Price
            left_col = QVBoxLayout()
            left_col.setSpacing(3)
            name_lbl = QLabel(item['name'])
            name_lbl.setStyleSheet(f"font-size: 12px; font-weight: bold; color: #20283A; {RESET}")
            price_lbl = QLabel(f"\u20b1{item['price']:,.2f} each")
            price_lbl.setStyleSheet(f"font-size: 11px; color: #7C8798; {RESET}")
            left_col.addWidget(name_lbl)
            left_col.addWidget(price_lbl)

            # Right column: Quantity and Total
            right_col = QVBoxLayout()
            right_col.setSpacing(3)
            quantity_label = QLabel(f"x{item['qty']}")
            quantity_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            quantity_label.setStyleSheet(f"font-size: 11px; font-weight: bold; color: #A9872E; {RESET}")
            total_label = QLabel(f"\u20b1{line_total:,.2f}")
            total_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            total_label.setStyleSheet(f"font-size: 12px; font-weight: bold; color: #20283A; {RESET}")
            right_col.addWidget(quantity_label)
            right_col.addWidget(total_label)

            b_layout.addLayout(left_col, stretch=1)
            b_layout.addLayout(right_col)
            
            self.cart_layout.addWidget(box)

        # FIX: Add a stretch at the very bottom so the items pack tightly at the top
        if self.cart_items:
            self.cart_layout.addStretch(1)

        # Update summaries
        product_count = len(self.cart_items)
        unit_count = sum(item['qty'] for item in self.cart_items)
        self.cart_summary.setText(f"{product_count} products \u2022 {unit_count} units")
        self.cart_count_badge.setText(str(product_count))
        self.total_label.setText(f"\u20b1{self.current_total:,.2f}")
        self._update_change()

    def get_selected_payment(self):
        if self.pay_cash.isChecked():
            return "Cash"
        elif self.pay_gcash.isChecked():
            return "GCash"
        return "Online Banking"

    def _clear_field_errors(self):
        field_names = ("name_input", "phone_input", "address_input",
                       "reference_input", "amount_paid_input")
        for field_name in field_names:
            widget = getattr(self, field_name, None)
            if widget is not None:
                widget.setStyleSheet(FIELD_STYLE)

    def _highlight_required_fields(self):
        """Called whenever a validation error is shown. Figures out which
        fields are the likely cause, using the same rules the controller
        checks, and puts a red border on just those - so the person sees
        exactly what to fix, not just a banner at the top."""
        self._clear_field_errors()
        is_online = self.online_tab.isChecked()

        if is_online and not self.name_input.text().strip():
            self.name_input.setStyleSheet(ERROR_FIELD_STYLE)
        if is_online and not self.phone_input.text().strip():
            self.phone_input.setStyleSheet(ERROR_FIELD_STYLE)
        if is_online and not self.address_input.text().strip():
            self.address_input.setStyleSheet(ERROR_FIELD_STYLE)

        if self.pay_cash.isChecked():
            try:
                amount_paid = float(self.amount_paid_input.text() or 0)
            except ValueError:
                amount_paid = -1  # force the highlight on unparseable input too
            if amount_paid < self.current_total:
                self.amount_paid_input.setStyleSheet(ERROR_FIELD_STYLE)
        elif is_online and not self.reference_input.text().strip():
            self.reference_input.setStyleSheet(ERROR_FIELD_STYLE)

    def show_form_error(self, message):
        self.form_error.setStyleSheet("color: #A33F35; background: #FBE8E2; border: 1px solid #E9B8AE; border-radius: 5px; padding: 7px 9px; font-size: 11px;")
        self.form_error.setText(message)
        self.form_error.setVisible(True)
        self._highlight_required_fields()

    def show_form_success(self, message):
        self.form_error.setStyleSheet("color: #2F7A4A; background: #EAF6ED; border: 1px solid #A9D5B4; border-radius: 5px; padding: 7px 9px; font-size: 11px;")
        self.form_error.setText(message)
        self.form_error.setVisible(True)
        self._clear_field_errors()

    def show_transaction_success(self, order_code):
        dialog = QDialog(self)
        dialog.setWindowTitle("Transaction Complete")
        dialog.setFixedWidth(390)
        dialog.setStyleSheet("QDialog { background: #FFFDFB; color: #2A2421; }")
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(10)

        title = QLabel("Transaction saved successfully")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: #6D9F71; {RESET}")
        detail = QLabel(f"Order Code: {order_code}\nTotal: ₱{self.current_total:,.2f}")
        detail.setStyleSheet(f"font-size: 13px; color: #2A2421; {RESET}")
        layout.addWidget(title)
        layout.addWidget(detail)

        actions = QHBoxLayout()
        print_btn = QPushButton("Print Thermal Receipt")
        print_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        print_btn.setStyleSheet("QPushButton { background: #F6EEDC; color: #6D5A27; border: 1px solid #D6CEBC; border-radius: 6px; padding: 9px 10px; font-weight: bold; } QPushButton:hover { background: #EADCB9; }")
        new_sale_btn = QPushButton("Start New Sale")
        new_sale_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_sale_btn.setStyleSheet("QPushButton { background: #C09E3B; color: white; border: none; border-radius: 6px; padding: 9px 10px; font-weight: bold; } QPushButton:hover { background: #A9872E; }")
        print_btn.clicked.connect(lambda: self._print_thermal_receipt(dialog, order_code))
        new_sale_btn.clicked.connect(dialog.accept)
        actions.addWidget(print_btn)
        actions.addWidget(new_sale_btn)
        layout.addLayout(actions)
        dialog.exec()

    @staticmethod
    def _print_thermal_receipt(parent, order_code):
        QMessageBox.information(parent, "Receipt", f"Thermal receipt prepared for {order_code}.")

    def clear_form(self):
        self._mode_forms[self._active_transaction_mode] = self._empty_form_state()
        self._reset_active_mode_state()
        QTimer.singleShot(0, self.search_input.setFocus)