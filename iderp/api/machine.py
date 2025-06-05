# iderp/api/machine.py

"""
API per comunicazione con macchine stampa
Sistema produzione IDERP - ERPNext 15
"""

import frappe
from frappe import _
from frappe.utils import flt, cint, now_datetime, getdate
import json
import hashlib
import hmac

@frappe.whitelist(allow_guest=True)
def authenticate_machine():
    """
    Autentica macchina stampa tramite API key
    """
    # Ottieni API key dall'header
    api_key = frappe.get_request_header("X-Machine-API-Key")
    machine_id = frappe.get_request_header("X-Machine-ID")
    
    if not api_key or not machine_id:
        frappe.throw(_("Credenziali macchina mancanti"), frappe.AuthenticationError)
    
    # Verifica macchina
    machine_user = frappe.db.get_value("User", 
        {"machine_id": machine_id, "enabled": 1},
        ["name", "api_key"]
    )
    
    if not machine_user:
        frappe.throw(_("Macchina non registrata"), frappe.AuthenticationError)
    
    # Verifica API key
    if not verify_api_key(api_key, machine_user.api_key):
        frappe.throw(_("API key non valida"), frappe.AuthenticationError)
    
    # Genera token sessione
    session_token = generate_session_token(machine_id)
    
    return {
        "success": True,
        "machine_id": machine_id,
        "session_token": session_token,
        "expires_in": 3600  # 1 ora
    }


def verify_api_key(provided_key, stored_key):
    """
    Verifica API key con timing attack protection
    """
    return hmac.compare_digest(provided_key, stored_key)


def generate_session_token(machine_id):
    """
    Genera token sessione temporaneo
    """
    import secrets
    token = secrets.token_urlsafe(32)
    
    # Salva in cache con TTL
    frappe.cache().set_value(
        f"machine_session_{machine_id}",
        token,
        expires_in_sec=3600
    )
    
    return token


@frappe.whitelist()
def get_pending_jobs(machine_id=None, job_type=None):
    """
    Ottieni lavori in attesa per macchina
    """
    # Verifica autenticazione macchina
    if not verify_machine_session():
        frappe.throw(_("Sessione non valida"), frappe.AuthenticationError)
    
    filters = {
        "status": ["in", ["Open", "Work In Progress"]],
        "docstatus": 1
    }
    
    if machine_id:
        filters["assigned_machine"] = machine_id
    
    if job_type:
        filters["print_type"] = job_type
    
    # Query Work Orders assegnati
    work_orders = frappe.get_all("Work Order",
        filters=filters,
        fields=[
            "name", "production_item", "qty", "produced_qty",
            "planned_start_date", "expected_delivery_date",
            "print_type", "material_width", "material_length",
            "priority", "custom_instructions"
        ],
        order_by="priority desc, planned_start_date asc",
        limit=20
    )
    
    # Aggiungi dettagli item
    for wo in work_orders:
        item_details = get_item_print_details(wo.production_item)
        wo.update(item_details)
        
        # Aggiungi job cards
        wo["job_cards"] = get_work_order_job_cards(wo.name)
    
    return {
        "success": True,
        "count": len(work_orders),
        "jobs": work_orders
    }


def verify_machine_session():
    """
    Verifica sessione macchina attiva
    """
    machine_id = frappe.get_request_header("X-Machine-ID")
    session_token = frappe.get_request_header("X-Session-Token")
    
    if not machine_id or not session_token:
        return False
    
    stored_token = frappe.cache().get_value(f"machine_session_{machine_id}")
    
    return stored_token and hmac.compare_digest(session_token, stored_token)


def get_item_print_details(item_code):
    """
    Ottieni dettagli stampa per articolo
    """
    item = frappe.get_doc("Item", item_code)
    
    details = {
        "item_name": item.item_name,
        "tipo_vendita": item.get("tipo_vendita_default"),
        "supports_custom_measurement": item.get("supports_custom_measurement", 0)
    }
    
    # Aggiungi specifiche tecniche stampa
    if item.get("print_specifications"):
        details["specifications"] = {
            "resolution": item.get("print_resolution"),
            "color_mode": item.get("color_mode"),
            "material_type": item.get("material_type"),
            "finishing": item.get("finishing_type")
        }
    
    return details


def get_work_order_job_cards(work_order):
    """
    Ottieni job cards per work order
    """
    job_cards = frappe.get_all("Job Card",
        filters={
            "work_order": work_order,
            "docstatus": ["!=", 2]
        },
        fields=[
            "name", "operation", "status", 
            "time_logs", "completed_qty"
        ],
        order_by="sequence_id asc"
    )
    
    return job_cards


