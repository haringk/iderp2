# iderp/doctype/item_pricing_tier/item_pricing_tier.py

import frappe
from frappe.model.document import Document
from frappe import _

class ItemPricingTier(Document):
    def validate(self):
        """Validazione scaglioni prezzo"""
        self.validate_quantities()
        self.validate_price()
        self.validate_tier_logic()
        
    def validate_quantities(self):
        """Valida quantità from/to"""
        if self.from_qty < 0:
            frappe.throw(_("From Quantity cannot be negative"))
            
        if self.to_qty is not None:
            if self.to_qty < 0:
                frappe.throw(_("To Quantity cannot be negative"))
                
            if self.from_qty >= self.to_qty:
                frappe.throw(_(
                    f"To Quantity ({self.to_qty}) must be greater than "
                    f"From Quantity ({self.from_qty})"
                ))
                
    def validate_price(self):
        """Valida prezzo unitario"""
        if self.price_per_unit <= 0:
            frappe.throw(_("Price per Unit must be greater than 0"))
            
    def validate_tier_logic(self):
        """Valida logica scaglioni nel contesto del parent Item"""
        if not self.parent:
            return
            
        # Ottieni tutti gli altri scaglioni dello stesso tipo
        siblings = [
            tier for tier in self.get_parent_doc().pricing_tiers 
            if (tier.selling_type == self.selling_type and 
                tier.name != self.name)
        ]
        
        if not siblings:
            return
            
        # Controlla sovrapposizioni
        for sibling in siblings:
            self.check_overlap_with_sibling(sibling)
    
    def check_overlap_with_sibling(self, other_tier):
        """Controlla sovrapposizione con altro scaglione"""
        # Se uno dei due non ha to_qty, skip controllo sovrapposizione
        if not self.to_qty or not other_tier.to_qty:
            return
            
        # Vera sovrapposizione: inizio di uno prima della fine dell'altro
        if (self.from_qty < other_tier.to_qty and 
            other_tier.from_qty < self.to_qty):
            
            frappe.throw(_(
                f"Tier overlap detected: "
                f"This tier ({self.from_qty}-{self.to_qty}) "
                f"overlaps with existing tier "
                f"({other_tier.from_qty}-{other_tier.to_qty}) "
                f"for {self.selling_type}"
            ))
    
    def get_parent_doc(self):
        """Ottieni documento parent (Item)"""
        if not hasattr(self, '_parent_doc'):
            self._parent_doc = frappe.get_doc(self.parenttype, self.parent)
        return self._parent_doc
    
    @staticmethod
    def find_applicable_tier(item_code, selling_type, quantity):
        """
        Trova scaglione applicabile per quantità specifica
        
        Args:
            item_code: Codice articolo
            selling_type: Tipo vendita 
            quantity: Quantità da valutare
            
        Returns:
            dict: Scaglione trovato o None
        """
        # Cache key per performance
        cache_key = f"pricing_tier_{item_code}_{selling_type}_{quantity}"
        cached_tier = frappe.cache().get_value(cache_key)
        
        if cached_tier is not None:
            return cached_tier
            
        # Query scaglioni per questo item/tipo
        tiers = frappe.db.sql("""
            SELECT ipt.from_qty, ipt.to_qty, ipt.price_per_unit, 
                   ipt.tier_name, ipt.is_default
            FROM `tabItem Pricing Tier` ipt
            JOIN `tabItem` i ON i.name = ipt.parent
            WHERE i.item_code = %s 
            AND ipt.selling_type = %s
            AND ipt.from_qty <= %s
            AND (ipt.to_qty IS NULL OR ipt.to_qty >= %s)
            ORDER BY ipt.from_qty DESC
            LIMIT 1
        """, [item_code, selling_type, quantity, quantity], as_dict=True)
        
        if not tiers:
            # Cerca default per questo tipo
            default_tiers = frappe.db.sql("""
                SELECT ipt.from_qty, ipt.to_qty, ipt.price_per_unit, 
                       ipt.tier_name, ipt.is_default
                FROM `tabItem Pricing Tier` ipt
                JOIN `tabItem` i ON i.name = ipt.parent
                WHERE i.item_code = %s 
                AND ipt.selling_type = %s
                AND ipt.is_default = 1
                ORDER BY ipt.from_qty DESC
                LIMIT 1
            """, [item_code, selling_type], as_dict=True)
            
            result = default_tiers[0] if default_tiers else None
        else:
            result = tiers[0]
            
        # Cache per 5 minuti
        frappe.cache().set_value(cache_key, result, expires_in_sec=300)
        
        return result
    
    @staticmethod
    def get_price_for_quantity(item_code, selling_type, quantity):
        """
        Calcola prezzo per quantità specifica
        
        Returns:
            float: Prezzo per unità o 0 se non trovato
        """
        tier = ItemPricingTier.find_applicable_tier(item_code, selling_type, quantity)
        return tier["price_per_unit"] if tier else 0
    
    @staticmethod
    def get_all_tiers_for_item(item_code, selling_type=None):
        """
        Ottieni tutti gli scaglioni per un item
        
        Args:
            item_code: Codice articolo
            selling_type: Tipo vendita (opzionale, se None ritorna tutti)
            
        Returns:
            list: Lista scaglioni raggruppati per tipo
        """
        filters = {"parent": frappe.db.get_value("Item", {"item_code": item_code}, "name")}
        
        if selling_type:
            filters["selling_type"] = selling_type
            
        tiers = frappe.get_all("Item Pricing Tier",
            filters=filters,
            fields=["selling_type", "from_qty", "to_qty", "price_per_unit", "tier_name", "is_default"],
            order_by="selling_type, from_qty"
        )
        
        # Raggruppa per tipo vendita
        grouped = {}
        for tier in tiers:
            st = tier["selling_type"]
            if st not in grouped:
                grouped[st] = []
            grouped[st].append(tier)
            
        return grouped
    
    def on_update(self):
        """Dopo aggiornamento, pulisci cache"""
        self.clear_pricing_cache()
        
    def on_trash(self):
        """Prima di eliminare, pulisci cache"""
        self.clear_pricing_cache()
        
    def clear_pricing_cache(self):
        """Pulisce cache prezzi per questo item"""
        if self.parent:
            item_code = frappe.db.get_value("Item", self.parent, "item_code")
            if item_code:
                cache_pattern = f"pricing_tier_{item_code}_*"
                frappe.cache().delete_keys(cache_pattern)

