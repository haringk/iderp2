import frappe

def after_install():
    """Installazione completa plugin iderp con supporto e-commerce"""
    print("[iderp] Iniziando installazione plugin...")
    
    # 1. Installa campi custom per documenti di vendita
    install_sales_custom_fields()
    
    # 2. Installa campi custom per configurazione Item
    install_item_config_fields()
    
    # 3. Crea Custom Fields per e-commerce
    install_ecommerce_fields()
    
    # 4. Setup configurazioni e-commerce
    setup_ecommerce_settings()
    
    # 5. Crea print formats personalizzati
    create_custom_print_formats()
    
    print("[iderp] Installazione completata con successo!")

def install_sales_custom_fields():
    """Installa campi custom per documenti di vendita"""
    doctypes = [
        "Quotation Item",
        "Sales Order Item",
        "Delivery Note Item", 
        "Sales Invoice Item",
        "Purchase Order Item",
        "Purchase Invoice Item",
        "Material Request Item",
    ]
    
    custom_fields = [
        # Campo per tipo di vendita
        {
            "fieldname": "tipo_vendita",
            "label": "Tipo Vendita", 
            "fieldtype": "Select",
            "options": "\nPezzo\nMetro Quadrato\nMetro Lineare",
            "default": "Pezzo",
            "insert_after": "item_code",
            "reqd": 1,
            "description": "Seleziona come vendere questo prodotto",
        },
        
        # Campi per metri quadrati
        {
            "fieldname": "base",
            "label": "Base (cm)",
            "fieldtype": "Float", 
            "insert_after": "tipo_vendita",
            "precision": 2,
            "depends_on": "eval:doc.tipo_vendita=='Metro Quadrato'",
            "description": "Base in centimetri per calcolo mq",
        },
        {
            "fieldname": "altezza",
            "label": "Altezza (cm)",
            "fieldtype": "Float",
            "insert_after": "base",
            "precision": 2, 
            "depends_on": "eval:doc.tipo_vendita=='Metro Quadrato'",
            "description": "Altezza in centimetri per calcolo mq",
        },
        {
            "fieldname": "mq_calcolati",
            "label": "Metri Quadri",
            "fieldtype": "Float",
            "insert_after": "altezza",
            "precision": 3,
            "read_only": 1,
            "depends_on": "eval:doc.tipo_vendita=='Metro Quadrato'",
            "description": "Base x Altezza / 10000 (calcolato automaticamente)",
        },
        
        # Campi per metri lineari
        {
            "fieldname": "larghezza_materiale",
            "label": "Larghezza Materiale (cm)",
            "fieldtype": "Float",
            "insert_after": "mq_calcolati", 
            "precision": 2,
            "depends_on": "eval:doc.tipo_vendita=='Metro Lineare'",
            "description": "Larghezza del materiale in centimetri",
        },
        {
            "fieldname": "lunghezza",
            "label": "Lunghezza (cm)",
            "fieldtype": "Float",
            "insert_after": "larghezza_materiale",
            "precision": 2,
            "depends_on": "eval:doc.tipo_vendita=='Metro Lineare'", 
            "description": "Lunghezza in centimetri",
        },
        {
            "fieldname": "ml_calcolati",
            "label": "Metri Lineari",
            "fieldtype": "Float",
            "insert_after": "lunghezza",
            "precision": 2,
            "read_only": 1,
            "depends_on": "eval:doc.tipo_vendita=='Metro Lineare'",
            "description": "Lunghezza / 100 (calcolato automaticamente)",
        },
        
        # Prezzi specifici per tipo
        {
            "fieldname": "prezzo_mq",
            "label": "Prezzo al Mq (€)",
            "fieldtype": "Currency",
            "insert_after": "rate",
            "depends_on": "eval:doc.tipo_vendita=='Metro Quadrato'",
            "description": "Prezzo per metro quadrato",
        },
        {
            "fieldname": "prezzo_ml", 
            "label": "Prezzo al Ml (€)",
            "fieldtype": "Currency",
            "insert_after": "prezzo_mq",
            "depends_on": "eval:doc.tipo_vendita=='Metro Lineare'",
            "description": "Prezzo per metro lineare",
        },
        
        # Campo informativo
        {
            "fieldname": "note_calcolo",
            "label": "Note Calcolo",
            "fieldtype": "Small Text",
            "insert_after": "prezzo_ml",
            "read_only": 1,
            "description": "Mostra come è stato calcolato il prezzo",
        },
    ]
    
    for dt in doctypes:
        for cf in custom_fields:
            create_custom_field(dt, cf)

