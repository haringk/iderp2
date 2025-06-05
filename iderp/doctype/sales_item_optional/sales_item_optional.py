# Copyright (c) 2025, IDERP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt

class SalesItemOptional(Document):
    """Child table per optional nei documenti vendita"""
    
    def validate(self):
        """Validazioni e calcoli"""
        self.set_optional_details()
        self.calculate_total_price()
    
    def set_optional_details(self):
        """Imposta dettagli dall'optional master"""
        if self.optional:
            opt_doc = frappe.get_doc("Item Optional", self.optional)
            
            # Imposta descrizione e tipo prezzo se non già presenti
            if not self.description:
                self.description = opt_doc.description or opt_doc.optional_name
            
            if not self.pricing_type:
                self.pricing_type = opt_doc.pricing_type
            
            # Imposta prezzo unitario se non specificato
            if not self.unit_price:
                self.unit_price = opt_doc.price
    
    def calculate_total_price(self):
        """Calcola prezzo totale basato sul tipo di pricing"""
        if not self.optional:
            return
        
        opt_doc = frappe.get_doc("Item Optional", self.optional)
        
        # Ottieni riferimenti al documento padre
        parent_doc = self.get_parent_doc()
        if not parent_doc:
            return
        
        # Calcola in base al tipo di pricing
        if self.pricing_type == "Fisso":
            self.total_price = flt(self.unit_price) * flt(self.quantity)
        
        elif self.pricing_type == "Percentuale":
            # Calcola percentuale sul prezzo base dell'item
            base_amount = flt(parent_doc.rate) * flt(parent_doc.qty)
            self.total_price = base_amount * flt(self.unit_price) / 100
        
        elif self.pricing_type == "Per Metro Quadrato":
            # Usa i metri quadrati calcolati
            if hasattr(parent_doc, 'mq_calcolati'):
                self.total_price = flt(self.unit_price) * flt(parent_doc.mq_calcolati)
            else:
                self.total_price = flt(self.unit_price) * flt(self.quantity)
        
        elif self.pricing_type == "Per Metro Lineare":
            # Usa i metri lineari calcolati
            if hasattr(parent_doc, 'ml_calcolati'):
                self.total_price = flt(self.unit_price) * flt(parent_doc.ml_calcolati)
            else:
                self.total_price = flt(self.unit_price) * flt(self.quantity)
        
        else:
            self.total_price = flt(self.unit_price) * flt(self.quantity)
    
    def get_parent_doc(self):
        """Ottieni documento padre (Quotation Item, Sales Order Item, etc.)"""
        if self.parent and self.parenttype:
            return frappe.get_doc(self.parenttype, self.parent)
        return None


def calculate_item_optionals_total(parent_doc, item_row):
    """Calcola totale optional per una riga item"""
    total = 0
    
    if hasattr(item_row, 'item_optionals'):
        for opt in item_row.item_optionals:
            total += flt(opt.total_price)
    
    return total


def update_optional_prices(parent_doc, item_row):
    """Aggiorna prezzi optional quando cambiano le quantità"""
    if not hasattr(item_row, 'item_optionals'):
        return
    
    for opt in item_row.item_optionals:
        opt.calculate_total_price()
    
    # Aggiorna totale optional sulla riga
    if hasattr(item_row, 'optional_total'):
        item_row.optional_total = calculate_item_optionals_total(parent_doc, item_row)


@frappe.whitelist()
def add_optional_to_item(parent_doctype, parent_name, item_idx, optional_name):
    """Aggiungi un optional a una riga item"""
    parent_doc = frappe.get_doc(parent_doctype, parent_name)
    
    # Trova la riga item corretta
    item_row = None
    for idx, row in enumerate(parent_doc.items):
        if idx + 1 == int(item_idx):
            item_row = row
            break
    
    if not item_row:
        frappe.throw(_("Riga item non trovata"))
    
    # Verifica che l'optional non sia già presente
    for opt in item_row.get('item_optionals', []):
        if opt.optional == optional_name:
            frappe.throw(_("Optional {0} già presente").format(optional_name))
    
    # Aggiungi optional
    opt_doc = frappe.get_doc("Item Optional", optional_name)
    
    item_row.append('item_optionals', {
        'optional': optional_name,
        'description': opt_doc.description,
        'pricing_type': opt_doc.pricing_type,
        'unit_price': opt_doc.price,
        'quantity': 1
    })
    
    # Salva documento
    parent_doc.save()
    
    return {
        'success': True,
        'message': _('Optional aggiunto con successo')
    }


@frappe.whitelist()
def remove_optional_from_item(parent_doctype, parent_name, item_idx, optional_idx):
    """Rimuovi un optional da una riga item"""
    parent_doc = frappe.get_doc(parent_doctype, parent_name)
    
    # Trova la riga item
    item_row = None
    for idx, row in enumerate(parent_doc.items):
        if idx + 1 == int(item_idx):
            item_row = row
            break
    
    if not item_row:
        frappe.throw(_("Riga item non trovata"))
    
    # Rimuovi optional
    if item_row.get('item_optionals'):
        item_row.item_optionals.pop(int(optional_idx))
    
    # Salva documento
    parent_doc.save()
    
    return {
        'success': True,
        'message': _('Optional rimosso con successo')
    }


@frappe.whitelist()
def get_optional_summary(parent_doctype, parent_name):
    """Ottieni riepilogo optional per tutto il documento"""
    parent_doc = frappe.get_doc(parent_doctype, parent_name)
    
    optional_summary = {}
    total_amount = 0
    
    for item in parent_doc.get('items', []):
        if hasattr(item, 'item_optionals'):
            for opt in item.item_optionals:
                if opt.optional not in optional_summary:
                    optional_summary[opt.optional] = {
                        'name': opt.optional,
                        'description': opt.description,
                        'total_qty': 0,
                        'total_amount': 0
                    }
                
                optional_summary[opt.optional]['total_qty'] += flt(opt.quantity)
                optional_summary[opt.optional]['total_amount'] += flt(opt.total_price)
                total_amount += flt(opt.total_price)
    
    return {
        'optionals': list(optional_summary.values()),
        'total_amount': total_amount
    }
