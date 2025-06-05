# iderp/maintenance.py

"""
Modulo manutenzione e pulizia sistema IDERP
Funzioni schedulabili per ottimizzazione performance
"""

import frappe
from frappe import _
from frappe.utils import add_days, now_datetime, getdate
import json

def cleanup_old_calculations():
    """
    Pulisce calcoli vecchi non più necessari
    Schedulato: daily
    """
    try:
        # Pulisci log calcoli più vecchi di 30 giorni
        cleanup_date = add_days(now_datetime(), -30)
        
        # Pulisci note di calcolo vecchie
        frappe.db.sql("""
            UPDATE `tabQuotation Item`
            SET note_calcolo = NULL
            WHERE modified < %s
            AND note_calcolo IS NOT NULL
            AND parent IN (
                SELECT name FROM `tabQuotation`
                WHERE docstatus = 2
                OR status = 'Cancelled'
            )
        """, cleanup_date)
        
        # Pulisci anche da Sales Order cancellati
        frappe.db.sql("""
            UPDATE `tabSales Order Item`
            SET note_calcolo = NULL
            WHERE modified < %s
            AND note_calcolo IS NOT NULL
            AND parent IN (
                SELECT name FROM `tabSales Order`
                WHERE docstatus = 2
                OR status = 'Cancelled'
            )
        """, cleanup_date)
        
        # Commit modifiche
        frappe.db.commit()
        
        # Log operazione
        frappe.log_error(
            "Pulizia calcoli completata",
            "IDERP Maintenance"
        )
        
    except Exception as e:
        frappe.log_error(
            f"Errore pulizia calcoli: {str(e)}",
            "IDERP Maintenance Error"
        )


def cleanup_cache():
    """
    Pulisce cache IDERP
    Schedulato: weekly
    """
    try:
        # Lista chiavi cache IDERP
        cache_keys = [
            "iderp_customer_pricing_cache",
            "iderp_item_tiers_cache",
            "iderp_customer_minimums_cache",
            "iderp_optional_cache"
        ]
        
        cleared_count = 0
        
        # Pulisci cache keys
        for key in cache_keys:
            # Pulisci tutte le varianti della chiave
            for i in range(100):  # Assumendo max 100 varianti
                full_key = f"{key}_{i}"
                if frappe.cache().exists(full_key):
                    frappe.cache().delete_value(full_key)
                    cleared_count += 1
            
            # Pulisci chiave base
            if frappe.cache().exists(key):
                frappe.cache().delete_value(key)
                cleared_count += 1
        
        # Pulisci cache documenti modificati
        cleanup_document_cache()
        
        # Log operazione
        frappe.log_error(
            f"Cache pulita: {cleared_count} chiavi rimosse",
            "IDERP Cache Cleanup"
        )
        
    except Exception as e:
        frappe.log_error(
            f"Errore pulizia cache: {str(e)}",
            "IDERP Cache Error"
        )


def cleanup_document_cache():
    """
    Pulisce cache documenti IDERP
    """
    # Pulisci cache per Item con misure personalizzate
    items = frappe.get_all("Item", 
        filters={"supports_custom_measurement": 1},
        fields=["name"]
    )
    
    for item in items:
        cache_key = f"iderp_item_config_{item.name}"
        frappe.cache().delete_value(cache_key)


def optimize_database_tables():
    """
    Ottimizza tabelle database IDERP
    Schedulato: monthly (da aggiungere a hooks se necessario)
    """
    try:
        tables_to_optimize = [
            "tabItem Pricing Tier",
            "tabCustomer Group Price Rule",
            "tabCustomer Group Minimum",
            "tabItem Optional",
            "tabOptional Template",
            "tabSales Item Optional"
        ]
        
        for table in tables_to_optimize:
            try:
                frappe.db.sql(f"OPTIMIZE TABLE `{table}`")
            except Exception:
                # Alcune tabelle potrebbero non esistere
                pass
        
        frappe.db.commit()
        
        frappe.log_error(
            "Ottimizzazione tabelle completata",
            "IDERP Database Optimization"
        )
        
    except Exception as e:
        frappe.log_error(
            f"Errore ottimizzazione DB: {str(e)}",
            "IDERP DB Error"
        )


def cleanup_orphaned_child_records():
    """
    Rimuove record child orfani
    """
    try:
        # Pulisci Item Pricing Tier orfani
        frappe.db.sql("""
            DELETE FROM `tabItem Pricing Tier`
            WHERE parent NOT IN (
                SELECT name FROM `tabItem`
            )
        """)
        
        # Pulisci Customer Group Minimum orfani
        frappe.db.sql("""
            DELETE FROM `tabCustomer Group Minimum`
            WHERE parent NOT IN (
                SELECT name FROM `tabItem`
            )
        """)
        
        # Pulisci Sales Item Optional orfani
        frappe.db.sql("""
            DELETE FROM `tabSales Item Optional`
            WHERE parenttype = 'Quotation Item'
            AND parent NOT IN (
                SELECT name FROM `tabQuotation Item`
            )
        """)
        
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(
            f"Errore pulizia record orfani: {str(e)}",
            "IDERP Cleanup Error"
        )


