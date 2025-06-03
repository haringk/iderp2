from setuptools import setup, find_packages

setup(
    name="iderp",
    version="0.0.1",
    description="Custom fields and item sync for ERPNext",
    author="idstudio AI",
    author_email="ai@idstudio.org",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["frappe>=14,<15", "erpnext>=14,<15"],
)
