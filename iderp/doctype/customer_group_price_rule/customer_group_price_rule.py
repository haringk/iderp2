# iderp/doctype/customer_group_price_rule/customer_group_price_rule.py

import frappe
from frappe.model.document import Document
from frappe import _

class CustomerGroupPriceRule(Document):
    def validate(self):
        """Validazione regole prezzo gruppo cliente"""
        self.validate_dates()
        self.validate_min_qty()
        self.validate_duplicate_rules()
        
    def validate_dates(self):
        """Valida date validità"""
        if self.valid_from and self.valid_till:
            if self.valid_from >= self.valid_till:
                frappe.throw(_("Valid Till date must be after Valid From date"))
                
    def validate_min_qty(self):
        """Valida quantità minima"""
        if self.min_qty and self.min_qty < 0:
            frappe.throw(_("Minimum Quantity cannot be negative"))
            
    def validate_duplicate_rules(self):
        """Evita regole duplicate per stesso gruppo/item/tipo"""
        if not self.name:  # Solo per nuovi documenti
            existing = frappe.db.exists("Customer Group Price Rule", {
                "customer_group": self.customer_group,
                "item_code": self.item_code,
                "selling_type": self.selling_type,
                "enabled": 1,
                "name": ["!=", self.name or ""]
            })
            
            if existing:
                frappe.throw(_(
                    f"Active price rule already exists for {self.customer_group} "
                    f"+ {self.item_code} + {self.selling_type}. "
                    f"Disable existing rule first."
                ))
    
    def on_update(self):
        """Dopo aggiornamento, pulisci cache prezzi"""
        self.clear_pricing_cache()
        
    def on_trash(self):
        """Prima di eliminare, pulisci cache"""
        self.clear_pricing_cache()
        
    def clear_pricing_cache(self):
        """Pulisce cache prezzi per questo item/gruppo"""
        cache_key = f"customer_price_rule_{self.customer_group}_{self.item_code}"
        frappe.cache().delete_value(cache_key)
        
    @staticmethod
    def get_applicable_rule(customer_group, item_code, selling_type, date=None):
        """
        Trova regola applicabile per gruppo/item/tipo
        
        Args:
            customer_group: Nome gruppo cliente
            item_code: Codice articolo
            selling_type: Tipo vendita (Metro Quadrato, Metro Lineare, Pezzo)
            date: Data di riferimento (default: oggi)
            
        Returns:
            dict: Regola trovata o None
        """
        if not date:
            date = frappe.utils.today()
            
        # Cache key
        cache_key = f"customer_price_rule_{customer_group}_{item_code}_{selling_type}_{date}"
        cached_rule = frappe.cache().get_value(cache_key)
        
        if cached_rule is not None:
            return cached_rule
            
        # Query con filtri date e priorità
        filters = {
            "customer_group": customer_group,
            "item_code": item_code,
            "selling_type": selling_type,
            "enabled": 1
        }
        
        # Aggiungi filtri date solo se configurati
        date_conditions = []
        if frappe.db.count("Customer Group Price Rule", {"valid_from": ["is", "set"]}):
            date_conditions.append(["valid_from", "<=", date])
        if frappe.db.count("Customer Group Price Rule", {"valid_till": ["is", "set"]}):
            date_conditions.append(["valid_till", ">=", date])
            
        if date_conditions:
            filters.update({"name": ["in", frappe.db.get_list(
                "Customer Group Price Rule",
                filters=date_conditions,
                pluck="name"
            )]})
        
        # Trova regola con priorità più alta
        rules = frappe.get_all("Customer Group Price Rule",
            filters=filters,
            fields=["*"],
            order_by="priority desc, creation desc",
            limit=1
        )
        
        result = rules[0] if rules else None
        
        # Cache per 5 minuti
        frappe.cache().set_value(cache_key, result, expires_in_sec=300)
        
        return result
    
    @staticmethod
    def get_effective_minimum(customer_group, item_code, selling_type, quantity):
        """
        Calcola minimo effettivo considerando regole gruppo
        
        Args:
            customer_group: Gruppo cliente
            item_code: Codice articolo  
            selling_type: Tipo vendita
            quantity: Quantità originale
            
        Returns:
            dict: {
                'original_qty': quantità originale,
                'effective_qty': quantità effettiva (>= minimo),
                'minimum_applied': True se minimo applicato,
                'rule': regola applicata,
                'fixed_cost': costo fisso aggiuntivo
            }
        """
        rule = CustomerGroupPriceRule.get_applicable_rule(
            customer_group, item_code, selling_type
        )
        
        if not rule or not rule.get("min_qty"):
            return {
                'original_qty': quantity,
                'effective_qty': quantity,
                'minimum_applied': False,
                'rule': None,
                'fixed_cost': 0
            }
            
        min_qty = rule["min_qty"]
        effective_qty = max(quantity, min_qty)
        
        return {
            'original_qty': quantity,
            'effective_qty': effective_qty,
            'minimum_applied': effective_qty > quantity,
            'rule': rule,
            'fixed_cost': rule.get("fixed_cost", 0) or 0
        }

def clear_all_pricing_cache():
    """Utility per pulire tutta la cache prezzi"""
    frappe.cache().delete_keys("customer_price_rule_*")

def get_customer_group_rules_summary(customer_group):
    """
    Ottieni riepilogo regole per un gruppo cliente
    
    Returns:
        list: Lista regole attive per il gruppo
    """
    return frappe.get_all("Customer Group Price Rule",
        filters={
            "customer_group": customer_group,
            "enabled": 1
        },
        fields=[
            "item_code", "selling_type", "min_qty", 
            "calculation_mode", "fixed_cost", "priority"
        ],
        order_by="item_code, selling_type"
    )

# Validatori per Import Data
def validate_customer_group_price_rule_import(doc, method=None):
    """Validazione extra per import dati"""
    if not frappe.db.exists("Customer Group", doc.customer_group):
        frappe.throw(_(f"Customer Group '{doc.customer_group}' does not exist"))
        
    if not frappe.db.exists("Item", doc.item_code):
        frappe.throw(_(f"Item '{doc.item_code}' does not exist"))