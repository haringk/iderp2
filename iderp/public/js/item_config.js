console.log("IDERP: Item Config JS Loaded - Versione semplificata");

// Versione semplificata senza errori - non interferisce con il salvataggio
frappe.ui.form.on('Item', {
    refresh: function(frm) {
        // Non fare nulla di complesso per ora, solo logga
        console.log("Item form refreshed - IDERP active");
    }
});

console.log("✅ IDERP Item Config semplificato caricato");