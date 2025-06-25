# iderp/__init__.py - VERSIONE INSTALLAZIONE
"""
iderp Module Initialization
Sistema Stampa Digitale per ERPNext 15
"""

__version__ = "2.0.0"

# Module metadata
app_name = "iderp"
app_title = "iderp - Sistema Stampa Digitale"
app_publisher = "idstudio"
app_description = "Plugin ERPNext per stampa digitale"
app_email = "dev@idstudio.org"
app_license = "MIT"

# ERPNext 15 compatibility flags
is_frappe_15_compatible = True
required_frappe_version = ">=15.0.0"
required_erpnext_version = ">=15.0.0"

def get_version():
    """Return current version"""
    return __version__

def get_app_info():
    """Return app information"""
    return {
        "name": app_name,
        "title": app_title,
        "version": __version__,
        "publisher": app_publisher,
        "description": app_description,
        "email": app_email,
        "license": app_license,
        "frappe_compatible": is_frappe_15_compatible
    }

# Gli import dei moduli frappe-dipendenti verranno caricati dopo l'installazione

# __init__.py zzz
# """
# iderp Module Initialization
# Sistema Stampa Digitale per ERPNext 15
# """
# 
# __version__ = "2.0.0"
# 
# # Import key functions for module access
# from .iderp.pricing_utils import (
#     calculate_universal_item_pricing,
#     calculate_universal_item_pricing_with_fallback,
#     get_item_pricing_tiers,
#     get_customer_group_min_sqm
# )
# 
# from .iderp.customer_group_pricing import (
#     get_customer_group_pricing,
#     apply_customer_group_rules
# )
# 
# # Import setup functions
# from .iderp.install import after_install
# 
# # Import DocType classes for external access
# try:
#     from .iderp.doctype.customer_group_price_rule.customer_group_price_rule import CustomerGroupPriceRule
#     from .iderp.doctype.item_pricing_tier.item_pricing_tier import ItemPricingTier
#     from .iderp.doctype.customer_group_minimum.customer_group_minimum import CustomerGroupMinimum
# except ImportError:
#     # DocTypes might not be installed yet
#     pass
# 
# # Module metadata
# app_name = "iderp"
# app_title = "iderp - Sistema Stampa Digitale"
# app_publisher = "idstudio"
# app_description = "Plugin ERPNext per stampa digitale"
# app_email = "dev@idstudio.org"
# app_license = "MIT"
# 
# # ERPNext 15 compatibility flags
# is_frappe_15_compatible = True
# required_frappe_version = ">=15.0.0"
# required_erpnext_version = ">=15.0.0"
# 
# def get_version():
#     """Return current version"""
#     return __version__
# 
# def get_app_info():
#     """Return app information"""
#     return {
#         "name": app_name,
#         "title": app_title,
#         "version": __version__,
#         "publisher": app_publisher,
#         "description": app_description,
#         "email": app_email,
#         "license": app_license,
#         "frappe_compatible": is_frappe_15_compatible
#     }
# 
# def validate_dependencies():
#     """Validate ERPNext 15 dependencies"""
#     import frappe
#     
#     # Check Frappe version
#     frappe_version = frappe.__version__
#     if not frappe_version.startswith(('15.', '16.', '17.')):
#         frappe.throw(f"iderp requires Frappe 15+. Current version: {frappe_version}")
#     
#     # Check ERPNext installation
#     try:
#         import erpnext
#         erpnext_version = erpnext.__version__
#         if not erpnext_version.startswith(('15.', '16.', '17.')):
#             frappe.throw(f"iderp requires ERPNext 15+. Current version: {erpnext_version}")
#     except ImportError:
#         frappe.throw("ERPNext is required for iderp")
# 
# def check_installation():
#     """Check if iderp is properly installed"""
#     import frappe
#     
#     required_doctypes = [
#         "Customer Group Price Rule",
#         "Item Pricing Tier", 
#         "Customer Group Minimum"
#     ]
#     
#     missing_doctypes = []
#     for doctype in required_doctypes:
#         if not frappe.db.exists("DocType", doctype):
#             missing_doctypes.append(doctype)
#     
#     if missing_doctypes:
#         return {
#             "installed": False,
#             "missing_doctypes": missing_doctypes,
#             "message": f"Missing DocTypes: {', '.join(missing_doctypes)}"
#         }
#     
#     # Check custom fields
#     required_fields = [
#         ("Item", "supports_custom_measurement"),
#         ("Item", "tipo_vendita_default"),
#         ("Quotation Item", "tipo_vendita"),
#         ("Quotation Item", "base"),
#         ("Quotation Item", "altezza")
#     ]
#     
#     missing_fields = []
#     for doctype, fieldname in required_fields:
#         if not frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname}):
#             missing_fields.append(f"{doctype}.{fieldname}")
#     
#     return {
#         "installed": len(missing_fields) == 0,
#         "missing_fields": missing_fields,
#         "message": "iderp is properly installed" if len(missing_fields) == 0 else f"Missing fields: {', '.join(missing_fields)}"
#     }
# 
# def get_system_status():
#     """Get comprehensive system status"""
#     import frappe
#     
#     try:
#         validate_dependencies()
#         installation_status = check_installation()
#         
#         # Count configured items
#         configured_items = frappe.db.count("Item", {"supports_custom_measurement": 1})
#         
#         # Count customer groups
#         customer_groups = frappe.db.count("Customer Group", 
#             filters={"name": ["in", ["Finale", "Bronze", "Gold", "Diamond"]]})
#         
#         # Count active pricing rules
#         active_rules = frappe.db.count("Customer Group Price Rule", {"enabled": 1})
#         
#         return {
#             "status": "healthy" if installation_status["installed"] else "incomplete",
#             "version": __version__,
#             "dependencies_ok": True,
#             "installation": installation_status,
#             "statistics": {
#                 "configured_items": configured_items,
#                 "customer_groups": customer_groups,
#                 "active_pricing_rules": active_rules
#             }
#         }
#         
#     except Exception as e:
#         return {
#             "status": "error",
#             "version": __version__,
#             "dependencies_ok": False,
#             "error": str(e)
#         }
# 
# # Boot function for client-side
# def boot_session(bootinfo):
#     """Add iderp data to boot session"""
#     import frappe
#     
#     try:
#         if frappe.session.user != "Guest":
#             bootinfo.iderp = {
#                 "version": __version__,
#                 "app_info": get_app_info(),
#                 "system_status": get_system_status()
#             }
#     except Exception:
#         # Don't break boot if iderp has issues
#         pass