@frappe.whitelist()
def start_job(job_card_id):
    """
    Inizia lavorazione job
    """
    if not verify_machine_session():
        frappe.throw(_("Sessione non valida"), frappe.AuthenticationError)
    
    machine_id = frappe.get_request_header("X-Machine-ID")
    
    try:
        job_card = frappe.get_doc("Job Card", job_card_id)
        
        # Verifica stato
        if job_card.status != "Open":
            frappe.throw(_("Job già in lavorazione o completato"))
        
        # Inizia time log
        job_card.append("time_logs", {
            "from_time": now_datetime(),
            "employee": get_machine_operator(machine_id),
            "operation": job_card.operation
        })
        
        job_card.status = "Work In Progress"
        job_card.actual_start_time = now_datetime()
        job_card.save()
        
        # Log evento
        log_machine_event(machine_id, "job_started", {
            "job_card": job_card_id,
            "work_order": job_card.work_order
        })
        
        return {
            "success": True,
            "message": _("Job iniziato"),
            "job_card": job_card_id,
            "start_time": job_card.actual_start_time
        }
        
    except Exception as e:
        frappe.log_error(f"Errore start job: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }


@frappe.whitelist()
def update_job_progress(job_card_id, completed_qty, notes=None):
    """
    Aggiorna progresso lavorazione
    """
    if not verify_machine_session():
        frappe.throw(_("Sessione non valida"), frappe.AuthenticationError)
    
    machine_id = frappe.get_request_header("X-Machine-ID")
    
    try:
        job_card = frappe.get_doc("Job Card", job_card_id)
        
        if job_card.status != "Work In Progress":
            frappe.throw(_("Job non in lavorazione"))
        
        # Aggiorna quantità
        job_card.completed_qty = flt(completed_qty)
        
        # Aggiungi note se presenti
        if notes:
            if job_card.remarks:
                job_card.remarks += f"\n{now_datetime()}: {notes}"
            else:
                job_card.remarks = f"{now_datetime()}: {notes}"
        
        job_card.save()
        
        # Log progresso
        log_machine_event(machine_id, "job_progress", {
            "job_card": job_card_id,
            "completed_qty": completed_qty,
            "percentage": (completed_qty / job_card.for_quantity * 100)
        })
        
        return {
            "success": True,
            "completed_qty": completed_qty,
            "remaining_qty": job_card.for_quantity - completed_qty
        }
        
    except Exception as e:
        frappe.log_error(f"Errore update progress: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }


@frappe.whitelist()
def complete_job(job_card_id, final_qty=None, quality_check=None):
    """
    Completa lavorazione job
    """
    if not verify_machine_session():
        frappe.throw(_("Sessione non valida"), frappe.AuthenticationError)
    
    machine_id = frappe.get_request_header("X-Machine-ID")
    
    try:
        job_card = frappe.get_doc("Job Card", job_card_id)
        
        if job_card.status != "Work In Progress":
            frappe.throw(_("Job non in lavorazione"))
        
        # Chiudi time log
        if job_card.time_logs:
            job_card.time_logs[-1].to_time = now_datetime()
        
        # Imposta quantità finale
        if final_qty is not None:
            job_card.completed_qty = flt(final_qty)
        
        # Registra quality check se presente
        if quality_check:
            job_card.quality_inspection = create_quality_inspection(
                job_card, quality_check
            )
        
        job_card.status = "Completed"
        job_card.actual_end_time = now_datetime()
        job_card.save()
        job_card.submit()
        
        # Aggiorna Work Order
        update_work_order_status(job_card.work_order)
        
        # Log completamento
        log_machine_event(machine_id, "job_completed", {
            "job_card": job_card_id,
            "work_order": job_card.work_order,
            "completed_qty": job_card.completed_qty,
            "duration": calculate_job_duration(job_card)
        })
        
        return {
            "success": True,
            "message": _("Job completato"),
            "completed_qty": job_card.completed_qty,
            "duration": calculate_job_duration(job_card)
        }
        
    except Exception as e:
        frappe.log_error(f"Errore complete job: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }


def get_machine_operator(machine_id):
    """
    Ottieni operatore associato a macchina
    """
    return frappe.db.get_value("User", 
        {"machine_id": machine_id}, 
        "name"
    ) or "Administrator"


def create_quality_inspection(job_card, quality_data):
    """
    Crea ispezione qualità per job completato
    """
    # Implementazione base - può essere estesa
    return None


def update_work_order_status(work_order_name):
    """
    Aggiorna stato Work Order basato su Job Cards
    """
    wo = frappe.get_doc("Work Order", work_order_name)
    
    # Conta job cards
    total_cards = frappe.db.count("Job Card", {"work_order": work_order_name})
    completed_cards = frappe.db.count("Job Card", {
        "work_order": work_order_name,
        "status": "Completed"
    })
    
    # Aggiorna quantità prodotta
    produced_qty = frappe.db.sql("""
        SELECT SUM(completed_qty) 
        FROM `tabJob Card`
        WHERE work_order = %s AND status = 'Completed'
    """, work_order_name)[0][0] or 0
    
    wo.produced_qty = produced_qty
    
    # Aggiorna stato
    if completed_cards == total_cards and total_cards > 0:
        wo.status = "Completed"
    elif completed_cards > 0:
        wo.status = "In Process"
    
    wo.save()


def calculate_job_duration(job_card):
    """
    Calcola durata totale lavorazione
    """
    total_minutes = 0
    
    for log in job_card.time_logs:
        if log.from_time and log.to_time:
            duration = log.to_time - log.from_time
            total_minutes += duration.total_seconds() / 60
    
    return round(total_minutes, 2)


def log_machine_event(machine_id, event_type, data):
    """
    Log eventi macchina per tracking
    """
    try:
        frappe.get_doc({
            "doctype": "Machine Event Log",
            "machine_id": machine_id,
            "event_type": event_type,
            "event_data": json.dumps(data),
            "timestamp": now_datetime()
        }).insert(ignore_permissions=True)
    except:
        # Se la tabella log non esiste, ignora
        pass


@frappe.whitelist()
def report_issue(machine_id, issue_type, description, severity="Medium"):
    """
    Segnala problema macchina
    """
    if not verify_machine_session():
        frappe.throw(_("Sessione non valida"), frappe.AuthenticationError)
    
    try:
        # Crea Issue
        issue = frappe.get_doc({
            "doctype": "Issue",
            "subject": f"Problema Macchina: {issue_type}",
            "description": description,
            "priority": severity,
            "issue_type": "Machine Problem",
            "machine_id": machine_id,
            "raised_by": get_machine_operator(machine_id)
        })
        issue.insert()
        
        # Notifica responsabili
        notify_machine_issue(machine_id, issue)
        
        return {
            "success": True,
            "issue_id": issue.name,
            "message": _("Problema segnalato")
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


def notify_machine_issue(machine_id, issue):
    """
    Notifica responsabili produzione
    """
    # Trova responsabili
    recipients = frappe.get_all("User",
        filters={"role": ["in", ["Production Manager", "System Manager"]]},
        pluck="email"
    )
    
    if recipients:
        frappe.sendmail(
            recipients=recipients,
            subject=f"[URGENTE] Problema Macchina {machine_id}",
            message=f"""
            <h3>Segnalazione Problema Macchina</h3>
            <p><strong>Macchina:</strong> {machine_id}</p>
            <p><strong>Problema:</strong> {issue.subject}</p>
            <p><strong>Priorità:</strong> {issue.priority}</p>
            <p><strong>Descrizione:</strong><br>{issue.description}</p>
            <p><a href="{frappe.utils.get_url()}/app/issue/{issue.name}">Visualizza Issue</a></p>
            """
        )


@frappe.whitelist()
def get_machine_status(machine_id):
    """
    Ottieni stato corrente macchina
    """
    if not verify_machine_session():
        frappe.throw(_("Sessione non valida"), frappe.AuthenticationError)
    
    # Job attivo
    active_job = frappe.db.get_value("Job Card",
        {"assigned_machine": machine_id, "status": "Work In Progress"},
        ["name", "work_order", "operation", "completed_qty", "for_quantity"],
        as_dict=True
    )
    
    # Jobs in coda
    pending_jobs = frappe.db.count("Job Card", {
        "assigned_machine": machine_id,
        "status": "Open"
    })
    
    # Statistiche giornaliere
    daily_stats = get_machine_daily_stats(machine_id)
    
    return {
        "machine_id": machine_id,
        "status": "working" if active_job else "idle",
        "active_job": active_job,
        "pending_jobs": pending_jobs,
        "daily_stats": daily_stats
    }


def get_machine_daily_stats(machine_id):
    """
    Statistiche giornaliere macchina
    """
    today = getdate()
    
    completed_jobs = frappe.db.count("Job Card", {
        "assigned_machine": machine_id,
        "status": "Completed",
        "actual_end_time": [">=", today]
    })
    
    total_qty = frappe.db.sql("""
        SELECT SUM(completed_qty)
        FROM `tabJob Card`
        WHERE assigned_machine = %s
        AND status = 'Completed'
        AND DATE(actual_end_time) = %s
    """, (machine_id, today))[0][0] or 0
    
    return {
        "date": today,
        "completed_jobs": completed_jobs,
        "total_quantity": total_qty
    }