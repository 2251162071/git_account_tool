from pathlib import Path
import subprocess
from typing import Optional

class SSHManager:
    def __init__(self, ssh_dir: Optional[Path] = None):
        if ssh_dir is None:
            ssh_dir = Path.home() / '.ssh'
        self.ssh_dir = Path(ssh_dir).expanduser().resolve()
        self.ssh_dir.mkdir(exist_ok=True)
        
    def generate_key(self, name: str, email: str) -> Path:
        key_path = self.ssh_dir / f"id_rsa_{name}"
        if not key_path.exists():
            subprocess.run([
                'ssh-keygen',
                '-t', 'rsa',
                '-b', '4096',
                '-C', email,
                '-f', str(key_path),
                '-N', ''
            ], check=True)
        return key_path

    def add_to_agent(self, key_path: Path):
        try:
            subprocess.run(['ssh-add', '-l'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            subprocess.run(['eval', '$(ssh-agent -s)'], shell=True, check=True)
        subprocess.run(['ssh-add', str(key_path)], check=True)

    def get_public_key(self, key_path: Path) -> Optional[str]:
        pub_key_path = Path(str(key_path) + '.pub')
        if pub_key_path.exists():
            return pub_key_path.read_text().strip()
        return None

    def test_github_connection(self, key_path, alias=None):
        if alias is None:
            file_name = Path(key_path).name
            alias = file_name.replace('id_rsa_', '') if file_name.startswith('id_rsa_') else ''
        ssh_host = f"git@github.com-{alias}" if alias else "git@github.com"
        cmd = [
            "ssh",
            "-i", str(key_path),
            "-o", "StrictHostKeyChecking=no",
            "-T",
            ssh_host
        ]
        try:
            import os
            env = os.environ.copy()
            env.pop("GIT_PROXY_COMMAND", None)
            ret = subprocess.run(cmd, capture_output=True, timeout=10, env=env, text=True)
            if ret.returncode == 1 and "successfully authenticated" in (ret.stdout + ret.stderr):
                return True, ret.stdout + ret.stderr
            return ret.returncode == 0, (ret.stdout + ret.stderr)
        except Exception as e:
            return False, str(e)