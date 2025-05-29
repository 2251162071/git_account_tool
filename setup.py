# setup.py
try:
    from setuptools import setup
except ImportError:
    print("Please install setuptools first using: pip install setuptools")
    raise

APP = ['main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['PyQt5'],
    'includes': ['sip']
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)