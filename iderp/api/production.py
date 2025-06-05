# -*- coding: utf-8 -*-
# Copyright (c) 2024, ID Studio and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate
from typing import Dict, List


@frappe.whitelist()
def get_order_production_status(sales_order: str) -> Dict:
    """
    Recupera stato produzione per un ordine di vendita
    
    Args:
        sales_order: Nome ordine di vendita
        
    Returns:
        dict: Stato produzione dettagliato
    """
    if not sales_order or not frappe.db.exists("Sales Order", sales_order):
        return {}
        
    # Recupera dettagli ordine
    so = frappe.get_doc("Sales Order", sales_order)
    
    status = {
        "sales_order": sales_order,
        "customer": so.customer,
        "delivery_date": so.delivery_date,
        "items": [],
        "overall_progress": 0,
        "production_status": "Not Started"
    }
    
    total_qty = 0
    total_produced = 0
    
    # Analizza ogni articolo
    for item in so.items:
        item_status = {
            "item_code": item.item_code,
            "item_name": item.item_name,
            "qty": item.qty,
            "uom": item.uom,
            "base": item.get("base", 0),
            "altezza": item.get("altezza", 0),
            "mq_totali": item.get("mq_totali", 0),
            "work_orders": [],
            "produced_qty": 0,
            "pending_qty": item.qty,
            "progress": 0
        }
        
        # Cerca ordini di lavoro correlati
        work_orders = frappe.db.sql("""
            SELECT 
                wo.name,
                wo.production_item,
                wo.qty,
                wo.produced_qty,
                wo.status,
                wo.planned_start_date,
                wo.planned_end_date
            FROM `tabWork Order` wo
            WHERE wo.sales_order = %s
            AND wo.production_item = %s
            AND wo.docstatus = 1
        """, (sales_order, item.item_code), as_dict=True)
        
        for wo in work_orders:
            item_status["work_orders"].append({
                "name": wo.name,
                "qty": wo.qty,
                "produced_qty": wo.produced_qty,
                "status": wo.status,
                "planned_start": wo.planned_start_date,
                "planned_end": wo.planned_end_date,
                "progress": (wo.produced_qty / wo.qty * 100) if wo.qty > 0 else 0
            })
            
            item_status["produced_qty"] += wo.produced_qty
            
        # Calcola progresso articolo
        if item.qty > 0:
            item_status["progress"] = (item_status["produced_qty"] / item.qty) * 100
            item_status["pending_qty"] = item.qty - item_status["produced_qty"]
            
        # Aggiungi a totali
        total_qty += item.qty
        total_produced += item_status["produced_qty"]
        
        status["items"].append(item_status)
    
    # Calcola progresso complessivo
    if total_qty > 0:
        status["overall_progress"] = (total_produced / total_qty) * 100
        
    # Determina stato produzione
    if status["overall_progress"] == 0:
        status["production_status"] = "Non Iniziata"
    elif status["overall_progress"] < 100:
        status["production_status"] = "In Corso"
    else:
        status["production_status"] = "Completata"
        
    # Aggiungi info consegne
    status["deliveries"] = get_order_deliveries(sales_order)
    
    return status


def get_order_deliveries(sales_order: str) -> List[Dict]:
    """Recupera consegne associate all'ordine"""
    
    deliveries = frappe.db.sql("""
        SELECT 
            dn.name,
            dn.posting_date,
            dn.customer,
            dn.status,
            SUM(dni.qty) as total_qty
        FROM `tabDelivery Note` dn
        INNER JOIN `tabDelivery Note Item` dni ON dni.parent = dn.name
        WHERE dni.against_sales_order = %s
        AND dn.docstatus = 1
        GROUP BY dn.name
        ORDER BY dn.posting_date DESC
    """, sales_order, as_dict=True)
    
    return deliveries


