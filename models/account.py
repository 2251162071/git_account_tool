# models/account.py
from dataclasses import dataclass
from pathlib import Path

@dataclass
class GitAccount:
    name: str
    email: str
    key_path: Path
    alias: str
    is_active: bool = False

    def to_dict(self):
        return {
            'name': self.name,
            'email': self.email,
            'key_path': str(self.key_path),
            'alias': self.alias,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data['name'],
            email=data['email'],
            key_path=Path(data['key_path']),
            alias=data['alias'],
            is_active=data.get('is_active', False)
        )