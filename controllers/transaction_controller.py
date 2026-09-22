from PyQt6.QtWidgets import QMessageBox

class TransactionController:
    def __init__(self, txn_model, inv_model, record_view, status_view):
        self.txn_model = txn_model
        self.inv_model = inv_model
        self.record_view = record_view
        self.status_view = status_view

        self.record_view.item_added_to_cart.connect(self.handle_add_to_cart)
        self.record_view.confirm_btn.clicked.connect(self.handle_confirm_transaction)
        
        self.status_view.filter_changed.connect(self.load_orders)
        self.status_view.search_input.textChanged.connect(self.load_orders)

    def load_catalog(self):
        products = self.inv_model.get_all_products()
        self.record_view.populate_catalog(products)

    def handle_add_to_cart(self, product):
        self.record_view.add_to_selected(product)

    def handle_confirm_transaction(self):
        cust_name = self.record_view.name_input.text().strip()
        cust_phone = self.record_view.phone_input.text().strip()
        address = self.record_view.address_input.text().strip()
        platform = self.record_view.platform_combo.currentText()
        order_type = platform
        cart = self.record_view.cart_items
        total = self.record_view.current_total

        if not cust_name:
            QMessageBox.warning(self.record_view, "Validation Error", "Customer name is required.")
            return

        if not cart:
            QMessageBox.warning(self.record_view, "Cart Empty", "Please add at least one product.")
            return

        payment = self.record_view.get_selected_payment()
        order_code = self.txn_model.create_order(cust_name, cust_phone, address, order_type, total, payment, cart)

        QMessageBox.information(self.record_view, "Success", f"Transaction saved successfully!\nOrder Code: {order_code}")
        self.record_view.clear_form()
        self.load_catalog()
        self.load_orders()

    def load_orders(self):
        current_tab = self.status_view.get_active_tab()
        search = self.status_view.search_input.text().strip()
        orders = self.txn_model.get_all_orders(current_tab, search)
        self.status_view.display_orders(orders)
