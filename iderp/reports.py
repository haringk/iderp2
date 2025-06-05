# iderp/reports.py

"""
Modulo report e analisi iderp
Report settimanali e analisi dati stampa digitale
"""

import frappe
from frappe import _
from frappe.utils import (
    add_days, getdate, get_first_day, get_last_day,
    fmt_money, cint, flt, now_datetime
)
from datetime import datetime, timedelta
import json

def generate_weekly_reports():
    """
    Genera report settimanali automatici
    Schedulato: weekly
    """
    try:
        # Periodo report (settimana precedente)
        end_date = getdate()
        start_date = add_days(end_date, -7)
        
        reports = {
            "period": {
                "start": start_date,
                "end": end_date
            },
            "generated_at": now_datetime(),
            "reports": {}
        }
        
        # 1. Report Vendite
        reports["reports"]["sales"] = generate_sales_report(start_date, end_date)
        
        # 2. Report Produzione
        reports["reports"]["production"] = generate_production_report(start_date, end_date)
        
        # 3. Report Customer Groups
        reports["reports"]["customer_groups"] = generate_customer_group_report(start_date, end_date)
        
        # 4. Report Optional
        reports["reports"]["optionals"] = generate_optional_report(start_date, end_date)
        
        # 5. Report Performance
        reports["reports"]["performance"] = generate_performance_report(start_date, end_date)
        
        # Salva report
        save_weekly_report(reports)
        
        # Invia email ai manager
        send_weekly_report_email(reports)
        
        frappe.log_error(
            f"Report settimanale generato: {start_date} - {end_date}",
            "iderp Weekly Report"
        )
        
    except Exception as e:
        frappe.log_error(
            f"Errore generazione report: {str(e)}",
            "iderp Report Error"
        )


def generate_sales_report(start_date, end_date):
    """
    Report vendite per periodo
    """
    report = {
        "summary": {},
        "by_type": {},
        "by_customer_group": {},
        "top_items": [],
        "trends": {}
    }
    
    # Query vendite totali
    sales_data = frappe.db.sql("""
        SELECT 
            COUNT(DISTINCT q.name) as total_quotations,
            COUNT(DISTINCT so.name) as total_orders,
            SUM(CASE WHEN q.status = 'Ordered' THEN 1 ELSE 0 END) as converted_quotations,
            SUM(so.grand_total) as total_revenue
        FROM `tabQuotation` q
        LEFT JOIN `tabSales Order` so ON so.quotation = q.name
        WHERE q.transaction_date BETWEEN %s AND %s
        AND q.docstatus = 1
    """, (start_date, end_date), as_dict=True)[0]
    
    report["summary"] = {
        "total_quotations": sales_data.total_quotations or 0,
        "total_orders": sales_data.total_orders or 0,
        "conversion_rate": (
            (sales_data.converted_quotations / sales_data.total_quotations * 100)
            if sales_data.total_quotations > 0 else 0
        ),
        "total_revenue": sales_data.total_revenue or 0
    }
    
    # Vendite per tipo
    type_data = frappe.db.sql("""
        SELECT 
            qi.tipo_vendita,
            COUNT(DISTINCT qi.parent) as count,
            SUM(qi.amount) as total,
            SUM(CASE 
                WHEN qi.tipo_vendita = 'Metro Quadrato' THEN qi.mq_calcolati
                WHEN qi.tipo_vendita = 'Metro Lineare' THEN qi.ml_calcolati
                ELSE qi.qty
            END) as quantity
        FROM `tabQuotation Item` qi
        JOIN `tabQuotation` q ON q.name = qi.parent
        WHERE q.transaction_date BETWEEN %s AND %s
        AND q.docstatus = 1
        AND qi.tipo_vendita IS NOT NULL
        GROUP BY qi.tipo_vendita
    """, (start_date, end_date), as_dict=True)
    
    for row in type_data:
        report["by_type"][row.tipo_vendita] = {
            "count": row.count,
            "total": row.total,
            "quantity": row.quantity,
            "unit": get_unit_for_type(row.tipo_vendita)
        }
    
    # Vendite per Customer Group
    group_data = frappe.db.sql("""
        SELECT 
            c.customer_group,
            COUNT(DISTINCT q.name) as count,
            SUM(q.grand_total) as total,
            AVG(q.grand_total) as average
        FROM `tabQuotation` q
        JOIN `tabCustomer` c ON c.name = q.customer
        WHERE q.transaction_date BETWEEN %s AND %s
        AND q.docstatus = 1
        GROUP BY c.customer_group
        ORDER BY total DESC
    """, (start_date, end_date), as_dict=True)
    
    for row in group_data:
        report["by_customer_group"][row.customer_group] = {
            "count": row.count,
            "total": row.total,
            "average": row.average
        }
    
    # Top Items venduti
    top_items = frappe.db.sql("""
        SELECT 
            qi.item_code,
            qi.item_name,
            COUNT(DISTINCT qi.parent) as orders,
            SUM(qi.amount) as revenue,
            SUM(qi.qty) as quantity
        FROM `tabQuotation Item` qi
        JOIN `tabQuotation` q ON q.name = qi.parent
        WHERE q.transaction_date BETWEEN %s AND %s
        AND q.docstatus = 1
        GROUP BY qi.item_code
        ORDER BY revenue DESC
        LIMIT 10
    """, (start_date, end_date), as_dict=True)
    
    report["top_items"] = top_items
    
    return report


