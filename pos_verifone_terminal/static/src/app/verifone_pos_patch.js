/** @odoo-module **/

import { registry } from "@web/core/registry";

registry.category("pos_payment_method").add("verifone_bus_listener", {
    async setup(pos) {
        // Espera a que el POS haya cargado completamente
        await pos.ready;  // <--- esta línea es importante

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
