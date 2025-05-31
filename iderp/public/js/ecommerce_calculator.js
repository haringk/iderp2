// iderp/public/js/ecommerce_calculator.js
console.log("IDERP: E-commerce Calculator Loaded");

class ERPProductCalculator {
    constructor(itemCode) {
        this.itemCode = itemCode;
        this.currentConfig = null;
        this.basePrice = 0;
        this.init();
    }

    async init() {
        await this.loadItemConfig();
        this.createCalculatorInterface();
        this.bindEvents();
    }

    async loadItemConfig() {
        try {
            const response = await fetch('/api/method/iderp.ecommerce.get_item_selling_config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    item_code: this.itemCode
                })
            });
            
            const data = await response.json();
            this.currentConfig = data.message;
            console.log("Config caricata:", this.currentConfig);
        } catch (error) {
            console.error("Errore caricamento config:", error);
        }
    }

    createCalculatorInterface() {
        const productContainer = document.querySelector('.product-page');
        if (!productContainer) return;

        const calculatorHTML = `
            <div id="iderp-calculator" class="measurement-calculator mt-4">
                <h5>Personalizza il tuo ordine</h5>
                
                <!-- Tipo vendita -->
                <div class="form-group">
                    <label>Tipo di vendita:</label>
                    <select id="tipo_vendita" class="form-control">
                        <option value="Pezzo">Al Pezzo</option>
                        <option value="Metro Quadrato">Al Metro Quadrato</option>
                        <option value="Metro Lineare">Al Metro Lineare</option>
                    </select>
                </div>

                <!-- Campi per Metro Quadrato -->
                <div id="mq-fields" class="measurement-fields" style="display: none;">
                    <div class="row">
                        <div class="col-md-6">
                            <label>Base (cm):</label>
                            <input type="number" id="base" class="form-control" min="1" max="1000" step="0.1">
                        </div>
                        <div class="col-md-6">
                            <label>Altezza (cm):</label>
                            <input type="number" id="altezza" class="form-control" min="1" max="1000" step="0.1">
                        </div>
                    </div>
                    <div class="mt-2">
                        <small class="text-muted">Metri quadrati calcolati: <span id="mq-result">0.000 m²</span></small>
                    </div>
                </div>

                <!-- Campi per Metro Lineare -->
                <div id="ml-fields" class="measurement-fields" style="display: none;">
                    <div class="row">
                        <div class="col-md-6">
                            <label>Lunghezza (cm):</label>
                            <input type="number" id="lunghezza" class="form-control" min="1" max="10000" step="0.1">
                        </div>
                        <div class="col-md-6">
                            <label>Larghezza materiale (cm):</label>
                            <input type="number" id="larghezza_materiale" class="form-control" min="1" max="500" step="0.1" readonly>
                        </div>
                    </div>
                    <div class="mt-2">
                        <small class="text-muted">Metri lineari calcolati: <span id="ml-result">0.00 ml</span></small>
                    </div>
                </div>

                <!-- Risultato calcolo -->
                <div id="price-result" class="price-calculation mt-3">
                    <div class="alert alert-info">
                        <strong>Prezzo calcolato: <span id="calculated-price">€0.00</span></strong>
                        <br><small id="calculation-note"></small>
                    </div>
                </div>

                <!-- Pulsante aggiungi al carrello personalizzato -->
                <button id="add-to-cart-calculated" class="btn btn-primary btn-block mt-3">
                    Aggiungi al Carrello
                </button>
            </div>
        `;

        // Inserisci dopo il prezzo del prodotto
        const priceContainer = productContainer.querySelector('.product-price');
        if (priceContainer) {
            priceContainer.insertAdjacentHTML('afterend', calculatorHTML);
        }

        // Imposta valori di default
        this.setDefaultValues();
    }

    setDefaultValues() {
        if (!this.currentConfig) return;

        // Imposta tipo vendita default
        const tipoSelect = document.getElementById('tipo_vendita');
        if (tipoSelect && this.currentConfig.tipo_vendita_default) {
            tipoSelect.value = this.currentConfig.tipo_vendita_default;
        }

        // Imposta larghezza materiale se disponibile
        const larghezzaInput = document.getElementById('larghezza_materiale');
        if (larghezzaInput && this.currentConfig.larghezza_materiale_default) {
            larghezzaInput.value = this.currentConfig.larghezza_materiale_default;
        }

        this.updateFieldsVisibility();
    }

    bindEvents() {
        // Cambio tipo vendita
        document.getElementById('tipo_vendita')?.addEventListener('change', () => {
            this.updateFieldsVisibility();
            this.calculatePrice();
        });

        // Eventi per campi di misurazione
        ['base', 'altezza', 'lunghezza', 'larghezza_materiale'].forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.addEventListener('input', () => this.calculatePrice());
                field.addEventListener('change', () => this.calculatePrice());
            }
        });

        // Aggiungi al carrello
        document.getElementById('add-to-cart-calculated')?.addEventListener('click', () => {
            this.addToCartCalculated();
        });
    }

    updateFieldsVisibility() {
        const tipoVendita = document.getElementById('tipo_vendita')?.value;
        
        // Nasconde tutti i campi
        document.getElementById('mq-fields').style.display = 'none';
        document.getElementById('ml-fields').style.display = 'none';
        
        // Mostra campi appropriati
        if (tipoVendita === 'Metro Quadrato') {
            document.getElementById('mq-fields').style.display = 'block';
        } else if (tipoVendita === 'Metro Lineare') {
            document.getElementById('ml-fields').style.display = 'block';
        }

        this.calculatePrice();
    }

    async calculatePrice() {
        const tipoVendita = document.getElementById('tipo_vendita')?.value;
        
        const measurements = {
            base: parseFloat(document.getElementById('base')?.value || 0),
            altezza: parseFloat(document.getElementById('altezza')?.value || 0),
            lunghezza: parseFloat(document.getElementById('lunghezza')?.value || 0),
            larghezza_materiale: parseFloat(document.getElementById('larghezza_materiale')?.value || 0)
        };

        try {
            const response = await fetch('/api/method/iderp.ecommerce.calculate_item_price', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    item_code: this.itemCode,
                    tipo_vendita: tipoVendita,
                    ...measurements
                })
            });

            const data = await response.json();
            
            if (data.message && !data.message.error) {
                this.displayCalculationResult(data.message);
            } else {
                this.displayError(data.message?.error || 'Errore nel calcolo');
            }

        } catch (error) {
            console.error('Errore calcolo prezzo:', error);
            this.displayError('Errore di connessione');
        }
    }

    displayCalculationResult(result) {
        // Aggiorna visualizzazione metri quadrati/lineari
        if (result.measurements) {
            if (result.measurements.mq_calcolati) {
                document.getElementById('mq-result').textContent = 
                    `${result.measurements.mq_calcolati.toFixed(3)} m²`;
            }
            if (result.measurements.ml_calcolati) {
                document.getElementById('ml-result').textContent = 
                    `${result.measurements.ml_calcolati.toFixed(2)} ml`;
            }
        }

        // Aggiorna prezzo calcolato
        document.getElementById('calculated-price').textContent = 
            `€${result.calculated_price.toFixed(2)}`;
        
        document.getElementById('calculation-note').textContent = result.note_calcolo;

        // Abilita pulsante
        const button = document.getElementById('add-to-cart-calculated');
        button.disabled = false;
        button.textContent = 'Aggiungi al Carrello';

        this.currentCalculation = result;
    }

    displayError(errorMessage) {
        document.getElementById('calculated-price').textContent = '€0.00';
        document.getElementById('calculation-note').textContent = errorMessage;
        
        const button = document.getElementById('add-to-cart-calculated');
        button.disabled = true;
        button.textContent = 'Inserire misure valide';
    }

    async addToCartCalculated() {
        if (!this.currentCalculation) {
            alert('Calcola prima il prezzo');
            return;
        }

        const tipoVendita = document.getElementById('tipo_vendita').value;
        const measurements = this.currentCalculation.measurements || {};

        try {
            const response = await fetch('/api/method/iderp.ecommerce.add_to_cart_calculated', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    item_code: this.itemCode,
                    tipo_vendita: tipoVendita,
                    measurements: measurements
                })
            });

            const data = await response.json();
            
            if (data.message && !data.message.error) {
                // Mostra successo
                this.showSuccess('Prodotto aggiunto al carrello!');
                
                // Aggiorna contatore carrello se presente
                this.updateCartCounter();
            } else {
                alert(data.message?.error || 'Errore nell\'aggiunta al carrello');
            }

        } catch (error) {
            console.error('Errore aggiunta carrello:', error);
            alert('Errore di connessione');
        }
    }

    showSuccess(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'alert alert-success alert-dismissible';
        successDiv.innerHTML = `
            ${message}
            <button type="button" class="close" data-dismiss="alert">
                <span>&times;</span>
            </button>
        `;
        
        document.getElementById('iderp-calculator').prepend(successDiv);
        
        setTimeout(() => {
            successDiv.remove();
        }, 3000);
    }

    updateCartCounter() {
        // Aggiorna il contatore del carrello se presente
        const cartCounter = document.querySelector('.cart-count');
        if (cartCounter) {
            const currentCount = parseInt(cartCounter.textContent) || 0;
            cartCounter.textContent = currentCount + 1;
        }
    }
}

// Inizializza il calcolatore quando la pagina è caricata
document.addEventListener('DOMContentLoaded', function() {
    // Verifica se siamo in una pagina prodotto
    const productCode = document.querySelector('[data-item-code]')?.getAttribute('data-item-code');
    
    if (productCode) {
        console.log('Inizializzazione calcolatore per prodotto:', productCode);
        new ERPProductCalculator(productCode);
    }
});