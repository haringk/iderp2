# iderp/global_minimums.py

"""
Modulo per gestione minimi globali per preventivo
Sistema stampa digitale IDERP - ERPNext 15
Implementa logica minimi aggregati invece che per riga
"""

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import cint, flt


def apply_global_minimums_server_side(doc, method=None):
    """
    Applica minimi globali aggregando per item_code + customer_group
    Hook chiamato su before_save
    """
    if not doc.customer:
        return

    # Ottieni gruppo cliente
    customer_group = frappe.db.get_value("Customer", doc.customer, "customer_group")
    if not customer_group:
        return

    # Verifica se usare minimi globali (configurabile)
    use_global_minimums = (
        frappe.db.get_single_value("Selling Settings", "use_global_minimums") or True
    )

    if not use_global_minimums:
        # Usa logica standard per riga
        return apply_per_row_minimums(doc, customer_group)

    # Logica minimi globali
    apply_aggregated_minimums(doc, customer_group)


def apply_aggregated_minimums(doc, customer_group):
    """
    Applica minimi aggregando righe stesso articolo
    """
    # Raggruppa righe per item_code + tipo_vendita
    item_groups = defaultdict(list)

    for item in doc.items:
        if not getattr(item, "supports_custom_measurement", False):
            continue

        tipo_vendita = getattr(item, "tipo_vendita", "Pezzo")
        key = (item.item_code, tipo_vendita)
        item_groups[key].append(item)

    # Applica minimi per gruppo
    total_adjustments = 0

    for (item_code, tipo_vendita), items in item_groups.items():
        adjustment = calculate_group_minimum(items, item_code, tipo_vendita, customer_group)

        if adjustment > 0:
            # Distribuisci adjustment proporzionalmente
            distribute_adjustment(items, adjustment)
            total_adjustments += adjustment

    # Aggiorna note documento
    if total_adjustments > 0:
        update_document_notes(doc, item_groups, customer_group)


def calculate_group_minimum(items, item_code, tipo_vendita, customer_group):
    """
    Calcola minimo per gruppo di righe stesso articolo
    """
    # Ottieni configurazione minimi
    minimum_config = get_minimum_config(item_code, tipo_vendita, customer_group)

    if not minimum_config:
        return 0

    # Calcola totali gruppo
    if tipo_vendita == "Metro Quadrato":
        total_qty = sum(flt(item.mq_calcolati) for item in items)
        min_qty = flt(minimum_config.get("min_sqm", 0))

    elif tipo_vendita == "Metro Lineare":
        total_qty = sum(flt(item.ml_calcolati) for item in items)
        min_qty = flt(minimum_config.get("min_ml", 0))

    elif tipo_vendita == "Pezzo":
        total_qty = sum(flt(item.qty) for item in items)
        min_qty = flt(minimum_config.get("min_pcs", 0))

    else:
        return 0

    # Se sotto il minimo, calcola adjustment
    if total_qty < min_qty and total_qty > 0:
        # Calcola prezzo medio ponderato
        weighted_price = calculate_weighted_average_price(items, tipo_vendita)

        # Calcola valore adjustment
        qty_diff = min_qty - total_qty
        adjustment = qty_diff * weighted_price

        # Aggiungi costo setup se configurato
        setup_cost = flt(minimum_config.get("setup_cost", 0))
        if setup_cost > 0 and minimum_config.get("apply_setup_once", True):
            adjustment += setup_cost

        return adjustment

    return 0


def get_minimum_config(item_code, tipo_vendita, customer_group):
    """
    Ottieni configurazione minimo per item/gruppo
    """
    # Prima cerca configurazione specifica
    config = frappe.db.get_value(
        "Customer Group Minimum",
        {
            "parent": item_code,
            "customer_group": customer_group,
            "selling_type": tipo_vendita,
            "enabled": 1,
        },
        ["min_qty", "setup_cost", "apply_per_row", "notes"],
        as_dict=True,
    )

    if config:
        # Mappa min_qty al campo corretto
        if tipo_vendita == "Metro Quadrato":
            config["min_sqm"] = config["min_qty"]
        elif tipo_vendita == "Metro Lineare":
            config["min_ml"] = config["min_qty"]
        elif tipo_vendita == "Pezzo":
            config["min_pcs"] = config["min_qty"]

        config["apply_setup_once"] = not config.get("apply_per_row", False)

        return config

    # Fallback a Customer Group Price Rule per compatibilità
    rule = frappe.db.get_value(
        "Customer Group Price Rule",
        {
            "customer_group": customer_group,
            "item_code": item_code,
            "enabled": 1,
            "selling_type": tipo_vendita,
        },
        ["min_qty", "setup_cost"],
        as_dict=True,
    )

    if rule:
        if tipo_vendita == "Metro Quadrato":
            return {
                "min_sqm": rule["min_qty"],
                "setup_cost": rule.get("setup_cost", 0),
                "apply_setup_once": True,
            }

    return None


def calculate_weighted_average_price(items, tipo_vendita):
    """
    Calcola prezzo medio ponderato del gruppo
    """
    total_value = 0
    total_qty = 0

    for item in items:
        if tipo_vendita == "Metro Quadrato":
            qty = flt(item.mq_calcolati)
            price = flt(item.prezzo_mq) or (flt(item.rate) / qty if qty > 0 else 0)

        elif tipo_vendita == "Metro Lineare":
            qty = flt(item.ml_calcolati)
            price = flt(item.prezzo_ml) or (flt(item.rate) / qty if qty > 0 else 0)

        else:
            qty = flt(item.qty)
            price = flt(item.rate)

        total_value += price * qty
        total_qty += qty

    return total_value / total_qty if total_qty > 0 else 0


