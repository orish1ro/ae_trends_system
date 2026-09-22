from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar)

class ReportsView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #F7F3EB;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("Reports")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #2A2421;")
        sub = QLabel("Review store sales performance, top product trends, and low stock warnings.")
        sub.setStyleSheet("font-size: 13px; color: #777777;")
        layout.addWidget(title)
        layout.addWidget(sub)

        # Best-Selling Products Card
        top_card = QFrame()
        top_card.setStyleSheet("background: white; border-radius: 8px; border: 1px solid #E5E0D5; padding: 20px;")
        top_layout = QVBoxLayout(top_card)

        t_title = QLabel("Best-Selling Products (Top 5)")
        t_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2A2421;")
        top_layout.addWidget(t_title)

        sample_best = [
            ("Basic White Tee", 45),
            ("Hydrating Moisturizer", 38),
            ("Cargo Pants", 32),
            ("Sunscreen SPF50", 28),
            ("Denim Jacket", 22)
        ]

        for name, units in sample_best:
            row = QHBoxLayout()
            lbl = QLabel(f"{name:25}")
            lbl.setStyleSheet("font-weight: 500;")
            bar = QProgressBar()
            bar.setMaximum(50)
            bar.setValue(units)
            bar.setTextVisible(False)
            bar.setStyleSheet("""
                QProgressBar { border: 1px solid #E5E0D5; border-radius: 4px; height: 16px; background: #F0EDE6; }
                QProgressBar::chunk { background-color: #C09E3B; border-radius: 4px; }
            """)
            u_lbl = QLabel(f"{units} units")
            u_lbl.setStyleSheet("color: #666; font-size: 12px;")
            row.addWidget(lbl)
            row.addWidget(bar)
            row.addWidget(u_lbl)
            top_layout.addLayout(row)

        layout.addWidget(top_card)

        # Inventory Low Stock Warning Card
        sec_title = QLabel("Inventory Health: Low Stock Warning")
        sec_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2A2421; margin-top: 10px;")
        layout.addWidget(sec_title)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["PRODUCT NAME", "CATEGORY", "CURRENT STOCK", "REORDER LEVEL", "ALERT STATUS"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("background: white; border-radius: 8px; border: 1px solid #E5E0D5;")
        layout.addWidget(self.table)

    def display_low_stock(self, items):
        self.table.setRowCount(len(items))
        for row, prod in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(prod['name']))
            self.table.setItem(row, 1, QTableWidgetItem(prod['category']))
            self.table.setItem(row, 2, QTableWidgetItem(f"{prod['stock_qty']} pcs"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{prod['reorder_level']} pcs"))
            self.table.setItem(row, 4, QTableWidgetItem("Critical" if prod['stock_qty'] <= 3 else "Low"))