def generate_production_report(start_date, end_date):
    """
    Report produzione
    """
    report = {
        "summary": {},
        "by_machine": {},
        "by_operation": {},
        "efficiency": {}
    }
    
    # Summary produzione
    production_data = frappe.db.sql("""
        SELECT 
            COUNT(DISTINCT wo.name) as total_work_orders,
            SUM(wo.qty) as planned_qty,
            SUM(wo.produced_qty) as produced_qty,
            COUNT(DISTINCT jc.name) as total_job_cards,
            SUM(CASE WHEN jc.status = 'Completed' THEN 1 ELSE 0 END) as completed_jobs
        FROM `tabWork Order` wo
        LEFT JOIN `tabJob Card` jc ON jc.work_order = wo.name
        WHERE wo.created_on BETWEEN %s AND %s
    """, (start_date, end_date), as_dict=True)[0]
    
    report["summary"] = {
        "total_work_orders": production_data.total_work_orders or 0,
        "planned_qty": production_data.planned_qty or 0,
        "produced_qty": production_data.produced_qty or 0,
        "completion_rate": (
            (production_data.produced_qty / production_data.planned_qty * 100)
            if production_data.planned_qty > 0 else 0
        ),
        "total_job_cards": production_data.total_job_cards or 0,
        "completed_jobs": production_data.completed_jobs or 0
    }
    
    # Produzione per macchina
    machine_data = frappe.db.sql("""
        SELECT 
            jc.assigned_machine as machine_id,
            COUNT(*) as jobs,
            SUM(jc.completed_qty) as quantity,
            SUM(TIME_TO_SEC(TIMEDIFF(jc.actual_end_time, jc.actual_start_time))/3600) as hours
        FROM `tabJob Card` jc
        WHERE jc.actual_start_time BETWEEN %s AND %s
        AND jc.status = 'Completed'
        GROUP BY jc.assigned_machine
    """, (start_date, end_date), as_dict=True)
    
    for row in machine_data:
        if row.machine_id:
            report["by_machine"][row.machine_id] = {
                "jobs": row.jobs,
                "quantity": row.quantity or 0,
                "hours": round(row.hours or 0, 2),
                "productivity": (row.quantity / row.hours) if row.hours else 0
            }
    
    return report


def generate_customer_group_report(start_date, end_date):
    """
    Report analisi Customer Groups
    """
    report = {
        "summary": {},
        "minimums_impact": {},
        "group_performance": {}
    }
    
    # Impatto minimi
    minimums_data = frappe.db.sql("""
        SELECT 
            c.customer_group,
            COUNT(DISTINCT qi.parent) as affected_quotes,
            SUM(CASE WHEN qi.manual_rate_override = 1 THEN 1 ELSE 0 END) as adjusted_items,
            SUM(CASE WHEN qi.manual_rate_override = 1 THEN qi.amount - (qi.qty * qi.rate) ELSE 0 END) as total_adjustment
        FROM `tabQuotation Item` qi
        JOIN `tabQuotation` q ON q.name = qi.parent
        JOIN `tabCustomer` c ON c.name = q.customer
        WHERE q.transaction_date BETWEEN %s AND %s
        AND q.docstatus = 1
        GROUP BY c.customer_group
    """, (start_date, end_date), as_dict=True)
    
    for row in minimums_data:
        report["minimums_impact"][row.customer_group] = {
            "affected_quotes": row.affected_quotes,
            "adjusted_items": row.adjusted_items or 0,
            "total_adjustment": row.total_adjustment or 0
        }
    
    # Performance per gruppo
    for group in ["Finale", "Bronze", "Gold", "Diamond"]:
        perf_data = frappe.db.sql("""
            SELECT 
                AVG(q.grand_total) as avg_order_value,
                AVG(DATEDIFF(so.delivery_date, so.transaction_date)) as avg_lead_time,
                COUNT(DISTINCT q.customer) as unique_customers
            FROM `tabQuotation` q
            JOIN `tabCustomer` c ON c.name = q.customer
            LEFT JOIN `tabSales Order` so ON so.quotation = q.name
            WHERE c.customer_group = %s
            AND q.transaction_date BETWEEN %s AND %s
            AND q.docstatus = 1
        """, (group, start_date, end_date), as_dict=True)[0]
        
        report["group_performance"][group] = {
            "avg_order_value": perf_data.avg_order_value or 0,
            "avg_lead_time": perf_data.avg_lead_time or 0,
            "unique_customers": perf_data.unique_customers or 0
        }
    
    return report


