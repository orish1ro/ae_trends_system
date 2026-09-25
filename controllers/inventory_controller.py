import base64
import mimetypes
import os

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QPushButton, QMessageBox, QFileDialog, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from views.styled_dropdown import StyledComboBox

class InventoryController:
    def __init__(self, model, view, on_data_changed=None):
        self.model = model
        self.view = view

        self.on_data_changed = on_data_changed  # call after any write, so Dashboard/Reports/other
                                                 # pages that also depend on Product data stay in sync

        self.is_edit_modal_open = False
        self.selected_product = None

        
        self.view.search_input.textChanged.connect(self.load_products)
        self.view.category_filter.currentTextChanged.connect(self.load_products)
        self.view.status_filter.currentTextChanged.connect(self.load_products)
        self.view.add_product_btn.clicked.connect(self.open_add_product_dialog)
        self.view.edit_product_requested.connect(self.open_edit_product_dialog)

    def load_products(self):
        search = self.view.search_input.text().strip()
        category = self.view.category_filter.currentText()
        status = self.view.status_filter.currentText()
        products = self.model.get_all_products(search, category, status)
        self.view.display_products(products)

    def _notify_change(self):
        """Called after a write. Uses the app-wide refresh if one was
        provided (so Dashboard/Reports update too); otherwise just
        refreshes this page's own table."""
        if self.on_data_changed:
            self.on_data_changed()
        else:
            self.load_products()

    def open_add_product_dialog(self):
        self._open_product_dialog()

    def open_edit_product_dialog(self, product):
        self.handle_edit_product(product)

    def handle_edit_product(self, product):
        """Safe equivalent of React onClick={() => handleEditProduct(product)}."""
        if not product:
            return
        self.selected_product = dict(product)
        self._open_product_dialog(self.selected_product)

    def _open_product_dialog(self, product=None):
        product = dict(product or {})
        self.is_edit_modal_open = bool(product)
        dialog = QDialog(self.view)
        dialog.setWindowTitle("Edit Product" if product else "Add New Product")
        dialog.setFixedWidth(390)
        layout = QVBoxLayout(dialog)

        form = QFormLayout()
        name_in = QLineEdit(product.get("name", ""))
        cat_in = StyledComboBox()
        cat_in.addItems(["Clothing • Tops", "Clothing • Bottoms", "Clothing • Outerwear", "Skincare • Face", "Skincare • Treatment"])
        cat_in.setCurrentText(product.get("category", ""))
        price_in = QLineEdit(str(product.get("price", "")))
        stock_in = QLineEdit(str(product.get("stock_qty", "")))
        reorder_in = QLineEdit(str(product.get("reorder_level", 10)))
        exp_in = QLineEdit(product.get("expiration_date", ""))
        exp_in.setPlaceholderText("e.g. Dec 2026 or -")
        image_in = QLineEdit(product.get("image_path", ""))
        image_in.setReadOnly(True)
        image_preview = QLabel()
        image_preview.setFixedSize(120, 80)
        image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_preview.setStyleSheet("background: #F3E7D3; border: 1px solid #E5DCCA; border-radius: 7px; color: #8B6820;")
        image_btn = QPushButton("Choose Image")
        image_btn.clicked.connect(lambda: self._choose_image(image_in, image_preview, dialog))
        image_row = QHBoxLayout()
        image_row.addWidget(image_preview)
        image_row.addWidget(image_in)
        image_row.addWidget(image_btn)
        self._update_image_preview(image_preview, image_in.text(), name_in.text())
        name_in.textChanged.connect(lambda name: self._update_image_preview(image_preview, image_in.text(), name))

        form.addRow("Product Name:", name_in)
        form.addRow("Category:", cat_in)
        form.addRow("Price (₱):", price_in)
        form.addRow("Stock Qty:", stock_in)
        form.addRow("Reorder Level:", reorder_in)
        form.addRow("Expiration:", exp_in)
        form.addRow("Image:", image_row)

        save_btn = QPushButton("Save Product")
        save_btn.setStyleSheet("background-color: #C09E3B; color: white; padding: 8px; border-radius: 4px;")
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("QPushButton { background: #FFFDFB; color: #6D6257; border: 1px solid #D6CEBC; padding: 8px; border-radius: 4px; } QPushButton:hover { background: #F3E7D3; }")
        cancel_btn.clicked.connect(dialog.reject)
        actions = QHBoxLayout()
        actions.addWidget(cancel_btn)
        actions.addWidget(save_btn)

        def save():
            try:
                name = name_in.text().strip()
                cat = cat_in.currentText()
                price = float(price_in.text())
                stock = int(stock_in.text())
                reorder = int(reorder_in.text())
                exp = exp_in.text().strip() or "-"
                image_value = self._image_to_data_url(image_in.text().strip())
                if not name or price < 0 or stock < 0 or reorder < 0:
                    raise ValueError("Product name is required.")
                if product.get("id") is not None:
                    self.model.update_product(product["id"], name, product.get("sku", ""), cat, price, stock, reorder, exp, image_value)
                else:
                    self.model.add_product(name, cat, price, stock, reorder, exp, image_path=image_value)
                dialog.accept()
                self._notify_change()
            except ValueError as e:
                QMessageBox.warning(dialog, "Input Error", f"Please enter valid product values. {e}")
            except Exception as error:
                QMessageBox.critical(dialog, "Save Failed", f"Unable to save product: {error}")

        save_btn.clicked.connect(save)
        layout.addLayout(form)
        layout.addLayout(actions)
        dialog.exec()
        self.is_edit_modal_open = False
        self.selected_product = None

    @staticmethod
    def _image_to_data_url(path):
        if not path:
            return ""
        if path.startswith("data:image/"):
            return path
        if not os.path.isfile(path):
            return path
        mime_type = mimetypes.guess_type(path)[0] or "image/png"
        with open(path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    @staticmethod
    def _update_image_preview(preview, image_value, product_name):
        try:
            if image_value.startswith("data:image/"):
                encoded = image_value.split(",", 1)[1]
                pixmap = QPixmap()
                pixmap.loadFromData(base64.b64decode(encoded))
            else:
                pixmap = QPixmap(image_value) if image_value else QPixmap()
            if not pixmap.isNull():
                preview.setPixmap(pixmap.scaled(116, 76, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                return
        except (ValueError, OSError):
            pass
        preview.setText((product_name[:1] or "?").upper())

    @staticmethod
    def _choose_image(field, preview, parent):
        path, _ = QFileDialog.getOpenFileName(parent, "Choose Product Image", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            data_url = InventoryController._image_to_data_url(path)
            field.setText(data_url)
            InventoryController._update_image_preview(preview, data_url, "Product")

    def archive_product(self, product):
        answer = QMessageBox.question(
            self.view, "Archive Product", f"Archive {product['name']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            try:
                self.model.archive_product(product["id"])
                self.load_products()
            except Exception as error:
                QMessageBox.critical(self.view, "Archive Failed", str(error))
