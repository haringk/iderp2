console.log("IDERP: Item Config JS Loaded - Versione semplificata");

// Versione semplificata senza errori
frappe.ui.form.on('Item', {
    refresh: function(frm) {
        // Non fare nulla per ora, solo logga
        console.log("Item form refreshed");
    }
});