def generate_optional_report(start_date, end_date):
    """
    Report utilizzo optional
    """
    report = {
        "summary": {},
        "by_optional": {},
        "revenue_impact": 0
    }
    
    # Optional più utilizzati
    optional_data = frappe.db.sql("""
        SELECT 
            sio.optional,
            io.optional_name,
            io.pricing_type,
            COUNT(DISTINCT qi.parent) as usage_count,
            SUM(sio.quantity) as total_quantity,
            SUM(sio.total_price) as total_revenue
        FROM `tabSales Item Optional` sio
        JOIN `tabItem Optional` io ON io.name = sio.optional
        JOIN `tabQuotation Item` qi ON qi.name = sio.parent
        JOIN `tabQuotation` q ON q.name = qi.parent
        WHERE q.transaction_date BETWEEN %s AND %s
        AND q.docstatus = 1
        GROUP BY sio.optional
        ORDER BY total_revenue DESC
    """, (start_date, end_date), as_dict=True)
    
    total_optional_revenue = 0
    
    for row in optional_data:
        report["by_optional"][row.optional] = {
            "name": row.optional_name,
            "pricing_type": row.pricing_type,
            "usage_count": row.usage_count,
            "total_quantity": row.total_quantity,
            "total_revenue": row.total_revenue,
            "avg_revenue_per_use": row.total_revenue / row.usage_count if row.usage_count else 0
        }
        total_optional_revenue += row.total_revenue or 0
    
    report["revenue_impact"] = total_optional_revenue
    
    # Summary
    report["summary"] = {
        "total_optional_revenue": total_optional_revenue,
        "unique_optionals_used": len(optional_data),
        "most_popular": optional_data[0]["optional_name"] if optional_data else None,
        "highest_revenue": optional_data[0]["total_revenue"] if optional_data else 0
    }
    
    return report


def generate_performance_report(start_date, end_date):
    """
    Report performance sistema
    """
    report = {
        "system_health": {},
        "calculation_stats": {},
        "error_summary": {}
    }
    
    # Health check
    from iderp.maintenance import get_system_health
    report["system_health"] = get_system_health()
    
    # Statistiche calcoli
    calc_stats = frappe.db.sql("""
        SELECT 
            COUNT(*) as total_calculations,
            AVG(TIME_TO_SEC(TIMEDIFF(modified, creation))) as avg_processing_time
        FROM `tabQuotation`
        WHERE transaction_date BETWEEN %s AND %s
        AND docstatus = 1
    """, (start_date, end_date), as_dict=True)[0]
    
    report["calculation_stats"] = {
        "total_calculations": calc_stats.total_calculations or 0,
        "avg_processing_time": round(calc_stats.avg_processing_time or 0, 2)
    }
    
    # Errori
    errors = frappe.db.sql("""
        SELECT 
            method,
            COUNT(*) as count
        FROM `tabError Log`
        WHERE method LIKE '%iderp%'
        AND creation BETWEEN %s AND %s
        GROUP BY method
        ORDER BY count DESC
        LIMIT 10
    """, (start_date, end_date), as_dict=True)
    
    report["error_summary"] = {
        "total_errors": sum(e.count for e in errors),
        "by_method": {e.method: e.count for e in errors}
    }
    
    return report


def get_unit_for_type(tipo_vendita):
    """
    Ottieni unità di misura per tipo vendita
    """
    units = {
        "Metro Quadrato": "m²",
        "Metro Lineare": "ml",
        "Pezzo": "pz"
    }
    return units.get(tipo_vendita, "")


def save_weekly_report(reports):
    """
    Salva report in database
    """
    try:
        # Crea documento Report Log (se esiste il DocType)
        if frappe.db.exists("DocType", "iderp Report Log"):
            report_doc = frappe.get_doc({
                "doctype": "iderp Report Log",
                "report_type": "Weekly Summary",
                "period_start": reports["period"]["start"],
                "period_end": reports["period"]["end"],
                "report_data": json.dumps(reports["reports"]),
                "generated_on": reports["generated_at"]
            })
            report_doc.insert(ignore_permissions=True)
        
        # Salva anche come file
        file_path = frappe.get_site_path(
            "private/files/iderp_reports",
            f"weekly_report_{reports['period']['start']}_{reports['period']['end']}.json"
        )
        
        import os
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(reports, f, indent=2, default=str)
            
    except Exception as e:
        frappe.log_error(f"Errore salvataggio report: {str(e)}")


