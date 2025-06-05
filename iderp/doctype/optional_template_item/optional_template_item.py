# Copyright (c) 2025, IDERP and contributors
# For license information, please see license.txt

from frappe.model.document import Document

class OptionalTemplateItem(Document):
    """Child table per optional nei template"""
    
    def validate(self):
        """Validazioni"""
        # Se è obbligatorio, deve essere anche selezionato di default
        if self.is_mandatory and not self.default_selected:
            self.default_selected = 1