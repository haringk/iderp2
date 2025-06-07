# iderp/doctype/pricing_tier/pricing_tier.py
import frappe
from frappe.model.document import Document

class PricingTier(Document):
    def validate(self):
        if self.to_sqm and self.from_sqm >= self.to_sqm:
            frappe.throw("'A m²' deve essere maggiore di 'Da m²'")
        
        if self.from_sqm < 0:
            frappe.throw("'Da m²' non può essere negativo")

    @staticmethod
    def get_price_for_sqm(item_code, total_sqm):
        """Ottieni prezzo per m² in base agli scaglioni"""
        
        # Cerca scaglione appropriato
        tiers = frappe.get_all("Pricing Tier", 
            filters={
                "item_code": item_code,
                "from_sqm": ["<=", total_sqm]
            },
            fields=["from_sqm", "to_sqm", "price_per_sqm"],
            order_by="from_sqm desc"
        )
        
        for tier in tiers:
            # Se to_sqm è None, significa "oltre X m²"
            if not tier.to_sqm or total_sqm <= tier.to_sqm:
                return tier.price_per_sqm
        
        # Se non trova scaglioni, cerca prezzo default
        default_tier = frappe.get_value("Pricing Tier", 
            {"item_code": item_code, "is_default": 1}, 
            "price_per_sqm"
        )
        
        if default_tier:
            return default_tier
            
        # Fallback: cerca Price List standard
        from erpnext.stock.get_item_details import get_price_list_rate
        return get_price_list_rate({
            "item_code": item_code,
            "price_list": frappe.db.get_single_value("Selling Settings", "selling_price_list")
        }) or 0

