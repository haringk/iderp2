# iderp/dashboard.py
"""
Dashboard functions per IDERP workspace in ERPNext 15
Fornisce metriche e KPI per il sistema stampa digitale
"""

import frappe
from frappe import _
from frappe.utils import today, add_months, get_first_day, get_last_day, flt
from datetime import datetime, timedelta

@frappe.whitelist()
def get_quotations_this_month():
    """
    Ottieni numero quotazioni del mese corrente
    """
    try:
        first_day = get_first_day(today())
        last_day = get_last_day(today())
        
        # Conta quotazioni totali
        total_quotations = frappe.db.count("Quotation", {
            "transaction_date": ["between", [first_day, last_day]]
        })
        
        # Conta quotazioni IDERP (con tipo_vendita configurato)
        iderp_quotations = frappe.db.sql("""
            SELECT COUNT(DISTINCT q.name) as count
            FROM `tabQuotation` q
            JOIN `tabQuotation Item` qi ON qi.parent = q.name
            WHERE q.transaction_date BETWEEN %s AND %s
            AND qi.tipo_vendita IN ('Metro Quadrato', 'Metro Lineare', 'Pezzo')
        """, [first_day, last_day])[0][0]
        
        # Conta quotazioni confermate (diventate Sales Order)
        confirmed_quotations = frappe.db.count("Quotation", {
            "transaction_date": ["between", [first_day, last_day]],
            "status": "Ordered"
        })
        
        return {
            "value": total_quotations,
            "label": _("Quotations This Month"),
            "subtitle": f"{iderp_quotations} with IDERP, {confirmed_quotations} confirmed",
            "color": "#3498db",
            "trend": "up" if total_quotations > 0 else "neutral"
        }
        
    except Exception as e:
        frappe.logger().error(f"Dashboard error - quotations_this_month: {e}")
        return {
            "value": 0,
            "label": _("Quotations This Month"),
            "subtitle": "Error loading data",
            "color": "#95a5a6"
        }

@frappe.whitelist()
def get_top_customer_groups():
    """
    Ottieni performance dei gruppi cliente top
    """
    try:
        # Ultimi 3 mesi per analisi
        start_date = add_months(today(), -3)
        
        customer_group_stats = frappe.db.sql("""
            SELECT 
                c.customer_group,
                COUNT(DISTINCT q.name) as quotations_count,
                SUM(q.grand_total) as total_value,
                AVG(q.grand_total) as avg_value
            FROM `tabQuotation` q
            JOIN `tabCustomer` c ON c.name = q.party_name
            WHERE q.transaction_date >= %s
            AND q.docstatus = 1
            GROUP BY c.customer_group
            ORDER BY total_value DESC
            LIMIT 5
        """, [start_date], as_dict=True)
        
        if not customer_group_stats:
            return {
                "value": 0,
                "label": _("Top Customer Groups"),
                "subtitle": "No data available",
                "color": "#95a5a6"
            }
        
        top_group = customer_group_stats[0]
        total_groups = len(customer_group_stats)
        
        return {
            "value": total_groups,
            "label": _("Active Customer Groups"),
            "subtitle": f"Top: {top_group['customer_group']} (€{flt(top_group['total_value'], 0):,.0f})",
            "color": "#e74c3c",
            "details": customer_group_stats[:3]  # Top 3 per dettaglio
        }
        
    except Exception as e:
        frappe.logger().error(f"Dashboard error - top_customer_groups: {e}")
        return {
            "value": 0,
            "label": _("Customer Groups"),
            "subtitle": "Error loading data",
            "color": "#95a5a6"
        }

