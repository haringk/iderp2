# Copyright (c) 2025, IDERP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class OptionalTemplate(Document):
    """Template predefiniti di optional per articoli stampa digitale"""
    
    def validate(self):
        """Validazioni pre-salvataggio"""
        self.validate_item()
        self.validate_optionals()
        self.ensure_single_default()
    
    def validate_item(self):
        """Valida che l'item supporti misure personalizzate"""
        supports_custom = frappe.db.get_value("Item", self.item_code, "supports_custom_measurement")
        
        if not supports_custom:
            frappe.msgprint(
                _("L'articolo {0} non ha 'Supporta Misure Personalizzate' abilitato. Il template potrebbe non funzionare correttamente.").format(self.item_code),
                alert=True
            )
    
    def validate_optionals(self):
        """Valida gli optional nel template"""
        if not self.optionals:
            frappe.throw(_("Aggiungi almeno un optional al template"))
        
        # Verifica duplicati
        optionals_list = []
        for row in self.optionals:
            if row.optional in optionals_list:
                frappe.throw(_("Optional {0} duplicato nel template").format(row.optional))
            optionals_list.append(row.optional)
            
            # Verifica che l'optional sia applicabile all'item
            opt_doc = frappe.get_doc("Item Optional", row.optional)
            if not opt_doc.is_applicable_to_item(self.item_code):
                frappe.throw(
                    _("L'optional {0} non è applicabile all'articolo {1}").format(
                        row.optional, self.item_code
                    )
                )
    
    def ensure_single_default(self):
        """Assicura che ci sia solo un template default per item"""
        if self.is_default:
            # Rimuovi flag default da altri template dello stesso item
            frappe.db.sql("""
                UPDATE `tabOptional Template`
                SET is_default = 0
                WHERE item_code = %s AND name != %s
            """, (self.item_code, self.name))
    
    def get_optional_details(self):
        """Ottieni dettagli completi degli optional nel template"""
        details = []
        
        for row in self.optionals:
            opt_doc = frappe.get_doc("Item Optional", row.optional)
            details.append({
                "optional": row.optional,
                "optional_name": opt_doc.optional_name,
                "description": opt_doc.description,
                "pricing_type": opt_doc.pricing_type,
                "price": opt_doc.price,
                "is_mandatory": row.is_mandatory,
                "default_selected": row.default_selected
            })
        
        return details


@frappe.whitelist()
def get_template_for_item(item_code):
    """Ottieni template default per un item"""
    
    # Prima cerca template default
    template = frappe.db.get_value("Optional Template", 
        {"item_code": item_code, "is_default": 1}, 
        "name"
    )
    
    # Se non c'è default, prendi il primo disponibile
    if not template:
        template = frappe.db.get_value("Optional Template",
            {"item_code": item_code},
            "name"
        )
    
    if template:
        doc = frappe.get_doc("Optional Template", template)
        return {
            "template": doc.name,
            "template_name": doc.template_name,
            "optionals": doc.get_optional_details()
        }
    
    return None


@frappe.whitelist()
def apply_template_to_item(template_name, parent_doctype, parent_name, parentfield):
    """Applica un template di optional a un item in un documento"""
    
    template = frappe.get_doc("Optional Template", template_name)
    parent_doc = frappe.get_doc(parent_doctype, parent_name)
    
    # Trova la riga item corretta
    item_row = None
    for row in parent_doc.get(parentfield):
        if row.item_code == template.item_code:
            item_row = row
            break
    
    if not item_row:
        frappe.throw(_("Item {0} non trovato nel documento").format(template.item_code))
    
    # Pulisci optional esistenti
    item_row.item_optionals = []
    
    # Applica optional dal template
    for opt in template.optionals:
        if opt.is_mandatory or opt.default_selected:
            opt_doc = frappe.get_doc("Item Optional", opt.optional)
            
            item_row.append("item_optionals", {
                "optional": opt.optional,
                "description": opt_doc.description,
                "pricing_type": opt_doc.pricing_type,
                "unit_price": opt_doc.price,
                "quantity": 1
            })
    
    parent_doc.save()
    
    return {
        "success": True,
        "message": _("Template {0} applicato con successo").format(template.template_name)
    }


@frappe.whitelist()
def create_template_from_selection(item_code, template_name, selected_optionals):
    """Crea un nuovo template da una selezione di optional"""
    
    import json
    if isinstance(selected_optionals, str):
        selected_optionals = json.loads(selected_optionals)
    
    # Crea nuovo template
    template = frappe.new_doc("Optional Template")
    template.template_name = template_name
    template.item_code = item_code
    
    # Aggiungi optional selezionati
    for opt in selected_optionals:
        template.append("optionals", {
            "optional": opt.get("optional"),
            "is_mandatory": opt.get("is_mandatory", 0),
            "default_selected": opt.get("default_selected", 1)
        })
    
    template.insert()
    
    return template.name