def send_weekly_report_email(reports):
    """
    Invia report via email ai manager
    """
    try:
        # Trova destinatari
        recipients = frappe.get_all("User",
            filters={
                "role": ["in", ["Sales Manager", "System Manager"]],
                "enabled": 1
            },
            pluck="email"
        )
        
        if not recipients:
            return
        
        # Genera HTML report
        html_content = generate_html_report(reports)
        
        # Invia email
        frappe.sendmail(
            recipients=recipients,
            subject=f"iderp Report Settimanale - {reports['period']['start']} / {reports['period']['end']}",
            message=html_content,
            delayed=False
        )
        
    except Exception as e:
        frappe.log_error(f"Errore invio email report: {str(e)}")


def generate_html_report(reports):
    """
    Genera HTML per email report
    """
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .header {{ background-color: #f8f9fa; padding: 20px; }}
            .section {{ margin: 20px 0; padding: 15px; border: 1px solid #dee2e6; }}
            .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #e9ecef; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
            .positive {{ color: #28a745; }}
            .negative {{ color: #dc3545; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>iderp Report Settimanale</h1>
            <p>Periodo: {reports['period']['start']} - {reports['period']['end']}</p>
        </div>
    """
    
    # Sezione Vendite
    if "sales" in reports["reports"]:
        sales = reports["reports"]["sales"]["summary"]
        html += f"""
        <div class="section">
            <h2>📊 Vendite</h2>
            <div class="metric">
                <strong>Preventivi:</strong> {sales['total_quotations']}
            </div>
            <div class="metric">
                <strong>Ordini:</strong> {sales['total_orders']}
            </div>
            <div class="metric">
                <strong>Conversione:</strong> {sales['conversion_rate']:.1f}%
            </div>
            <div class="metric">
                <strong>Fatturato:</strong> €{sales['total_revenue']:,.2f}
            </div>
        </div>
        """
    
    # Sezione Produzione
    if "production" in reports["reports"]:
        prod = reports["reports"]["production"]["summary"]
        html += f"""
        <div class="section">
            <h2>🏭 Produzione</h2>
            <div class="metric">
                <strong>Work Orders:</strong> {prod['total_work_orders']}
            </div>
            <div class="metric">
                <strong>Completamento:</strong> {prod['completion_rate']:.1f}%
            </div>
            <div class="metric">
                <strong>Job Completati:</strong> {prod['completed_jobs']}/{prod['total_job_cards']}
            </div>
        </div>
        """
    
    # Sezione Optional
    if "optionals" in reports["reports"]:
        opt = reports["reports"]["optionals"]["summary"]
        html += f"""
        <div class="section">
            <h2>🎨 Optional</h2>
            <div class="metric">
                <strong>Fatturato Optional:</strong> €{opt['total_optional_revenue']:,.2f}
            </div>
            <div class="metric">
                <strong>Più Popolare:</strong> {opt['most_popular'] or 'N/A'}
            </div>
        </div>
        """
    
    html += """
    </body>
    </html>
    """
    
    return html


@frappe.whitelist()
def get_custom_report(report_type, start_date=None, end_date=None):
    """
    API per generare report custom on-demand
    """
    if not frappe.has_permission("Sales Manager"):
        frappe.throw(_("Permesso negato"))
    
    if not start_date:
        start_date = get_first_day(getdate())
    if not end_date:
        end_date = getdate()
    
    if report_type == "sales":
        return generate_sales_report(start_date, end_date)
    elif report_type == "production":
        return generate_production_report(start_date, end_date)
    elif report_type == "customer_groups":
        return generate_customer_group_report(start_date, end_date)
    elif report_type == "optionals":
        return generate_optional_report(start_date, end_date)
    elif report_type == "performance":
        return generate_performance_report(start_date, end_date)
    else:
        frappe.throw(_("Tipo report non valido"))


@frappe.whitelist()
def get_report_list():
    """
    Lista report disponibili
    """
    return [
        {
            "name": "sales",
            "title": _("Report Vendite"),
            "description": _("Analisi vendite per periodo")
        },
        {
            "name": "production",
            "title": _("Report Produzione"),
            "description": _("Statistiche produzione e macchine")
        },
        {
            "name": "customer_groups",
            "title": _("Report Gruppi Cliente"),
            "description": _("Performance per gruppo cliente")
        },
        {
            "name": "optionals",
            "title": _("Report Optional"),
            "description": _("Utilizzo optional e fatturato")
        },
        {
            "name": "performance",
            "title": _("Report Performance"),
            "description": _("Performance sistema iderp")
        }
    ]