@frappe.whitelist()
def get_configured_items_count():
    """
    Ottieni numero item configurati per IDERP
    """
    try:
        # Item con misure personalizzate
        configured_items = frappe.db.count("Item", {
            "supports_custom_measurement": 1,
            "disabled": 0
        })
        
        # Item con scaglioni prezzo
        items_with_tiers = frappe.db.sql("""
            SELECT COUNT(DISTINCT i.name) as count
            FROM `tabItem` i
            JOIN `tabItem Pricing Tier` ipt ON ipt.parent = i.name
            WHERE i.disabled = 0
        """)[0][0]
        
        # Item con customer group minimums
        items_with_minimums = frappe.db.sql("""
            SELECT COUNT(DISTINCT i.name) as count
            FROM `tabItem` i  
            JOIN `tabCustomer Group Minimum` cgm ON cgm.parent = i.name
            WHERE i.disabled = 0
            AND cgm.enabled = 1
        """)[0][0]
        
        total_items = frappe.db.count("Item", {"disabled": 0})
        coverage_pct = (configured_items / total_items * 100) if total_items > 0 else 0
        
        return {
            "value": configured_items,
            "label": _("Configured Items"),
            "subtitle": f"{coverage_pct:.0f}% of items, {items_with_tiers} with tiers, {items_with_minimums} with minimums",
            "color": "#f39c12",
            "trend": "up" if configured_items > 0 else "neutral"
        }
        
    except Exception as e:
        frappe.logger().error(f"Dashboard error - configured_items: {e}")
        return {
            "value": 0,
            "label": _("Configured Items"),
            "subtitle": "Error loading data",
            "color": "#95a5a6"
        }

@frappe.whitelist()
def get_average_order_value():
    """
    Ottieni valore medio ordini per tipo vendita
    """
    try:
        # Ultimi 30 giorni
        start_date = add_months(today(), -1)
        
        # Valore medio per tipo vendita
        avg_by_type = frappe.db.sql("""
            SELECT 
                qi.tipo_vendita,
                COUNT(DISTINCT q.name) as orders_count,
                AVG(q.grand_total) as avg_total,
                SUM(q.grand_total) as total_value
            FROM `tabQuotation` q
            JOIN `tabQuotation Item` qi ON qi.parent = q.name
            WHERE q.transaction_date >= %s
            AND q.status = 'Ordered'
            AND qi.tipo_vendita IN ('Metro Quadrato', 'Metro Lineare', 'Pezzo')
            GROUP BY qi.tipo_vendita
            ORDER BY avg_total DESC
        """, [start_date], as_dict=True)
        
        if not avg_by_type:
            # Fallback: tutti gli ordini recenti
            general_avg = frappe.db.sql("""
                SELECT AVG(grand_total) as avg_total, COUNT(*) as count
                FROM `tabSales Order`
                WHERE transaction_date >= %s
                AND docstatus = 1
            """, [start_date])[0]
            
            return {
                "value": f"€{flt(general_avg[0] or 0, 0):,.0f}",
                "label": _("Avg Order Value"),
                "subtitle": f"{general_avg[1]} orders (all types)",
                "color": "#27ae60"
            }
        
        # Calcola media ponderata
        total_value = sum(item['total_value'] for item in avg_by_type)
        total_orders = sum(item['orders_count'] for item in avg_by_type)
        overall_avg = total_value / total_orders if total_orders > 0 else 0
        
        # Trova tipo più redditizio
        top_type = max(avg_by_type, key=lambda x: x['avg_total'])
        
        return {
            "value": f"€{flt(overall_avg, 0):,.0f}",
            "label": _("Avg Order Value"),
            "subtitle": f"Best: {top_type['tipo_vendita']} (€{flt(top_type['avg_total'], 0):,.0f})",
            "color": "#27ae60",
            "details": avg_by_type
        }
        
    except Exception as e:
        frappe.logger().error(f"Dashboard error - average_order_value: {e}")
        return {
            "value": "€0",
            "label": _("Avg Order Value"),
            "subtitle": "Error loading data",
            "color": "#95a5a6"
        }

