/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
    async setup() {
        await super.setup(...arguments);
        this.onNotified("PAYMOB_LATEST_RESPONSE", (payload) => {
            const paymentLine = this.getPendingPaymentLine("paymob");
            if (!paymentLine) {
                return;
            }

            const paymentMethod = paymentLine.payment_method_id;
            if (!paymentMethod) {
                return;
            }

            const terminal = paymentMethod.payment_terminal;
            if (!terminal || !terminal.paymentNotificationResolver) {
                return;
            }

            terminal.handlePaymobStatusResponse();
        });
    },
});
