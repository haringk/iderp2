# config/desktop.py
"""
IDERP Desktop Configuration for ERPNext 15
Configurazione icone e workspace per IDERP
"""

from frappe import _

# Configurazione base app
app_icon = "fa fa-print"
app_color = "#3498db"
app_email = "ai@idstudio.org"
app_license = "MIT"

def get_data():
    """
    Return desktop icons configuration per ERPNext 15
    """
    return [
        # Main IDERP workspace
        {
            "module_name": "IDERP",
            "category": "Modules",
            "label": _("IDERP - Stampa Digitale"),
            "color": "#3498db",
            "icon": "fa fa-print",
            "type": "module",
            "description": _("Sistema completo per stampa digitale con calcoli automatici")
        },
        
        # Quick access items
        {
            "module_name": "Customer Group Price Rule",
            "label": _("Customer Group Rules"),
            "color": "#e74c3c",
            "icon": "fa fa-users",
            "type": "doctype",
            "link": "List/Customer Group Price Rule",
            "description": _("Gestisci regole prezzo per gruppi cliente")
        },
        
        {
            "module_name": "Item Configuration",
            "label": _("Item Pricing Setup"),
            "color": "#f39c12",
            "icon": "fa fa-cogs",
            "type": "page",
            "link": "item-pricing-setup",
            "description": _("Configura scaglioni prezzo e misure personalizzate")
        },
        
        # Reports section
        {
            "module_name": "IDERP Reports",
            "label": _("IDERP Reports"),
            "color": "#9b59b6",
            "icon": "fa fa-bar-chart",
            "type": "module",
            "description": _("Report e analisi vendite stampa digitale")
        }
    ]

# Workspace configuration for ERPNext 15
def get_workspace_sidebar_items():
    """
    Return workspace sidebar items
    """
    return [
        {
            "title": _("Masters"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Customer Group Price Rule",
                    "label": _("Price Rules"),
                    "description": _("Customer group pricing rules")
                }
            ]
        },
        {
            "title": _("Setup"),
            "items": [
                {
                    "type": "page",
                    "name": "item-pricing-setup",
                    "label": _("Item Pricing"),
                    "description": _("Configure item pricing tiers")
                },
                {
                    "type": "page", 
                    "name": "customer-group-setup",
                    "label": _("Customer Groups"),
                    "description": _("Setup customer groups and minimums")
                }
            ]
        },
        {
            "title": _("Transactions"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Quotation",
                    "label": _("Quotations"),
                    "description": _("Sales quotations with automatic pricing")
                },
                {
                    "type": "doctype",
                    "name": "Sales Order",
                    "label": _("Sales Orders"),
                    "description": _("Confirmed sales orders")
                }
            ]
        },
        {
            "title": _("Reports"),
            "items": [
                {
                    "type": "report",
                    "name": "IDERP Pricing Analysis",
                    "label": _("Pricing Analysis"),
                    "is_query_report": True
                },
                {
                    "type": "report",
                    "name": "Customer Group Performance",
                    "label": _("Customer Performance"),
                    "is_query_report": True
                }
            ]
        }
    ]

# Gestione permessi per workspace
def has_permission(user=None):
    """
    Check if user has permission to access IDERP workspace
    """
    import frappe
    
    if not user:
        user = frappe.session.user
    
    # System Manager sempre autorizzato
    if "System Manager" in frappe.get_roles(user):
        return True
    
    # Sales roles autorizzati
    user_roles = frappe.get_roles(user)
    allowed_roles = ["Sales Manager", "Sales User", "Sales Master Manager"]
    
    return any(role in user_roles for role in allowed_roles)

# Cards per dashboard
def get_dashboard_cards():
    """
    Return dashboard cards for IDERP workspace
    """
    return [
        {
            "name": "Quotations This Month",
            "label": _("Quotations This Month"),
            "function": "iderp.dashboard.get_quotations_this_month",
            "color": "#3498db",
            "icon": "fa fa-file-text-o"
        },
        {
            "name": "Top Customer Groups",
            "label": _("Top Customer Groups"),
            "function": "iderp.dashboard.get_top_customer_groups", 
            "color": "#e74c3c",
            "icon": "fa fa-users"
        },
        {
            "name": "Items with Custom Pricing",
            "label": _("Configured Items"),
            "function": "iderp.dashboard.get_configured_items_count",
            "color": "#f39c12", 
            "icon": "fa fa-cogs"
        },
        {
            "name": "Average Order Value",
            "label": _("Avg Order Value"),
            "function": "iderp.dashboard.get_average_order_value",
            "color": "#27ae60",
            "icon": "fa fa-money"
        }
    ]

# Shortcuts per toolbar
def get_quick_shortcuts():
    """
    Return quick shortcuts for IDERP
    """
    return [
        {
            "label": _("New Quotation"),
            "url": "/app/quotation/new",
            "icon": "fa fa-plus",
            "color": "#3498db"
        },
        {
            "label": _("Item Setup"),
            "url": "/app/item",
            "icon": "fa fa-cogs", 
            "color": "#f39c12"
        },
        {
            "label": _("Customer Groups"),
            "url": "/app/customer-group",
            "icon": "fa fa-users",
            "color": "#e74c3c"
        },
        {
            "label": _("Price Rules"),
            "url": "/app/customer-group-price-rule",
            "icon": "fa fa-money",
            "color": "#27ae60"
        }
    ]

# Configuration per menu principal
workspace_config = {
    "name": "IDERP",
    "title": _("IDERP - Stampa Digitale"),
    "icon": "fa fa-print",
    "color": "#3498db",
    "description": _("Sistema completo per gestione stampa digitale con calcoli automatici metro quadrato, metro lineare e al pezzo"),
    "shortcuts": get_quick_shortcuts(),
    "cards": get_dashboard_cards(),
    "sidebar_items": get_workspace_sidebar_items()
}