@frappe.whitelist()
def get_iderp_system_health():
    """
    Ottieni stato salute sistema IDERP
    """
    try:
        health_score = 0
        max_score = 100
        issues = []
        
        # Check 1: DocTypes esistenti (25 punti)
        required_doctypes = ["Customer Group Price Rule", "Item Pricing Tier", "Customer Group Minimum"]
        existing_doctypes = sum(1 for dt in required_doctypes if frappe.db.exists("DocType", dt))
        doctype_score = (existing_doctypes / len(required_doctypes)) * 25
        health_score += doctype_score
        
        if existing_doctypes < len(required_doctypes):
            issues.append(f"Missing {len(required_doctypes) - existing_doctypes} DocTypes")
        
        # Check 2: Item configurati (25 punti)
        total_items = frappe.db.count("Item", {"disabled": 0})
        configured_items = frappe.db.count("Item", {"supports_custom_measurement": 1, "disabled": 0})
        
        if total_items > 0:
            item_score = min((configured_items / total_items) * 25, 25)
            health_score += item_score
            
            if configured_items == 0:
                issues.append("No items configured for custom measurements")
            elif configured_items / total_items < 0.1:
                issues.append("Less than 10% of items configured")
        
        # Check 3: Customer Groups attivi (25 punti)
        standard_groups = ["Finale", "Bronze", "Gold", "Diamond"]
        existing_groups = sum(1 for g in standard_groups if frappe.db.exists("Customer Group", g))
        group_score = (existing_groups / len(standard_groups)) * 25
        health_score += group_score
        
        if existing_groups == 0:
            issues.append("No standard customer groups configured")
        
        # Check 4: Regole pricing attive (25 punti)
        active_rules = frappe.db.count("Customer Group Price Rule", {"enabled": 1})
        
        if configured_items > 0:
            expected_rules = configured_items * len(standard_groups)  # Stima
            rule_coverage = min(active_rules / expected_rules, 1) if expected_rules > 0 else 0
            rule_score = rule_coverage * 25
            health_score += rule_score
            
            if active_rules == 0:
                issues.append("No active pricing rules")
        
        # Determina stato
        if health_score >= 80:
            status = "excellent"
            color = "#27ae60"
        elif health_score >= 60:
            status = "good"
            color = "#f39c12"
        elif health_score >= 40:
            status = "fair"
            color = "#e67e22"
        else:
            status = "poor"
            color = "#e74c3c"
        
        return {
            "value": f"{health_score:.0f}%",
            "label": _("System Health"),
            "subtitle": f"Status: {status.title()} ({len(issues)} issues)",
            "color": color,
            "details": {
                "score": health_score,
                "status": status,
                "issues": issues,
                "components": {
                    "doctypes": doctype_score,
                    "items": item_score if 'item_score' in locals() else 0,
                    "groups": group_score,
                    "rules": rule_score if 'rule_score' in locals() else 0
                }
            }
        }
        
    except Exception as e:
        frappe.logger().error(f"Dashboard error - system_health: {e}")
        return {
            "value": "N/A",
            "label": _("System Health"),
            "subtitle": "Error checking health",
            "color": "#95a5a6"
        }

@frappe.whitelist()
def get_monthly_trends():
    """
    Ottieni trend mensili per grafici dashboard
    """
    try:
        # Ultimi 6 mesi
        months_data = []
        
        for i in range(6):
            month_start = add_months(get_first_day(today()), -i)
            month_end = get_last_day(month_start)
            
            # Quotazioni del mese
            quotations = frappe.db.count("Quotation", {
                "transaction_date": ["between", [month_start, month_end]]
            })
            
            # Valore totale
            total_value = frappe.db.sql("""
                SELECT SUM(grand_total) 
                FROM `tabQuotation`
                WHERE transaction_date BETWEEN %s AND %s
                AND docstatus = 1
            """, [month_start, month_end])[0][0] or 0
            
            months_data.append({
                "month": month_start.strftime("%b %Y"),
                "quotations": quotations,
                "value": flt(total_value, 0)
            })
        
        return {
            "success": True,
            "data": list(reversed(months_data))  # Cronologico
        }
        
    except Exception as e:
        frappe.logger().error(f"Dashboard error - monthly_trends: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# Utility functions
def get_dashboard_summary():
    """
    Ottieni riepilogo completo dashboard
    """
    return {
        "quotations": get_quotations_this_month(),
        "customer_groups": get_top_customer_groups(),
        "configured_items": get_configured_items_count(),
        "avg_order_value": get_average_order_value(),
        "system_health": get_iderp_system_health(),
        "trends": get_monthly_trends()
    }

def refresh_dashboard_cache():
    """
    Aggiorna cache dashboard
    """
    cache_keys = [
        "iderp_dashboard_quotations",
        "iderp_dashboard_customer_groups", 
        "iderp_dashboard_items",
        "iderp_dashboard_orders",
        "iderp_dashboard_health"
    ]
    
    for key in cache_keys:
        frappe.cache().delete_value(key)
