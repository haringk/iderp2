# iderp/doctype/customer_group_minimum/customer_group_minimum.py

import frappe
from frappe.model.document import Document
from frappe import _

class CustomerGroupMinimum(Document):
    def validate(self):
        """Validazione minimi gruppo cliente"""
        self.validate_min_qty()
        self.validate_fixed_cost()
        self.validate_customer_group()
        
    def validate_min_qty(self):
        """Valida quantità minima"""
        if self.min_qty < 0:
            frappe.throw(_("Minimum Quantity cannot be negative"))
            
    def validate_fixed_cost(self):
        """Valida costo fisso"""
        if self.fixed_cost and self.fixed_cost < 0:
            frappe.throw(_("Fixed Cost cannot be negative"))
            
        if self.fixed_cost and self.fixed_cost > 0 and not self.fixed_cost_mode:
            frappe.throw(_("Fixed Cost Mode is required when Fixed Cost is set"))
            
    def validate_customer_group(self):
        """Valida gruppo cliente"""
        if not frappe.db.exists("Customer Group", self.customer_group):
            frappe.throw(_(f"Customer Group '{self.customer_group}' does not exist"))
    
    def validate_duplicate_within_parent(self):
        """Evita duplicati per stesso gruppo/tipo nel parent Item"""
        if not self.parent:
            return
            
        # Controlla altri record nello stesso parent con stesso gruppo/tipo
        siblings = [
            minimum for minimum in self.get_parent_doc().customer_group_minimums
            if (minimum.customer_group == self.customer_group and
                minimum.selling_type == self.selling_type and
                minimum.name != self.name and
                minimum.enabled)
        ]
        
        if siblings:
            frappe.throw(_(
                f"Duplicate minimum rule found for {self.customer_group} "
                f"+ {self.selling_type}. Only one active rule per "
                f"customer group + selling type is allowed."
            ))
    
    def get_parent_doc(self):
        """Ottieni documento parent (Item)"""
        if not hasattr(self, '_parent_doc'):
            self._parent_doc = frappe.get_doc(self.parenttype, self.parent)
        return self._parent_doc
    
    @staticmethod
    def get_minimum_for_customer_and_item(customer_group, item_code, selling_type):
        """
        Trova minimo applicabile per gruppo cliente + item + tipo vendita
        
        Args:
            customer_group: Nome gruppo cliente
            item_code: Codice articolo
            selling_type: Tipo vendita
            
        Returns:
            dict: Configurazione minimo o None
        """
        # Cache key
        cache_key = f"customer_minimum_{customer_group}_{item_code}_{selling_type}"
        cached_minimum = frappe.cache().get_value(cache_key)
        
        if cached_minimum is not None:
            return cached_minimum
            
        # Query diretta per performance
        minimums = frappe.db.sql("""
            SELECT cgm.min_qty, cgm.calculation_mode, cgm.fixed_cost, 
                   cgm.fixed_cost_mode, cgm.description, cgm.priority
            FROM `tabCustomer Group Minimum` cgm
            JOIN `tabItem` i ON i.name = cgm.parent
            WHERE i.item_code = %s 
            AND cgm.customer_group = %s
            AND cgm.selling_type = %s
            AND cgm.enabled = 1
            ORDER BY cgm.priority DESC, cgm.creation DESC
            LIMIT 1
        """, [item_code, customer_group, selling_type], as_dict=True)
        
        result = minimums[0] if minimums else None
        
        # Cache per 10 minuti
        frappe.cache().set_value(cache_key, result, expires_in_sec=600)
        
        return result
    
    @staticmethod
    def apply_minimum_to_quantity(customer_group, item_code, selling_type, original_qty):
        """
        Applica minimo a quantità specifica
        
        Args:
            customer_group: Gruppo cliente
            item_code: Codice articolo
            selling_type: Tipo vendita
            original_qty: Quantità originale
            
        Returns:
            dict: {
                'original_qty': quantità originale,
                'effective_qty': quantità con minimo applicato,
                'minimum_applied': bool,
                'minimum_config': configurazione usata,
                'fixed_cost_info': informazioni costo fisso
            }
        """
        minimum_config = CustomerGroupMinimum.get_minimum_for_customer_and_item(
            customer_group, item_code, selling_type
        )
        
        if not minimum_config or not minimum_config.get("min_qty"):
            return {
                'original_qty': original_qty,
                'effective_qty': original_qty,
                'minimum_applied': False,
                'minimum_config': None,
                'fixed_cost_info': {'amount': 0, 'mode': None}
            }
            
        min_qty = minimum_config["min_qty"]
        effective_qty = max(original_qty, min_qty)
        
        # Calcola info costo fisso
        fixed_cost = minimum_config.get("fixed_cost", 0) or 0
        fixed_cost_mode = minimum_config.get("fixed_cost_mode")
        
        return {
            'original_qty': original_qty,
            'effective_qty': effective_qty,
            'minimum_applied': effective_qty > original_qty,
            'minimum_config': minimum_config,
            'fixed_cost_info': {
                'amount': fixed_cost,
                'mode': fixed_cost_mode,
                'applies': fixed_cost > 0
            }
        }
    
    @staticmethod
    def get_all_minimums_for_item(item_code):
        """
        Ottieni tutti i minimi configurati per un item
        
        Returns:
            dict: Minimi raggruppati per customer_group e selling_type
        """
        minimums = frappe.db.sql("""
            SELECT cgm.customer_group, cgm.selling_type, cgm.min_qty,
                   cgm.calculation_mode, cgm.fixed_cost, cgm.fixed_cost_mode,
                   cgm.enabled, cgm.description
            FROM `tabCustomer Group Minimum` cgm
            JOIN `tabItem` i ON i.name = cgm.parent
            WHERE i.item_code = %s
            ORDER BY cgm.customer_group, cgm.selling_type
        """, [item_code], as_dict=True)
        
        # Raggruppa per gruppo cliente
        grouped = {}
        for minimum in minimums:
            group = minimum["customer_group"]
            if group not in grouped:
                grouped[group] = {}
            grouped[group][minimum["selling_type"]] = minimum
            
        return grouped
    
    @staticmethod
    def get_customer_group_summary(customer_group):
        """
        Ottieni riepilogo minimi per un gruppo cliente
        
        Returns:
            list: Lista item con minimi configurati per questo gruppo
        """
        return frappe.db.sql("""
            SELECT i.item_code, i.item_name, cgm.selling_type, 
                   cgm.min_qty, cgm.calculation_mode, cgm.fixed_cost
            FROM `tabCustomer Group Minimum` cgm
            JOIN `tabItem` i ON i.name = cgm.parent
            WHERE cgm.customer_group = %s 
            AND cgm.enabled = 1
            ORDER BY i.item_code, cgm.selling_type
        """, [customer_group], as_dict=True)
    
    def on_update(self):
        """Dopo aggiornamento, pulisci cache"""
        self.clear_minimum_cache()
        
    def on_trash(self):
        """Prima di eliminare, pulisci cache"""
        self.clear_minimum_cache()
        
    def clear_minimum_cache(self):
        """Pulisce cache minimi per questo gruppo/item"""
        if self.parent:
            item_code = frappe.db.get_value("Item", self.parent, "item_code")
            if item_code:
                cache_pattern = f"customer_minimum_{self.customer_group}_{item_code}_*"
                frappe.cache().delete_keys(cache_pattern)

