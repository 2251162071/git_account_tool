import json
from pathlib import Path
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
    QLabel, QLineEdit, QFormLayout, QApplication
)
from PyQt5.QtCore import Qt
from models.account import GitAccount
from services.ssh_manager import SSHManager
from services.git_config_manager import GitConfigManager
import webbrowser

class AddAccountDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Git Account")
        layout = QFormLayout()

        self.name_input = QLineEdit()
        self.email_input = QLineEdit()
        self.alias_input = QLineEdit()

        layout.addRow("Name:", self.name_input)
        layout.addRow("Email:", self.email_input)
        layout.addRow("Alias:", self.alias_input)

        buttons = QVBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)
        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Git Account Switcher")
        self.setMinimumSize(600, 400)

        self.ssh_manager = SSHManager()
        self.git_manager = GitConfigManager()
        self.accounts = []

        self.init_ui()
        self.load_accounts()

    def init_ui(self):
        # Khởi tạo QTabWidget và thiết lập làm central widget
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # ----- Tab SSH Manager -----
        self.ssh_manager_tab = QWidget()
        self.ssh_manager_layout = QVBoxLayout(self.ssh_manager_tab)

        add_button = QPushButton("Add Account")
        add_button.clicked.connect(self.add_account)
        self.ssh_manager_layout.addWidget(add_button)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Name", "Email", "Alias", "Status", "Actions"]
        )
        self.ssh_manager_layout.addWidget(self.table)

        test_connect_btn = QPushButton("Test Connect (Active Account)")
        test_connect_btn.clicked.connect(self.test_active_account_connection)
        self.ssh_manager_layout.addWidget(test_connect_btn)

        self.tab_widget.addTab(self.ssh_manager_tab, "SSH Manager")

        # ----- Tab Hướng Dẫn -----
        from PyQt5.QtWidgets import QTextEdit

        self.guide_tab = QWidget()
        guide_layout = QVBoxLayout(self.guide_tab)

        instructions = """
        <h2>HƯỚNG DẪN SỬ DỤNG GIT VỚI NHIỀU TÀI KHOẢN</h2>
        <h3>1. Giả sử bạn có tài khoản với alias (Host) là <b>work</b> được tạo bởi công cụ này.</h3>
        <h4>File <code>~/.ssh/config</code> sẽ có dạng:</h4>
        <pre>
Host work
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_rsa_work
        </pre>
        <h3>2. Cách thao tác Git thông thường:</h3>
        <ul>
        <li><code>git clone git@github.com:tronghuan/tuthanhde.git</code></li>
        </ul>
        <h3>3. Khi sử dụng alias, bạn thay <b>github.com</b> thành tên alias (<b>work</b>):</h3>
        <ul>
        <li><code>git clone git@work:tronghuan/tuthanhde.git</code></li>
        </ul>
        <h4>Hoặc khi đổi remote cho repo đã clone:</h4>
        <ul>
        <li><code>git remote set-url origin git@work:tronghuan/tuthanhde.git</code></li>
        </ul>
        <h3>4. Một tài khoản khác (ví dụ alias là <b>personal</b>):</h3>
        <pre>
Host personal
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_rsa_personal
        </pre>
        <ul>
        <li><code>git clone git@personal:tronghuan/duan-rieng.git</code></li>
        </ul>
        <hr>
        <h4>Lưu ý:</h4>
        <ul>
            <li>Bạn có thể thêm nhiều Host khác nhau cho từng tài khoản Git với key tương ứng.</li>
            <li>Lệnh <b>git@tên_alias</b>: sẽ tự chọn đúng key và config.</li>
            <li>Không cần dùng <code>ssh-add</code> thủ công, công cụ đã cấu hình sẵn.</li>
        </ul>
        """

        guide_text = QTextEdit()
        guide_text.setReadOnly(True)
        guide_text.setHtml(instructions)
        guide_layout.addWidget(guide_text)
        self.tab_widget.addTab(self.guide_tab, "Hướng Dẫn")

    def update_table(self):
        """Update the table with current account information."""
        self.table.setColumnCount(8)  # Thêm cột Browser trước Delete
        self.table.setHorizontalHeaderLabels([
            "Name", "Email", "Alias", "Status", "Actions", "Public Key", "Browser", "Delete"
        ])
        self.table.setRowCount(len(self.accounts))
        for row, account in enumerate(self.accounts):
            # Name
            self.table.setItem(row, 0, QTableWidgetItem(account.name))
            # Email
            self.table.setItem(row, 1, QTableWidgetItem(account.email))
            # Alias
            self.table.setItem(row, 2, QTableWidgetItem(account.alias))
            # Status
            is_active = self.git_manager.is_current_account(account)
            status = "Active" if is_active else "Inactive"
            self.table.setItem(row, 3, QTableWidgetItem(status))
            # Actions (Switch button)
            switch_button = QPushButton("Switch to")
            switch_button.clicked.connect(lambda checked, acc=account: self.switch_account(acc))
            self.table.setCellWidget(row, 4, switch_button)
            # Public Key (Copy button)
            copy_btn = QPushButton("Copy")
            copy_btn.clicked.connect(lambda checked, acc=account: self.copy_public_key(acc))
            self.table.setCellWidget(row, 5, copy_btn)
            # Browser (Open button)
            open_btn = QPushButton("Open")
            open_btn.clicked.connect(
                lambda checked: webbrowser.open("https://github.com/settings/ssh/new")
            )
            self.table.setCellWidget(row, 6, open_btn)
            # Delete button
            delete_btn = QPushButton("Xóa")
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_account(r))
            self.table.setCellWidget(row, 7, delete_btn)
        self.table.resizeColumnsToContents()

        # Điều chỉnh kích thước cửa sổ chính
        self.resize(950, 500)  # Chỉnh lại thông số phù hợp với số lượng/cột bạn dùng

        # Thiết lập chế độ auto-resize cho các cột của QTableWidget
        from PyQt5.QtWidgets import QHeaderView
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)  # Toàn bộ cột tự co giãn theo khung
        # Nếu muốn cột đầu nhỏ, các cột khác tự động giãn, có thể dùng:
        # from PyQt5.QtWidgets import QHeaderView
        # header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        # for i in range(1, self.table.columnCount()):
        #     header.setSectionResizeMode(i, QHeaderView.Stretch)

    def copy_public_key(self, account):
        public_key = self.ssh_manager.get_public_key(account.key_path)
        if public_key:
            clipboard = QApplication.clipboard()
            clipboard.setText(public_key)
            QMessageBox.information(self, "Copied", "Đã copy public key vào clipboard!")
        else:
            QMessageBox.warning(self, "Not Found", "Không tìm thấy file public key cho tài khoản này!")

    def test_connection(self, account):
        """Test connection to Github using the account's SSH key."""
        success, msg = self.ssh_manager.test_github_connection(account.key_path, account.alias)
        if not success:
            QMessageBox.warning(self, "Failed", f"Kết nối SSH thất bại!\n{msg}")
            return
        if success:
            QMessageBox.information(self, "Success", "Kết nối SSH tới github.com thành công!")
        else:
            QMessageBox.warning(self, "Failed", f"Kết nối SSH thất bại!\n{msg}")

    def switch_account(self, account):
        """Switch to the selected Git account."""
        try:
            self.git_manager.switch_account(account)
            self.update_table()
            QMessageBox.information(self, "Success", f"Switched to account: {account.name}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to switch account: {str(e)}")

    def load_accounts(self):
        config_path = Path("config/accounts.json")
        if config_path.exists():
            try:
                with config_path.open() as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.accounts = [GitAccount.from_dict(acc) for acc in data]
                    else:
                        self.accounts = []
                self.update_table()
            except json.JSONDecodeError:
                self.accounts = []
                QMessageBox.warning(self, "Warning",
                                    "Failed to parse accounts.json file. Starting with empty accounts list.")
            except Exception as e:
                self.accounts = []
                QMessageBox.warning(self, "Error", f"Error loading accounts: {str(e)}")

    def save_accounts(self):
        config_path = Path("config/accounts.json")
        config_path.parent.mkdir(exist_ok=True)
        data = [acc.to_dict() for acc in self.accounts]
        config_path.write_text(json.dumps(data, indent=2))

    def add_account(self):
        dialog = AddAccountDialog(self)
        if dialog.exec_():
            name = dialog.name_input.text()
            email = dialog.email_input.text()
            alias = dialog.alias_input.text()

            # Generate SSH key
            key_path = self.ssh_manager.generate_key(name, email)

            # Create account
            account = GitAccount(name=name, email=email, key_path=key_path, alias=alias)

            # Update configs
            self.git_manager.update_ssh_config(account)

            # Add to accounts list
            self.accounts.append(account)
            self.save_accounts()
            self.update_table()

            # Show public key
            pub_key = self.ssh_manager.get_public_key(key_path)
            if pub_key:
                QMessageBox.information(self, "SSH Public Key",
                                        f"Add this public key to your GitHub account:\n\n{pub_key}")

    def test_active_account_connection(self):
        """Test SSH connection to github.com using the currently active account."""
        active_account = None
        for acc in self.accounts:
            if self.git_manager.is_current_account(acc):
                active_account = acc
                break
        if not active_account:
            QMessageBox.warning(self, "No Active Account", "Không có tài khoản nào đang active để kiểm tra!")
            return

        success, msg = self.ssh_manager.test_github_connection(active_account.key_path, active_account.alias)
        if success:
            QMessageBox.information(self, "Success", f"Kết nối SSH tới github.com bằng tài khoản '{active_account.name}' thành công!")
        else:
            QMessageBox.warning(self, "Failed", f"Kết nối SSH thất bại!\n{msg}")

    def edit_account(self, row):
        """Sửa account trên dòng row."""
        account = self.accounts[row]
        dialog = AddAccountDialog(self)
        dialog.name_input.setText(account.name)
        dialog.email_input.setText(account.email)
        dialog.alias_input.setText(account.alias)
        if dialog.exec_():
            # Cập nhật thông tin
            account.name = dialog.name_input.text()
            account.email = dialog.email_input.text()
            account.alias = dialog.alias_input.text()
            # (Tùy ý: cập nhật key nếu cần)
            self.save_accounts()
            self.update_table()
            QMessageBox.information(self, "Đã cập nhật", "Cập nhật thông tin tài khoản thành công.")

    def delete_account(self, row):
        """Xóa account trên dòng row và cả config."""
        account = self.accounts[row]
        reply = QMessageBox.question(
            self, "Xác nhận xóa",
            f"Bạn có chắc chắn muốn xóa tài khoản '{account.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # Xóa block Host khỏi ~/.ssh/config
            self.git_manager.remove_ssh_config(account.alias)
            # Xóa khỏi danh sách tài khoản
            self.accounts.pop(row)
            self.save_accounts()
            self.update_table()