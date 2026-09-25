from PyQt6.QtWidgets import QMessageBox
from views.order_status_view import OrderDetailDialog

class TransactionController:
    def __init__(self, txn_model, inv_model, record_view, status_view, on_order_saved=None):
        self.txn_model = txn_model
        self.inv_model = inv_model
        self.record_view = record_view
        self.status_view = status_view
        self.on_order_saved = on_order_saved

        # Record Transaction Connections
        self.record_view.item_added_to_cart.connect(self.handle_add_to_cart)
        self.record_view.confirm_btn.clicked.connect(self.handle_confirm_transaction)
        
        # Order Status Connections
        self.status_view.filter_changed.connect(self.load_orders)
        self.status_view.search_input.textChanged.connect(self.load_orders)
        
        # UI Action Connections
        self.status_view.status_changed.connect(self.handle_status_update)
        self.status_view.view_requested.connect(self.open_order_popup)

        self.load_orders()

    def load_catalog(self):
        products = self.inv_model.get_all_products()
        self.record_view.populate_catalog(products)

    def handle_add_to_cart(self, product):
        self.record_view.add_to_selected(product)

    def handle_confirm_transaction(self):
        cust_name = self.record_view.name_input.text().strip()
        cust_phone = self.record_view.phone_input.text().strip()
        address = self.record_view.address_input.text().strip()
        
        # Fallback to current behavior depending on your record UI logic
        try:
            platform = self.record_view.platform_combo.currentText()
            order_type = platform
        except AttributeError:
            order_type = "Online" if getattr(self.record_view, "online_tab", None) and self.record_view.online_tab.isChecked() else "Walk-in"
            
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
        if self.on_order_saved:
            self.on_order_saved()

    def load_orders(self):
        current_tab = self.status_view.get_active_tab()
        search = self.status_view.search_input.text().strip()
        
        orders = self.txn_model.get_all_orders(current_tab, search)
        self.status_view.display_orders(orders)
        
    def handle_status_update(self, order_code, new_status):
        success = self.txn_model.update_order_status(order_code, new_status)
        if success:
            # Refresh Order Status board to filter out terminal states instantly
            self.load_orders()
            # If the user has wired up on_order_saved, trigger the history board to update
            if self.on_order_saved:
                self.on_order_saved()
        
    def open_order_popup(self, order_code):
        # Fetch the professional order details using the order_code
        detail = self.txn_model.get_order_detail(order_code)
        
        if detail:
            from views.order_status_view import OrderDetailDialog
            dialog = OrderDetailDialog(self.status_view, detail)
            dialog.exec()