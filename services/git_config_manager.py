from pathlib import Path
import subprocess
from models.account import GitAccount
from typing import Optional

class GitConfigManager:
    def __init__(self, ssh_dir: Optional[Path] = None):
        if ssh_dir is None:
            ssh_dir = Path.home() / '.ssh'
        self.ssh_dir = Path(ssh_dir).expanduser().resolve()
        self.ssh_config_path = self.ssh_dir / 'config'

    def update_ssh_config(self, account: GitAccount):
        config_content = (
            f"Host {account.alias}\n"
            f"    HostName github.com\n"
            f"    User git\n"
            f"    IdentityFile {account.key_path}\n"
            f"    IdentitiesOnly yes\n"
        )
        if not self.ssh_config_path.exists():
            self.ssh_config_path.write_text(config_content)
        else:
            current_config = self.ssh_config_path.read_text()
            if f"Host {account.alias}" not in current_config:
                if not current_config.endswith('\n'):
                    current_config += '\n'
                self.ssh_config_path.write_text(current_config + config_content)

    def set_git_config(self, account: GitAccount):
        subprocess.run(['git', 'config', '--global', 'user.name', account.name], check=True)
        subprocess.run(['git', 'config', '--global', 'user.email', account.email], check=True)

    def switch_account(self, account: GitAccount):
        self.set_git_config(account)
        self.update_ssh_config(account)

    def is_current_account(self, account):
        try:
            current_name = self.get_config('user.name')
            current_email = self.get_config('user.email')
            return current_name == account.name and current_email == account.email
        except Exception:
            return False

    def get_config(self, key):
        try:
            result = subprocess.run(['git', 'config', '--get', key],
                                   capture_output=True,
                                   text=True,
                                   check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def remove_ssh_config(self, alias: str):
        if not self.ssh_config_path.exists():
            return
        lines = self.ssh_config_path.read_text().splitlines()
        new_lines = []
        skip_block = False
        for line in lines:
            if line.strip().startswith(f"Host github.com-{alias}"):
                skip_block = True
            elif skip_block and line.strip().startswith("Host "):
                skip_block = False
                new_lines.append(line)
                continue
            if not skip_block:
                new_lines.append(line)
        self.ssh_config_path.write_text('\n'.join(new_lines) + '\n')