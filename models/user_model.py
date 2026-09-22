"""MODEL: staff logins. AE Trends has no separate "users" table -
login accounts live in the Staff table (Username, PasswordHash)."""

VALID_ROLES = ("Owner", "Cashier", "Inventory Staff")


class UserModel:
    def __init__(self, db_manager):
        self.db = db_manager

    def authenticate(self, username, password):
        """Returns a normalized dict the rest of the app can use, or None."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM Staff WHERE Username = ? AND PasswordHash = ?",
                (username, password),
            )
            row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["StaffID"],
            "full_name": row["Name"],
            "role": row["Role"],
            "username": row["Username"],
        }

    def register_user(self, username, password, full_name, role="Cashier"):
        """Creates a new Staff login. role must be one of VALID_ROLES."""
        if role not in VALID_ROLES:
            role = "Cashier"
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT StaffID FROM Staff WHERE Username = ?", (username,))
            if cursor.fetchone():
                return False  # Username taken

            cursor.execute(
                """INSERT INTO Staff (Name, Role, Username, PasswordHash)
                   VALUES (?, ?, ?, ?)""",
                (full_name, role, username, password),
            )
            conn.commit()
            return True