def clear_all_pricing_tier_cache():
    """Utility per pulire tutta la cache scaglioni"""
    frappe.cache().delete_keys("pricing_tier_*")

def validate_item_pricing_tiers(item_doc, method=None):
    """
    Hook per validare tutti gli scaglioni di un Item
    Chiamato quando si salva un Item
    """
    if not hasattr(item_doc, 'pricing_tiers') or not item_doc.pricing_tiers:
        return
        
    # Raggruppa per selling_type
    by_type = {}
    for tier in item_doc.pricing_tiers:
        st = tier.selling_type
        if st not in by_type:
            by_type[st] = []
        by_type[st].append(tier)
    
    # Valida ogni gruppo separatamente
    for selling_type, tiers in by_type.items():
        validate_tiers_for_selling_type(selling_type, tiers)

def validate_tiers_for_selling_type(selling_type, tiers):
    """Valida scaglioni per un tipo vendita specifico"""
    if len(tiers) <= 1:
        return
        
    # Ordina per from_qty
    sorted_tiers = sorted(tiers, key=lambda t: t.from_qty)
    
    for i in range(len(sorted_tiers) - 1):
        current = sorted_tiers[i]
        next_tier = sorted_tiers[i + 1]
        
        # Se il corrente ha to_qty, verifica contiguità
        if current.to_qty:
            # Gap warning
            if next_tier.from_qty > current.to_qty:
                gap = next_tier.from_qty - current.to_qty
                frappe.msgprint(_(
                    f"Gap of {gap} detected between tiers for {selling_type}: "
                    f"{current.to_qty} to {next_tier.from_qty}. "
                    f"Orders in this range will use the previous tier."
                ), title="Tier Configuration Warning", indicator="orange")