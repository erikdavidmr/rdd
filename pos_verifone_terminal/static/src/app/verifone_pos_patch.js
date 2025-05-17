/** @odoo-module **/

import { registry } from "@web/core/registry";

// Listener del webhook desde backend
registry.category("pos_payment_method").add("verifone_bus_listener", {
    async setup(pos) {
        await pos.ready;

        pos.bus.on("VERIFONE_LATEST_RESPONSE", null, (payload) => {
            console.log("[Verifone] Evento VERIFONE_LATEST_RESPONSE recibido:", payload);

            const paymentLine = pos.getPendingPaymentLine("verifone_middleware");
            if (!paymentLine) {
                return console.warn("[Verifone] Línea pendiente no encontrada.");
            }

            const method = paymentLine.payment_method_id;
            const terminal = method?.payment_terminal;

            if (!terminal?.handleVerifoneStatusResponse) {
                return console.warn("[Verifone] Método no válido o sin handler");
            }

            terminal.handleVerifoneStatusResponse(payload);
        });

        console.log("[Verifone] Listener activo para VERIFONE_LATEST_RESPONSE");
    },
});

// Exponer `pos` globalmente para pruebas desde consola
registry.category("pos_payment_method").add("verifone_expose_pos", {
    async setup(pos) {
        await pos.ready;
        window.pos = pos;
        console.log("[Verifone] POS expuesto globalmente como 'window.pos'");
    },
});
