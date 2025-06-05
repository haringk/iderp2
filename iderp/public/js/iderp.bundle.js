// Bundle principale iDERP per ERPNext 15
// Importa tutti i moduli JavaScript necessari

import "./iderp.js";
import "./item_config.js";
import "./sales_item_optional.js";

// Importa estensioni per form specifici se necessario
import "./form_extensions/quotation.js";
import "./form_extensions/sales_order.js";
import "./form_extensions/sales_invoice.js";
import "./form_extensions/delivery_note.js";

// Esporta per uso globale
export { iderp } from "./iderp.js";