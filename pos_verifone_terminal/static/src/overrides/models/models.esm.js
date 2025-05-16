/** @odoo-module **/

import { PaymentVerifoneMiddleware } from "@pos_verifone_terminal/app/payment_verifone.esm";
import { register_payment_method } from "@point_of_sale/app/store/pos_store";
import { registry } from "@web/core/registry";

// Registro del método de pago Verifone
register_payment_method("verifone_middleware", PaymentVerifoneMiddleware);

// Registro seguro del listener de webhook
const category = registry.category("pos_payment_method");

if (!category.contains("verifone_bus_listener")) {
    category.add("verifone_bus_listener", {
        async setup(pos) {
            await pos.ready;

            pos.bus.on("VERIFONE_LATEST_RESPONSE", null, (payload) => {
                console.log("[Verifone] Evento VERIFONE_LATEST_RESPONSE recibido:", payload);

                const paymentLine = pos.getPendingPaymentLine("verifone_middleware");
                if (!paymentLine) {
                    console.warn("[Verifone] Línea de pago pendiente no encontrada.");
                    return;
                }

                const method = paymentLine.payment_method_id;
                const terminal = method?.payment_terminal;

                if (!terminal?.handleVerifoneStatusResponse) {
                    console.warn("[Verifone] Método de pago sin terminal válida o sin handler.");
                    return;
                }

                terminal.handleVerifoneStatusResponse(payload);
            });

            console.log("[Verifone] Listener VERIFONE_LATEST_RESPONSE registrado.");
        },
    });
} else {
    console.warn("[Verifone] Listener ya estaba registrado: verifone_bus_listener");
}

// Registro seguro del debug opcional
if (!category.contains("verifone_debug_logger")) {
    category.add("verifone_debug_logger", {
        async setup(pos) {
            await pos.ready;

            const methods = pos.payment_methods.filter(
                (m) => m.use_payment_terminal === "verifone_middleware"
            );

            if (methods.length) {
                console.info("[Verifone] Métodos configurados:");
                console.table(
                    methods.map((m) => ({
                        Nombre: m.name,
                        IP: m.verifone_middleware_ip,
                        Puerto: m.verifone_middleware_port,
                    }))
                );
            } else {
                console.warn("[Verifone] No se detectaron métodos configurados.");
            }
        },
    });
} else {
    console.warn("[Verifone] Debug logger ya estaba registrado: verifone_debug_logger");
}