def clear_all_minimum_cache():
    """Utility per pulire tutta la cache minimi"""
    frappe.cache().delete_keys("customer_minimum_*")

def validate_item_customer_minimums(item_doc, method=None):
    """
    Hook per validare tutti i minimi di un Item
    Chiamato quando si salva un Item
    """
    if not hasattr(item_doc, 'customer_group_minimums') or not item_doc.customer_group_minimums:
        return
        
    # Controlla duplicati per gruppo/tipo
    seen_combinations = set()
    
    for minimum in item_doc.customer_group_minimums:
        if not minimum.enabled:
            continue
            
        combo_key = f"{minimum.customer_group}_{minimum.selling_type}"
        
        if combo_key in seen_combinations:
            frappe.throw(_(
                f"Duplicate minimum configuration found for "
                f"{minimum.customer_group} + {minimum.selling_type}. "
                f"Only one active minimum per customer group + selling type is allowed."
            ))
            
        seen_combinations.add(combo_key)

def get_global_minimum_calculation_items(doc, customer_group):
    """
    Ottieni item che richiedono calcolo minimo globale
    
    Args:
        doc: Documento (Quotation, Sales Order, etc.)
        customer_group: Gruppo cliente
        
    Returns:
        dict: Item raggruppati per calcolo globale
    """
    global_items = {}
    
    for item in doc.items:
        tipo_vendita = getattr(item, 'tipo_vendita', 'Pezzo')
        
        minimum_config = CustomerGroupMinimum.get_minimum_for_customer_and_item(
            customer_group, item.item_code, tipo_vendita
        )
        
        if (minimum_config and 
            minimum_config.get("calculation_mode") == "Globale Preventivo"):
            
            key = f"{item.item_code}_{tipo_vendita}_{customer_group}"
            
            if key not in global_items:
                global_items[key] = {
                    'items': [],
                    'minimum_config': minimum_config,
                    'item_code': item.item_code,
                    'selling_type': tipo_vendita
                }
                
            global_items[key]['items'].append(item)
    
    return global_items