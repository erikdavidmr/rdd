/** @odoo-module **/

import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface";
import { _t } from "@web/core/l10n/translation";

export class PaymentVerifoneMiddleware extends PaymentInterface {
    setup() {
        super.setup(...arguments);
        this.paymentNotificationResolver = null;
    }

    async send_payment_request(uuid) {
        const order = this.pos.get_order();
        const pay_line = order.get_selected_paymentline();

        const config = await this.pos.data.silentCall(
            "pos.payment.method",
            "get_verifone_config",
            [[this.payment_method_id.id]]
        );

        const ip = config.verifone_middleware_ip;
        const port = config.verifone_middleware_port;
        const url = `http://${ip}:${port}/pay`;

        const payload = {
            amount: pay_line.amount,
            reference: order.name,
            pos_id: this.pos.config.name,
            LocalPaymentID: order.name,
            InvoiceID: order.name,
            Lane: this.pos.config.name,
            Venue: this.pos.config.name,
            paymentline_uuid: pay_line.uuid,
            merchant_order_id: `${new Date().toISOString()}--${order.session_id?.id || "nosession"}--${pay_line.uuid}`,
        };

        pay_line.set_payment_status("waitingCard");

        try {
            const response = await fetch(url, {
                method: "POST",
                body: JSON.stringify(payload),
                headers: { "Content-Type": "application/json" },
            });

            if (!response.ok) {
                throw new Error("Middleware responded with status " + response.status);
            }

            const result = await response.json();
            console.log("[Verifone] Middleware respondió:", result);

            if (result.status === "received") {
                return await new Promise((resolve) => {
                    console.log("[Verifone] Esperando confirmación de terminal...");
                    this.paymentNotificationResolver = resolve;
                });
            } else {
                return this._handle_error(result.message || _t("No se pudo iniciar el pago."));
            }
        } catch (error) {
            return this._handle_error(error.message || _t("Error de conexión con la terminal."));
        }
    }

    async handleVerifoneStatusResponse(payload = {}) {
    console.log("[Verifone] Entrando a handleVerifoneStatusResponse:", payload);
        const line = this.pos.getPendingPaymentLine("verifone_middleware");
        if (!line) {
            console.warn("[Verifone] No se encontró línea de pago pendiente.");
            return;
        }

        const expectedUuid = line.uuid;
        const receivedUuid = payload.paymentline_uuid;

        if (expectedUuid !== receivedUuid) {
            console.warn(`[Verifone] UUID no coincide. Esperado: ${expectedUuid}, Recibido: ${receivedUuid}`);
            this.paymentNotificationResolver?.(false);
            return;
        }


        console.log("[Verifone] Procesando respuesta de terminal:", payload);

        if (payload.status === "approved") {
            line.set_payment_status("done");
            line.transaction_id = payload.auth_code || payload.transaction_id;
            line.card_type = payload.card_type || "Verifone";

            this.env.services.notification.add(_t("Pago Verifone aprobado correctamente."), {
                type: "success",
            });

            if (this.paymentNotificationResolver) {
                console.log("[Verifone] Resolviendo promesa de pago con éxito.");
                this.paymentNotificationResolver(true);
            }
        } else if (payload.status === "declined") {
            line.set_payment_status("retry");
            this._show_error(payload.message || "Pago rechazado por la terminal.");
            this.paymentNotificationResolver?.(false);
        } else {
            line.set_payment_status("retry");
            this._show_error("Respuesta desconocida desde terminal Verifone.");
            this.paymentNotificationResolver?.(false);
        }
    }

    _handle_error(msg) {
        this._show_error(msg);
        return false;
    }

    _show_error(msg, title) {
        this.env.services.dialog.add(AlertDialog, {
            title: title || _t("Error con la terminal"),
            body: msg,
        });
    }
}