def validate_system_integrity():
    """
    Valida integrità sistema IDERP
    """
    issues = []
    
    try:
        # Check 1: Verifica Items con configurazioni incomplete
        incomplete_items = frappe.db.sql("""
            SELECT name 
            FROM `tabItem`
            WHERE supports_custom_measurement = 1
            AND (tipo_vendita_default IS NULL OR tipo_vendita_default = '')
        """, as_dict=True)
        
        if incomplete_items:
            issues.append({
                "type": "warning",
                "message": f"{len(incomplete_items)} articoli con configurazione incompleta"
            })
        
        # Check 2: Verifica Customer Groups standard
        required_groups = ["Finale", "Bronze", "Gold", "Diamond"]
        missing_groups = []
        
        for group in required_groups:
            if not frappe.db.exists("Customer Group", group):
                missing_groups.append(group)
        
        if missing_groups:
            issues.append({
                "type": "error",
                "message": f"Gruppi cliente mancanti: {', '.join(missing_groups)}"
            })
        
        # Check 3: Verifica scaglioni prezzo validi
        invalid_tiers = frappe.db.sql("""
            SELECT parent, COUNT(*) as count
            FROM `tabItem Pricing Tier`
            WHERE from_qty > IFNULL(to_qty, 999999)
            GROUP BY parent
        """, as_dict=True)
        
        if invalid_tiers:
            issues.append({
                "type": "error", 
                "message": f"{len(invalid_tiers)} articoli con scaglioni prezzo non validi"
            })
        
        # Check 4: Verifica optional orfani
        orphan_optionals = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabSales Item Optional` sio
            WHERE NOT EXISTS (
                SELECT 1 FROM `tabItem Optional` io
                WHERE io.name = sio.optional
            )
        """, as_dict=True)
        
        if orphan_optionals and orphan_optionals[0]['count'] > 0:
            issues.append({
                "type": "warning",
                "message": f"{orphan_optionals[0]['count']} optional orfani nei documenti"
            })
        
        # Report risultati
        if issues:
            report_content = "REPORT INTEGRITÀ SISTEMA IDERP\n" + "="*50 + "\n"
            for issue in issues:
                report_content += f"\n[{issue['type'].upper()}] {issue['message']}"
            
            frappe.log_error(
                report_content,
                "IDERP System Integrity Check"
            )
        
        return issues
        
    except Exception as e:
        frappe.log_error(
            f"Errore validazione sistema: {str(e)}",
            "IDERP Validation Error"
        )
        return [{"type": "error", "message": str(e)}]


@frappe.whitelist()
def run_maintenance_now(task=None):
    """
    Esegue task di manutenzione manualmente
    """
    if not frappe.has_permission("System Manager"):
        frappe.throw(_("Solo System Manager può eseguire manutenzione"))
    
    results = {}
    
    if not task or task == "cleanup_calculations":
        cleanup_old_calculations()
        results["cleanup_calculations"] = "Completato"
    
    if not task or task == "cleanup_cache":
        cleanup_cache()
        results["cleanup_cache"] = "Completato"
    
    if not task or task == "optimize_database":
        optimize_database_tables()
        results["optimize_database"] = "Completato"
    
    if not task or task == "cleanup_orphans":
        cleanup_orphaned_child_records()
        results["cleanup_orphans"] = "Completato"
    
    if not task or task == "validate_integrity":
        issues = validate_system_integrity()
        results["validate_integrity"] = {
            "completed": True,
            "issues_found": len(issues),
            "issues": issues
        }
    
    return {
        "success": True,
        "results": results,
        "message": _("Manutenzione completata")
    }


@frappe.whitelist()
def get_system_health():
    """
    Ottieni stato salute sistema IDERP
    """
    health_data = {
        "status": "healthy",
        "checks": {}
    }
    
    try:
        # Check 1: Items configurati
        configured_items = frappe.db.count("Item", {"supports_custom_measurement": 1})
        health_data["checks"]["configured_items"] = {
            "value": configured_items,
            "status": "ok" if configured_items > 0 else "warning"
        }
        
        # Check 2: Customer Groups
        customer_groups = frappe.db.count("Customer Group", 
            {"name": ["in", ["Finale", "Bronze", "Gold", "Diamond"]]})
        health_data["checks"]["customer_groups"] = {
            "value": customer_groups,
            "status": "ok" if customer_groups == 4 else "error"
        }
        
        # Check 3: Cache size
        cache_size = get_cache_size()
        health_data["checks"]["cache_size"] = {
            "value": cache_size,
            "status": "ok" if cache_size < 1000 else "warning"
        }
        
        # Check 4: Ultimi errori
        recent_errors = frappe.db.count("Error Log", {
            "method": ["like", "%iderp%"],
            "creation": [">", add_days(now_datetime(), -1)]
        })
        health_data["checks"]["recent_errors"] = {
            "value": recent_errors,
            "status": "ok" if recent_errors < 10 else "error"
        }
        
        # Determina stato generale
        if any(check["status"] == "error" for check in health_data["checks"].values()):
            health_data["status"] = "error"
        elif any(check["status"] == "warning" for check in health_data["checks"].values()):
            health_data["status"] = "warning"
        
    except Exception as e:
        health_data["status"] = "error"
        health_data["error"] = str(e)
    
    return health_data


def get_cache_size():
    """
    Stima dimensione cache IDERP
    """
    # Implementazione semplificata
    # In produzione potrebbe usare Redis INFO
    return frappe.cache().get("iderp_cache_size") or 0


def archive_old_quotations():
    """
    Archivia preventivi vecchi (opzionale)
    """
    # Implementazione futura se necessaria
    pass
