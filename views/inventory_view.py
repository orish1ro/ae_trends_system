from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QGridLayout, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal
import base64

from PyQt6.QtGui import QColor, QFont, QPainter, QPixmap
from views.styled_dropdown import StyledComboBox

RESET = "background: transparent; border: none;"


class ProductCard(QFrame):
    edit_requested = pyqtSignal(dict)

    def __init__(self, product, parent=None):
        super().__init__(parent)
        warning = product["status"] in ("Low Stock", "Expiring Soon", "Expired")
        border = "#C94C4C" if warning else "#E1D7C7"
        hover_border = "#B33D35" if warning else "#C09E3B"
        self.setObjectName("productCard")
        self.setStyleSheet(f"""
            QFrame#productCard {{ background: #FFFDFB; border: 2px solid {border}; border-radius: 10px; }}
            QFrame#productCard:hover {{ background: #FFF9EE; border-color: {hover_border}; }}
        """)
        self.setMinimumSize(270, 350)
        self.setMaximumSize(270, 350)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        hero = QFrame()
        hero.setFixedHeight(136)
        hero.setObjectName("productHero")
        hero.setStyleSheet("QFrame#productHero { background: #F3E7D3; border: none; border-top-left-radius: 8px; border-top-right-radius: 8px; }")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(0, 0, 0, 0)
        hero_layout.addWidget(self._thumbnail(product, 136))
        layout.addWidget(hero)

        self.warning_badge = QLabel(self)
        self.warning_badge.setText(product["status"].upper())
        self.warning_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge_style = ("color: #A33F35; background: #FBE8E2; border: 1px solid #C94C4C;"
                       if warning else "color: #2F7A4A; background: #EAF6ED; border: 1px solid #A9D5B4;")
        self.warning_badge.setStyleSheet(f"{badge_style} border-radius: 10px; padding: 3px 8px; font-size: 9px; font-weight: bold;")
        self.warning_badge.adjustSize()
        self.warning_badge.raise_()

        content = QFrame()
        content.setObjectName("productContent")
        content.setStyleSheet("QFrame#productContent { background: transparent; border: none; }")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(14, 12, 14, 12)
        content_layout.setSpacing(7)

        name = QLabel(product["name"])
        name.setWordWrap(True)
        name.setStyleSheet(f"font-size: 14px; font-weight: bold; color: #20283A; {RESET}")
        content_layout.addWidget(name)
        meta = QLabel(f"SKU: {product['sku']}  •  {product['category']}")
        meta.setStyleSheet(f"font-size: 10px; color: #7C8798; {RESET}")
        content_layout.addWidget(meta)
        price = QLabel(f"₱{product['price']:,.2f}")
        price.setStyleSheet(f"font-size: 18px; font-weight: bold; color: #A9872E; {RESET}")
        content_layout.addWidget(price)

        metrics = QHBoxLayout()
        metrics.setSpacing(6)
        stock = QLabel(f"Stock: {product['stock_qty']} pcs")
        reorder = QLabel(f"Reorder: {product['reorder_level']} pcs")
        for metric in (stock, reorder):
            metric.setAlignment(Qt.AlignmentFlag.AlignCenter)
            metric.setStyleSheet("color: #5E554C; background: #F8F2E8; border: 1px solid #E5DCCA; border-radius: 5px; padding: 4px 3px; font-size: 10px;")
            metrics.addWidget(metric, 1)
        content_layout.addLayout(metrics)

        expiry = QLabel(f"Expiry: {product['expiration_date']}")
        expiry.setStyleSheet(f"font-size: 10px; color: #7C8798; {RESET}")
        content_layout.addWidget(expiry)

        if warning:
            warning_text = "Low Stock: Reorder needed" if product["status"] == "Low Stock" else product["status"]
            warning_label = QLabel(f"Warning: {warning_text}")
            warning_label.setStyleSheet("color: #A33F35; background: #FBE8E2; border: 1px solid #E9B8AE; border-radius: 5px; padding: 5px; font-size: 10px; font-weight: bold;")
            content_layout.addWidget(warning_label)
        else:
            content_layout.addSpacing(18)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 4, 0, 0)
        edit = QPushButton("Edit")
        edit.setCursor(Qt.CursorShape.PointingHandCursor)
        edit.setFixedHeight(30)
        edit.setStyleSheet("QPushButton { background: #C09E3B; color: white; border: none; border-radius: 6px; padding: 6px 12px; font-weight: bold; } QPushButton:hover { background: #A9872E; } QPushButton:pressed { background: #8F7225; }")
        edit.clicked.connect(lambda: self.edit_requested.emit(product))
        actions.addWidget(edit, 1)
        content_layout.addLayout(actions)
        layout.addWidget(content, 1)

    def resizeEvent(self, event):
        if hasattr(self, "warning_badge"):
            self.warning_badge.move(self.width() - self.warning_badge.width() - 12, 12)
        super().resizeEvent(event)

    @staticmethod
    def _thumbnail(product, size=80):
        image = QLabel()
        image.setFixedSize(270, size)
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_value = product.get("image_path", "")
        pixmap = QPixmap()
        if image_value.startswith("data:image/"):
            try:
                pixmap.loadFromData(base64.b64decode(image_value.split(",", 1)[1]))
            except (ValueError, IndexError):
                pixmap = QPixmap()
        elif image_value:
            pixmap = QPixmap(image_value)
        if pixmap.isNull():
            pixmap = QPixmap(270, size)
            pixmap.fill(QColor("#F3E7D3"))
            painter = QPainter(pixmap)
            painter.setPen(QColor("#8B6820"))
            painter.setFont(QFont("Arial", 18, QFont.Weight.Bold))
            initials = "".join(part[0] for part in product["name"].split()[:2]).upper()
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, initials)
            painter.end()
        image.setPixmap(pixmap.scaled(270, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
        image.setStyleSheet("background: #F3E7D3; border: none; border-top-left-radius: 8px; border-top-right-radius: 8px;")
        return image


class InventoryView(QWidget):
    edit_product_requested = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #F7F3EB;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 20)
        layout.setSpacing(14)

        top = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Inventory")
        title.setStyleSheet(f"font-size: 22px; font-weight: bold; color: #20283A; {RESET}")
        subtitle = QLabel("Manage products, stock thresholds, and shelf-life warnings.")
        subtitle.setStyleSheet(f"font-size: 11px; color: #667085; {RESET}")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        top.addLayout(title_box)
        top.addStretch()
        self.add_product_btn = QPushButton("+ Add New Product")
        self.add_product_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_product_btn.setStyleSheet("QPushButton { background: #C09E3B; color: white; font-weight: bold; padding: 8px 14px; border-radius: 5px; border: none; } QPushButton:hover { background: #A9872E; }")
        top.addWidget(self.add_product_btn)
        layout.addLayout(top)

        filters = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search product name or SKU...")
        self.search_input.setFixedHeight(34)
        self.search_input.setStyleSheet("QLineEdit { padding: 6px 10px; border: 1px solid #DCCFBC; border-radius: 7px; background: #FFFDFB; color: #344054; }")
        self.category_filter = StyledComboBox()
        self.category_filter.addItems(["Category: All", "Clothing", "Skincare"])
        self.category_filter.setFixedWidth(150)
        self.status_filter = StyledComboBox()
        self.status_filter.addItems(["Status: All Stock", "In Stock", "Low Stock", "Expiring Soon"])
        self.status_filter.setFixedWidth(180)
        filters.addWidget(self.search_input, 1)
        filters.addWidget(self.category_filter)
        filters.addWidget(self.status_filter)
        layout.addLayout(filters)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.grid_host = QWidget()
        self.grid = QGridLayout(self.grid_host)
        self.grid.setContentsMargins(2, 2, 2, 2)
        self.grid.setHorizontalSpacing(14)
        self.grid.setVerticalSpacing(14)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.scroll.setWidget(self.grid_host)
        layout.addWidget(self.scroll, 1)
        self._cards = []
        self._products = []
        self.empty_label = QLabel("No products found.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(f"color: #8A8074; font-size: 13px; {RESET}")
        layout.addWidget(self.empty_label)
        self.empty_label.hide()

    def display_products(self, products):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._products = list(products)
        self._cards = []
        for product in products:
            card = ProductCard(product)
            card.edit_requested.connect(self.edit_product_requested)
            self._cards.append(card)
        self._reflow_cards()
        self.empty_label.setVisible(not products)

    def resizeEvent(self, event):
        self._reflow_cards()
        super().resizeEvent(event)

    def _reflow_cards(self):
        if not hasattr(self, "grid"):
            return
        while self.grid.count():
            self.grid.takeAt(0)
        available_width = max(270, self.scroll.viewport().width() - 4)
        columns = max(1, min(4, available_width // 284))
        for index, card in enumerate(self._cards):
            self.grid.addWidget(card, index // columns, index % columns, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        for column in range(columns):
            self.grid.setColumnStretch(column, 0)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.grid.setRowStretch((len(self._cards) + columns - 1) // columns, 1)
