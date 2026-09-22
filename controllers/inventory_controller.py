from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QPushButton, QMessageBox

class InventoryController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        
        self.view.search_input.textChanged.connect(self.load_products)
        self.view.category_filter.currentTextChanged.connect(self.load_products)
        self.view.status_filter.currentTextChanged.connect(self.load_products)
        self.view.add_product_btn.clicked.connect(self.open_add_product_dialog)

    def load_products(self):
        search = self.view.search_input.text().strip()
        category = self.view.category_filter.currentText()
        status = self.view.status_filter.currentText()
        products = self.model.get_all_products(search, category, status)
        self.view.display_products(products)

    def open_add_product_dialog(self):
        dialog = QDialog(self.view)
        dialog.setWindowTitle("Add New Product")
        dialog.setFixedWidth(350)
        layout = QVBoxLayout(dialog)

        form = QFormLayout()
        name_in = QLineEdit()
        cat_in = QComboBox()
        cat_in.addItems(["Clothing • Tops", "Clothing • Bottoms", "Clothing • Outerwear", "Skincare • Face", "Skincare • Treatment"])
        price_in = QLineEdit()
        stock_in = QLineEdit()
        exp_in = QLineEdit()
        exp_in.setPlaceholderText("e.g. Dec 2026 or -")

        form.addRow("Product Name:", name_in)
        form.addRow("Category:", cat_in)
        form.addRow("Price (₱):", price_in)
        form.addRow("Stock Qty:", stock_in)
        form.addRow("Expiration:", exp_in)

        save_btn = QPushButton("Save Product")
        save_btn.setStyleSheet("background-color: #C09E3B; color: white; padding: 8px; border-radius: 4px;")
        
        def save():
            try:
                name = name_in.text().strip()
                cat = cat_in.currentText()
                price = float(price_in.text())
                stock = int(stock_in.text())
                exp = exp_in.text().strip() or "-"
                if not name:
                    raise ValueError("Product name is required.")
                self.model.add_product(name, cat, price, stock, 10, exp)
                dialog.accept()
                self.load_products()
            except ValueError as e:
                QMessageBox.warning(dialog, "Input Error", str(e))

        save_btn.clicked.connect(save)
        layout.addLayout(form)
        layout.addWidget(save_btn)
        dialog.exec()