@frappe.whitelist()
def get_production_planning_data(
    from_date: str = None,
    to_date: str = None,
    item_code: str = None
) -> Dict:
    """
    Recupera dati pianificazione produzione
    
    Args:
        from_date: Data inizio periodo
        to_date: Data fine periodo
        item_code: Filtro per articolo specifico
        
    Returns:
        dict: Dati pianificazione
    """
    from_date = getdate(from_date or nowdate())
    to_date = getdate(to_date or frappe.utils.add_days(nowdate(), 30))
    
    conditions = ["so.delivery_date BETWEEN %(from_date)s AND %(to_date)s"]
    params = {
        "from_date": from_date,
        "to_date": to_date
    }
    
    if item_code:
        conditions.append("soi.item_code = %(item_code)s")
        params["item_code"] = item_code
        
    # Recupera ordini da produrre
    orders = frappe.db.sql(f"""
        SELECT 
            so.name as sales_order,
            so.customer,
            so.delivery_date,
            soi.item_code,
            soi.item_name,
            soi.qty,
            soi.uom,
            soi.base,
            soi.altezza,
            soi.mq_totali,
            COALESCE(wo_summary.planned_qty, 0) as planned_qty,
            COALESCE(wo_summary.produced_qty, 0) as produced_qty
        FROM `tabSales Order` so
        INNER JOIN `tabSales Order Item` soi ON soi.parent = so.name
        LEFT JOIN (
            SELECT 
                sales_order,
                production_item,
                SUM(qty) as planned_qty,
                SUM(produced_qty) as produced_qty
            FROM `tabWork Order`
            WHERE docstatus = 1
            GROUP BY sales_order, production_item
        ) wo_summary ON wo_summary.sales_order = so.name 
            AND wo_summary.production_item = soi.item_code
        WHERE so.docstatus = 1
        AND so.status NOT IN ('Completed', 'Cancelled')
        AND {' AND '.join(conditions)}
        ORDER BY so.delivery_date, so.name
    """, params, as_dict=True)
    
    # Raggruppa per data consegna
    planning_data = {}
    
    for order in orders:
        date_key = str(order.delivery_date)
        
        if date_key not in planning_data:
            planning_data[date_key] = {
                "date": order.delivery_date,
                "orders": [],
                "total_qty": 0,
                "total_mq": 0,
                "total_pending": 0
            }
            
        # Calcola quantità pendente
        pending_qty = order.qty - order.produced_qty
        
        planning_data[date_key]["orders"].append({
            "sales_order": order.sales_order,
            "customer": order.customer,
            "item_code": order.item_code,
            "item_name": order.item_name,
            "qty": order.qty,
            "uom": order.uom,
            "mq_totali": order.mq_totali or 0,
            "produced_qty": order.produced_qty,
            "pending_qty": pending_qty,
            "progress": (order.produced_qty / order.qty * 100) if order.qty > 0 else 0
        })
        
        planning_data[date_key]["total_qty"] += order.qty
        planning_data[date_key]["total_mq"] += order.mq_totali or 0
        planning_data[date_key]["total_pending"] += pending_qty
    
    # Converti in lista ordinata
    result = {
        "from_date": from_date,
        "to_date": to_date,
        "planning": sorted(planning_data.values(), key=lambda x: x["date"])
    }
    
    # Aggiungi riepilogo
    result["summary"] = {
        "total_orders": len(orders),
        "total_qty": sum(o.qty for o in orders),
        "total_mq": sum(o.mq_totali or 0 for o in orders),
        "total_pending": sum(o.qty - o.produced_qty for o in orders)
    }
    
    return result


@frappe.whitelist()
def create_work_order_from_sales_order(
    sales_order: str,
    item_code: str,
    qty: float = None
) -> str:
    """
    Crea ordine di lavoro da ordine di vendita
    
    Args:
        sales_order: Ordine di vendita
        item_code: Codice articolo
        qty: Quantità (opzionale, usa quella dell'ordine)
        
    Returns:
        str: Nome ordine di lavoro creato
    """
    if not frappe.has_permission("Work Order", "create"):
        frappe.throw(_("Permessi insufficienti per creare ordini di lavoro"))
        
    # Recupera dettagli ordine
    so_item = frappe.db.get_value(
        "Sales Order Item",
        {
            "parent": sales_order,
            "item_code": item_code
        },
        ["qty", "delivery_date", "base", "altezza", "mq_totali"],
        as_dict=True
    )
    
    if not so_item:
        frappe.throw(_("Articolo {0} non trovato nell'ordine {1}").format(
            item_code, sales_order
        ))
        
    # Verifica se l'articolo ha una distinta base
    bom = frappe.db.get_value("BOM", {
        "item": item_code,
        "is_active": 1,
        "is_default": 1
    })
    
    if not bom:
        frappe.throw(_("Nessuna distinta base attiva per {0}").format(item_code))
        
    # Quantità da produrre
    qty_to_produce = qty or so_item.qty
    
    # Crea ordine di lavoro
    wo = frappe.get_doc({
        "doctype": "Work Order",
        "production_item": item_code,
        "bom_no": bom,
        "qty": qty_to_produce,
        "sales_order": sales_order,
        "planned_start_date": nowdate(),
        "expected_delivery_date": so_item.delivery_date,
        "description": f"Produzione per ordine {sales_order}"
    })
    
    # Aggiungi info metrature se presenti
    if so_item.base and so_item.altezza:
        wo.description += f"\nDimensioni: {so_item.base}mm x {so_item.altezza}mm"
        if so_item.mq_totali:
            wo.description += f" ({so_item.mq_totali} mq)"
            
    wo.insert()
    wo.submit()
    
    frappe.msgprint(
        _("Creato ordine di lavoro {0}").format(
            frappe.utils.get_link_to_form("Work Order", wo.name)
        ),
        indicator="green"
    )
    
    return wo.name
