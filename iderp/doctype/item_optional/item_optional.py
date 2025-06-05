# Copyright (c) 2025, IDERP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class ItemOptional(Document):
    """Controller per gestione Optional prodotti stampa digitale"""
    
    def validate(self):
        """Validazioni pre-salvataggio"""
        self.validate_pricing_type()
        self.validate_applicability()
        self.set_title()
    
    def validate_pricing_type(self):
        """Valida coerenza tipo prezzo e valore"""
        if self.pricing_type == "Percentuale" and self.price > 100:
            frappe.throw(_("Per tipo Percentuale, il valore non può superare 100"))
        
        if self.price <= 0:
            frappe.throw(_("Il prezzo/valore deve essere maggiore di zero"))
    
    def validate_applicability(self):
        """Valida regole di applicabilità"""
        # Se è marcato "all_items", non dovrebbero esserci item specifici
        all_items_count = sum(1 for row in self.applicable_for if row.all_items)
        
        if all_items_count > 1:
            frappe.throw(_("Puoi avere solo una riga con 'Tutti gli Articoli' selezionato"))
        
        if all_items_count == 1 and len(self.applicable_for) > 1:
            frappe.throw(_("Se selezioni 'Tutti gli Articoli', non puoi specificare articoli singoli"))
    
    def set_title(self):
        """Imposta titolo descrittivo"""
        if self.pricing_type == "Fisso":
            pricing_desc = f"€{self.price}"
        elif self.pricing_type == "Percentuale":
            pricing_desc = f"{self.price}%"
        else:
            pricing_desc = f"€{self.price}/{self.pricing_type}"
        
        self.title = f"{self.optional_name} ({pricing_desc})"
    
    def is_applicable_to_item(self, item_code):
        """Verifica se optional è applicabile a un item"""
        if not self.enabled:
            return False
        
        # Se non ci sono regole, è applicabile a tutti
        if not self.applicable_for:
            return True
        
        # Verifica "all_items"
        for rule in self.applicable_for:
            if rule.all_items:
                return True
        
        # Verifica item specifico
        for rule in self.applicable_for:
            if rule.item_code == item_code:
                return True
        
        # Verifica item group
        item_group = frappe.db.get_value("Item", item_code, "item_group")
        for rule in self.applicable_for:
            if rule.item_group == item_group:
                return True
        
        return False
    
    def calculate_price(self, base_amount, quantity=1):
        """Calcola prezzo optional in base al tipo"""
        if self.pricing_type == "Fisso":
            return self.price * quantity
        
        elif self.pricing_type == "Percentuale":
            return (base_amount * self.price / 100)
        
        elif self.pricing_type == "Per Metro Quadrato":
            # quantity dovrebbe essere m²
            return self.price * quantity
        
        elif self.pricing_type == "Per Metro Lineare":
            # quantity dovrebbe essere ml
            return self.price * quantity
        
        return 0


@frappe.whitelist()
def get_applicable_optionals(item_code):
    """Ottieni tutti gli optional applicabili per un item"""
    
    if not item_code:
        return []
    
    # Query tutti gli optional attivi
    optionals = frappe.get_all("Item Optional",
        filters={"enabled": 1},
        fields=["name", "optional_name", "description", "pricing_type", "price"]
    )
    
    applicable = []
    
    for opt in optionals:
        opt_doc = frappe.get_doc("Item Optional", opt.name)
        if opt_doc.is_applicable_to_item(item_code):
            applicable.append({
                "optional": opt.name,
                "optional_name": opt.optional_name,
                "description": opt.description,
                "pricing_type": opt.pricing_type,
                "price": opt.price
            })
    
    return applicable


@frappe.whitelist()
def calculate_optional_price(optional, base_amount, quantity):
    """Calcola prezzo di un optional"""
    
    optional_doc = frappe.get_doc("Item Optional", optional)
    return optional_doc.calculate_price(
        flt(base_amount), 
        flt(quantity)
    )


def get_optional_templates(item_code):
    """Ottieni template optional per un item"""
    
    templates = frappe.get_all("Optional Template",
        filters={"item_code": item_code},
        fields=["name", "template_name", "is_default"],
        order_by="is_default desc, creation desc"
    )
    
    return templates