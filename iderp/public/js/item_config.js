console.log("IDERP: Item Config JS Loaded - Versione universale");

frappe.ui.form.on('Item', {
    refresh: function(frm) {
        // Aggiorna etichette dinamicamente
        update_pricing_section_labels(frm);
    },
    
    supports_custom_measurement: function(frm) {
        update_pricing_section_labels(frm);
    },
    
    tipo_vendita_default: function(frm) {
        update_pricing_section_labels(frm);
    }
});

function update_pricing_section_labels(frm) {
    if (!frm.doc.supports_custom_measurement) {
        return;
    }
    
    let tipo_default = frm.doc.tipo_vendita_default || "Metro Quadrato";
    
    // Aggiorna label sezione in base al tipo default
    let section_label = "";
    let help_text = "";
    
    switch(tipo_default) {
        case "Metro Quadrato":
            section_label = "Scaglioni Prezzo m²";
            help_text = "Configura prezzi in base ai metri quadrati totali dell'ordine";
            break;
        case "Metro Lineare":
            section_label = "Scaglioni Prezzo ml";
            help_text = "Configura prezzi in base ai metri lineari totali dell'ordine";
            break;
        case "Pezzo":
            section_label = "Scaglioni Prezzo per Quantità";
            help_text = "Configura prezzi in base al numero di pezzi nell'ordine";
            break;
        default:
            section_label = "Scaglioni Prezzo Universali";
            help_text = "Configura prezzi per tutti i tipi di vendita";
    }
    
    // Aggiorna nell'interfaccia se possibile
    try {
        let pricing_section = frm.get_field('pricing_section');
        if (pricing_section) {
            pricing_section.set_label(section_label);
        }
        
        // Mostra messaggio informativo
        if (frm.doc.supports_custom_measurement) {
            frm.set_intro(`📊 Tipo vendita attivo: <strong>${tipo_default}</strong> - ${help_text}`, 'blue');
        }
    } catch(e) {
        console.log("Info: Aggiornamento labels non disponibile");
    }
}

console.log("✅ IDERP Item Config universale caricato");