def distribute_adjustment(items, adjustment):
    """
    Distribuisci adjustment proporzionalmente sulle righe
    """
    # Calcola valore totale gruppo
    total_value = sum(flt(item.amount) for item in items)

    if total_value == 0:
        # Distribuisci equamente
        adj_per_item = adjustment / len(items)
        for item in items:
            apply_adjustment_to_item(item, adj_per_item)
    else:
        # Distribuisci proporzionalmente
        remaining = adjustment
        for i, item in enumerate(items):
            if i == len(items) - 1:
                # Ultima riga prende il resto (per arrotondamenti)
                item_adj = remaining
            else:
                proportion = flt(item.amount) / total_value
                item_adj = adjustment * proportion
                remaining -= item_adj

            apply_adjustment_to_item(item, item_adj)


def apply_adjustment_to_item(item, adjustment):
    """
    Applica adjustment a singola riga
    """
    if adjustment <= 0:
        return

    # Salva valore originale della riga
    original_amount = flt(item.amount)

    # Calcola nuovo amount
    new_amount = original_amount + adjustment

    # Ricalcola rate basato su quantità
    if flt(item.qty) > 0:
        item.rate = new_amount / flt(item.qty)

    item.amount = new_amount

    # Aggiorna flag e note
    item.manual_rate_override = 1
    item.auto_calculated = 0

    # Aggiungi nota calcolo
    note = f"Minimo globale applicato: +€{adjustment:.2f}"
    if hasattr(item, "note_calcolo"):
        if item.note_calcolo:
            item.note_calcolo += f"\n{note}"
        else:
            item.note_calcolo = note


def update_document_notes(doc, item_groups, customer_group):
    """
    Aggiorna note documento con dettagli minimi applicati
    """
    notes = [f"🏷️ MINIMI GLOBALI APPLICATI - Gruppo: {customer_group}"]
    notes.append("=" * 50)

    for (item_code, tipo_vendita), items in item_groups.items():
        total_qty = 0
        total_adjustment = 0

        for item in items:
            if tipo_vendita == "Metro Quadrato":
                total_qty += flt(item.mq_calcolati)
            elif tipo_vendita == "Metro Lineare":
                total_qty += flt(item.ml_calcolati)
            else:
                total_qty += flt(item.qty)

            # Calcola adjustment dalla differenza
            original_amount = flt(item.qty) * (
                flt(item.amount) / flt(item.qty) - flt(item.manual_rate_override or 0)
            )
            total_adjustment += flt(item.amount) - original_amount

        if total_adjustment > 0:
            unit = (
                "m²"
                if tipo_vendita == "Metro Quadrato"
                else "ml" if tipo_vendita == "Metro Lineare" else "pz"
            )
            notes.append(f"\n• {item_code} ({tipo_vendita}):")
            notes.append(f"  - Quantità totale: {total_qty:.2f} {unit}")
            notes.append(f"  - Adjustment: +€{total_adjustment:.2f}")

    # Aggiungi note esistenti
    if doc.notes:
        notes.append(f"\n\n{doc.notes}")

    doc.notes = "\n".join(notes)


def apply_per_row_minimums(doc, customer_group):
    """
    Fallback: applica minimi per riga (logica originale)
    """
    for item in doc.items:
        if not getattr(item, "supports_custom_measurement", False):
            continue

        tipo_vendita = getattr(item, "tipo_vendita", "Pezzo")

        # Ottieni configurazione minimo
        minimum_config = get_minimum_config(item.item_code, tipo_vendita, customer_group)

        if not minimum_config:
            continue

        # Applica minimo per riga
        apply_row_minimum(item, minimum_config, tipo_vendita)


def apply_row_minimum(item, config, tipo_vendita):
    """
    Applica minimo a singola riga
    """
    # Implementazione semplificata
    # La logica completa è in universal_pricing.py
    pass


@frappe.whitelist()
def toggle_global_minimums(enabled=True):
    """
    API per abilitare/disabilitare minimi globali
    """
    frappe.db.set_value("Selling Settings", None, "use_global_minimums", cint(enabled))
    frappe.db.commit()

    return {
        "success": True,
        "enabled": enabled,
        "message": _("Minimi globali {}").format(_("abilitati") if enabled else _("disabilitati")),
    }


@frappe.whitelist()
def get_minimum_summary(doctype, docname):
    """
    Ottieni riepilogo minimi applicati
    """
    doc = frappe.get_doc(doctype, docname)

    if not doc.customer:
        return {"minimums": []}

    customer_group = frappe.db.get_value("Customer", doc.customer, "customer_group")

    # Analizza righe per minimi
    minimums_data = analyze_document_minimums(doc, customer_group)

    return {
        "customer_group": customer_group,
        "use_global": frappe.db.get_single_value("Selling Settings", "use_global_minimums")
        or True,
        "minimums": minimums_data,
    }


def analyze_document_minimums(doc, customer_group):
    """
    Analizza documento per minimi applicati/applicabili
    """
    results = []

    # Raggruppa per articolo
    item_groups = defaultdict(list)

    for item in doc.items:
        if hasattr(item, "item_code"):
            item_groups[item.item_code].append(item)

    # Analizza ogni gruppo
    for item_code, items in item_groups.items():
        has_minimum = False

        for item in items:
            tipo_vendita = getattr(item, "tipo_vendita", "Pezzo")
            if get_minimum_config(item.item_code, tipo_vendita, customer_group):
                has_minimum = True
                break

        results.append(
            {
                "item_code": item_code,
                "rows": len(items),
                "has_minimum": has_minimum,
            }
        )

    return results