def install_item_config_fields():
    """Installa campi custom per configurazione Item"""
    custom_fields = [
        {
            "fieldname": "measurement_config_section",
            "fieldtype": "Section Break",
            "label": "Configurazione Vendita Personalizzata",
            "insert_after": "website_specifications",
            "collapsible": 1,
        },
        {
            "fieldname": "supports_custom_measurement",
            "fieldtype": "Check", 
            "label": "Supporta Misure Personalizzate",
            "insert_after": "measurement_config_section",
            "description": "Abilita calcoli per metro quadrato/lineare",
        },
        {
            "fieldname": "tipo_vendita_default",
            "fieldtype": "Select",
            "label": "Tipo Vendita Default",
            "options": "\nPezzo\nMetro Quadrato\nMetro Lineare",
            "insert_after": "supports_custom_measurement",
            "depends_on": "supports_custom_measurement",
        },
        {
            "fieldname": "config_column_break",
            "fieldtype": "Column Break",
            "insert_after": "tipo_vendita_default",
        },
        {
            "fieldname": "larghezza_materiale_default",
            "fieldtype": "Float",
            "label": "Larghezza Materiale Default (cm)",
            "precision": 2,
            "insert_after": "config_column_break",
            "depends_on": "eval:doc.tipo_vendita_default=='Metro Lineare'",
        },
        {
            "fieldname": "measurement_limits_section", 
            "fieldtype": "Section Break",
            "label": "Limiti Misurazione",
            "insert_after": "larghezza_materiale_default",
            "depends_on": "supports_custom_measurement",
            "collapsible": 1,
        },
        {
            "fieldname": "base_min",
            "fieldtype": "Float",
            "label": "Base Minima (cm)",
            "default": 1,
            "insert_after": "measurement_limits_section",
            "depends_on": "eval:doc.tipo_vendita_default=='Metro Quadrato'",
        },
        {
            "fieldname": "base_max", 
            "fieldtype": "Float",
            "label": "Base Massima (cm)",
            "default": 1000,
            "insert_after": "base_min",
            "depends_on": "eval:doc.tipo_vendita_default=='Metro Quadrato'",
        },
        {
            "fieldname": "limits_column_break",
            "fieldtype": "Column Break",
            "insert_after": "base_max",
        },
        {
            "fieldname": "altezza_min",
            "fieldtype": "Float", 
            "label": "Altezza Minima (cm)",
            "default": 1,
            "insert_after": "limits_column_break",
            "depends_on": "eval:doc.tipo_vendita_default=='Metro Quadrato'",
        },
        {
            "fieldname": "altezza_max",
            "fieldtype": "Float",
            "label": "Altezza Massima (cm)", 
            "default": 1000,
            "insert_after": "altezza_min",
            "depends_on": "eval:doc.tipo_vendita_default=='Metro Quadrato'",
        },
        {
            "fieldname": "lunghezza_limits_section",
            "fieldtype": "Section Break",
            "label": "Limiti Lunghezza",
            "insert_after": "altezza_max",
            "depends_on": "eval:doc.tipo_vendita_default=='Metro Lineare'",
            "collapsible": 1,
        },
        {
            "fieldname": "lunghezza_min",