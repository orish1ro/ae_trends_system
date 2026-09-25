from models.user_model import UserModel
from models.inventory_model import InventoryModel
from models.transaction_model import TransactionModel
from models.po_model import POModel
from models.history_model import HistoryModel
from controllers.inventory_controller import InventoryController
from controllers.transaction_controller import TransactionController
from controllers.report_controller import ReportController
from controllers.po_controller import POController
from controllers.history_controller import HistoryController
from PyQt6.QtWidgets import QMessageBox

class AuthController:
    def __init__(self, db, login_view, main_window):
        self.db = db
        self.login_view = login_view
        self.main_window = main_window
        self.user_model = UserModel(db)

        # Login signals
        self.login_view.login_button.clicked.connect(self.handle_login)
        self.main_window.logout_requested.connect(self.handle_logout)

        # Sign Up signals
        self.login_view.btn_go_to_signup.clicked.connect(lambda: self.login_view.stacked_cards.setCurrentIndex(1))
        self.login_view.btn_back_to_login.clicked.connect(lambda: self.login_view.stacked_cards.setCurrentIndex(0))
        self.login_view.btn_submit_signup.clicked.connect(self.handle_signup)

    def handle_login(self):
        username = self.login_view.username_input.text().strip()
        password = self.login_view.password_input.text().strip()

        user = self.user_model.authenticate(username, password)
        if user:
            self.init_app_controllers(user)
            self.login_view.hide()
            self.main_window.set_user(user['full_name'], user['role'])
            self.main_window.show()
        else:
            QMessageBox.warning(self.login_view, "Login Failed", "Invalid username or password.")

    def handle_signup(self):
        full_name = self.login_view.reg_name_input.text().strip()
        username = self.login_view.reg_username_input.text().strip()
        password = self.login_view.reg_password_input.text().strip()

        if not full_name or not username or not password:
            QMessageBox.warning(self.login_view, "Validation Error", "All fields are required.")
            return

        # Default new signups to Staff/Employee role
        success = self.user_model.register_user(username, password, full_name, role="Staff")
        if success:
            QMessageBox.information(self.login_view, "Success", "Account created successfully! You can now log in.")
            self.login_view.reg_name_input.clear()
            self.login_view.reg_username_input.clear()
            self.login_view.reg_password_input.clear()
            self.login_view.stacked_cards.setCurrentIndex(0)
            self.login_view.username_input.setText(username)
            self.login_view.password_input.clear()
        else:
            QMessageBox.warning(self.login_view, "Error", "Username already exists. Choose another.")

    def init_app_controllers(self, user):
        # StaffID is required (NOT NULL) on Product, Orders and PurchaseOrder,
        # so every model that can write those tables needs to know who is logged in.
        staff_id = user["id"]
        inv_model = InventoryModel(self.db, staff_id)
        txn_model = TransactionModel(self.db, staff_id)
        po_model = POModel(self.db, staff_id)

        self.inv_ctrl = InventoryController(inv_model, self.main_window.inventory_view)
        self.hist_ctrl = HistoryController(HistoryModel(self.db), self.main_window.transaction_history_view)
        self.txn_ctrl = TransactionController(
            txn_model, inv_model, self.main_window.record_tx_view,
            self.main_window.order_status_view, on_order_saved=self.hist_ctrl.load)
        self.po_ctrl = POController(
            po_model, self.main_window.purchase_orders_view, on_po_saved=self.hist_ctrl.load)
        self.rep_ctrl = ReportController(self.db, self.main_window.reports_view, self.main_window.dashboard_view)

        self.inv_ctrl.load_products()
        self.txn_ctrl.load_catalog()
        self.txn_ctrl.load_orders()
        self.po_ctrl.load_po_history()
        self.rep_ctrl.load_reports()
        self.hist_ctrl.load()

    def handle_logout(self):
        self.main_window.hide()
        self.login_view.username_input.clear()
        self.login_view.password_input.clear()
        self.login_view.stacked_cards.setCurrentIndex(0)
        self.login_view.show()