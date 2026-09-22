from PyQt6.QtWidgets import QMessageBox

class POController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.view.submit_po_btn.clicked.connect(self.handle_submit_po)

    def load_po_history(self):
        pos = self.model.get_all_po()
        self.view.display_po_history(pos)

    def handle_submit_po(self):
        supplier = self.view.supplier_combo.currentText()
        date_exp = self.view.date_input.text()
        total_cost = self.view.get_estimated_total()

        if supplier == "Select Supplier":
            QMessageBox.warning(self.view, "Validation", "Please select a supplier.")
            return

        item_name = self.view.item_name.text().strip()
        try:
            item_qty = int(self.view.item_qty.text())
            item_cost = float(self.view.item_cost.text())
        except ValueError:
            item_qty, item_cost = 0, 0.0

        po_code = self.model.create_po(supplier, date_exp, total_cost,
                                       item_name, item_qty, item_cost)
        QMessageBox.information(self.view, "Success", f"Purchase Order {po_code} submitted!")
        self.load_po_history()
