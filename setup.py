# setup.py
"""
IDERP Setup Configuration for ERPNext 15
Sistema Stampa Digitale - Package Installation
"""

from setuptools import setup, find_packages
import os

def read(fname):
    """Read file content"""
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

# Read requirements
def get_requirements():
    """Get requirements from requirements.txt"""
    try:
        with open('requirements.txt', 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        return ['frappe>=15.0.0', 'erpnext>=15.0.0']

setup(
    name="iderp",
    version="2.0.0",
    
    # Metadata
    description="Sistema completo per stampa digitale con calcoli automatici Metro Quadrato/Lineare/Pezzo",
    long_description="""
IDERP - Sistema Stampa Digitale per ERPNext 15

Funzionalità principali:
- Vendita multi-unità: Metro Quadrato, Metro Lineare, Pezzo
- Customer Groups con minimi configurabili
- Scaglioni prezzo dinamici
- Calcoli automatici server-side e client-side
- Dashboard e reportistica avanzata
- Compatible con ERPNext 15+

Perfetto per aziende di stampa digitale, serigrafia, cartotecnica.
    """.strip(),
    long_description_content_type="text/plain",
    
    # Author info
    author="idstudio AI",
    author_email="ai@idstudio.org",
    maintainer="idstudio AI",
    maintainer_email="ai@idstudio.org",
    
    # URLs
    url="https://github.com/haringk/iderp2",
    project_urls={
        "Bug Reports": "https://github.com/haringk/iderp2/issues",
        "Source": "https://github.com/haringk/iderp2",
        "Documentation": "https://github.com/haringk/iderp2/blob/master/README.md"
    },
    
    # License
    license="MIT",
    
    # Classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Manufacturing",
        "Topic :: Office/Business :: Financial :: Accounting",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Framework :: Flask",
        "Environment :: Web Environment",
        "Operating System :: OS Independent"
    ],
    
    # Python version requirement
    python_requires=">=3.8",
    
    # Package discovery
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    
    # Dependencies
    install_requires=get_requirements(),
    
    # Extra dependencies for development
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'black>=21.0',
            'flake8>=3.9',
            'mypy>=0.900'
        ],
        'test': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'factory-boy>=3.2'
        ]
    },
    
    # Package data
    package_data={
        'iderp': [
            'public/js/*.js',
            'public/css/*.css',
            'public/images/*',
            'templates/*.html',
            'templates/**/*.html',
            'doctype/*/fixtures/*.json',
            'fixtures/*.json'
        ]
    },
    
    # Data files
    data_files=[
        ('iderp/fixtures', ['fixtures/*.json']) if os.path.exists('fixtures') else []
    ],
    
    # Entry points
    entry_points={
        'frappe.apps': [
            'iderp = iderp'
        ]
    },
    
    # Keywords for PyPI search
    keywords=[
        'erpnext', 'frappe', 'erp', 'stampa digitale', 'digital printing',
        'serigrafia', 'printing', 'metro quadrato', 'customer groups',
        'pricing tiers', 'quotation', 'sales'
    ],
    
    # Platform
    platforms=['any'],
    
    # Additional metadata for ERPNext 15
    app_name="iderp",
    app_title="IDERP - Sistema Stampa Digitale",
    app_publisher="idstudio AI",
    app_description="Plugin ERPNext per stampa digitale con calcoli universali",
    app_email="ai@idstudio.org",
    app_license="MIT",
    app_version="2.0.0",
    required_apps=["frappe", "erpnext"],
    
    # Frappe app hooks (informational)
    app_include_css=[
        "/assets/iderp/css/iderp.css",
        "/assets/iderp/css/ecommerce_styles.css"
    ],
    app_include_js=[
        "/assets/iderp/js/iderp.js"
    ],
    
    # ERPNext 15 compatibility flags
    is_frappe_15_compatible=True,
    is_erpnext_15_compatible=True,
    
    # Documentation
    cmdclass={},
    
    # Test suite
    test_suite='tests',
    tests_require=[
        'pytest>=6.0',
        'pytest-cov>=2.0'
    ]
)

# Post-install message
print("""
🎉 IDERP v2.0.0 Setup Complete!

📋 Next Steps:
1. Install: bench --site [site-name] install-app iderp
2. Setup: Go to IDERP workspace to configure
3. Configure: Set up Customer Groups and Item pricing
4. Test: Create a quotation with custom measurements

📖 Documentation: https://github.com/haringk/iderp2
🐛 Issues: https://github.com/haringk/iderp2/issues
📧 Support: ai@idstudio.org

ERPNext 15 Compatible ✅
""")
