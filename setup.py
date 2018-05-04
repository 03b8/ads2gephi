try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
        'name': 'ads2gephi',
        'description': 'A CLI tool for querying and modeling Gephi-importable citation networks from the Astrophysical Data System',
        'author': 'Theodor Costea',
        'url': '',
        'license': 'MIT',
        'author_email': 'theo.costea@gmail.com',
        'version': '0.1.0a1',
        'install_requires': ['ads', 'sqlalchemy', 'python-igraph'],
        'python_requires': '>=3',
        'packages': ['ads2gephi'],
        'scripts': [],
        'entry_points':{
            'console_scripts': ['ads2gephi = ads2gephi.cli:main']
        }
}

setup(**config)

