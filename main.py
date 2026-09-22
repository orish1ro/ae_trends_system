import sys
import ctypes
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from database.db_manager import DatabaseManager
from views.login_view import LoginView
from views.main_window import MainWindow
from controllers.auth_controller import AuthController

def main():
    # --- WINDOWS TASKBAR FIX ---
    # Forces Windows to recognize this script as a standalone app to show the icon
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("aetrends.pos.app.1")
    except:
        pass
        
    app = QApplication(sys.argv)
    app.setStyle('Fusion') 
    
    # --- SET GLOBAL WINDOW ICON ---
    app.setWindowIcon(QIcon("ae-logo.jpg"))
    
    # --- GLOBAL FIGMA THEME RESET ---
    app.setStyleSheet("""
        /* Force light background on the main window */
        QMainWindow, QStackedWidget {
            background-color: #F8F4EC;
        }
        
        /* Force dark text globally to fix invisible text */
        QWidget {
            color: #2A2421;
        }
        
        /* Clean up the data tables */
        QTableWidget {
            background-color: #FFFFFF;
            color: #2A2421;
            gridline-color: #E5E0D5;
            border: 1px solid #E5E0D5;
            border-radius: 8px;
        }
        QHeaderView::section {
            background-color: #F8F4EC;
            color: #888888;
            font-weight: bold;
            border: none;
            border-bottom: 2px solid #E5E0D5;
            padding: 10px;
            text-align: left;
        }
        
        /* Style inputs to match the design */
        QLineEdit, QComboBox {
            background-color: #FFFFFF;
            color: #2A2421;
            border: 1px solid #D6CEBC;
            border-radius: 6px;
            padding: 8px;
        }
        QLineEdit:focus, QComboBox:focus {
            border: 1px solid #C09E3B;
        }
    """)

    # Initialize SQLite database with tables and sample data
    db = DatabaseManager("ae_trends.db")
    db.init_db()

    # Setup Views
    login_view = LoginView()
    main_window = MainWindow()

    # Setup Controller
    auth_controller = AuthController(db, login_view, main_window)

    login_view.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()