/** @odoo-module */

import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

export class PaymentPaymob extends PaymentInterface {
    setup() {
        super.setup(...arguments);
        this.paymentNotificationResolver = null;
    }

    send_payment_request(uuid) {
        super.send_payment_request(uuid);
        return this._paymob_pay(uuid);
    }

    send_payment_cancel(order, uuid) {     
        super.send_payment_cancel(order, uuid);
        return this._paymob_cancel();
    }

    _paymob_pay(uuid) {
        const order = this.pos.get_order();
        const line = order.get_selected_paymentline();

        if (line.amount < 0) {
            this._show_error(_t("Cannot process negative payment amounts."));
            return Promise.resolve();
        }

        const paymentData = this._paymob_payment_data(order, line);

        // To prevent canceling the payment while the order is being created
        if (line.payment_status !== "force_done" && line.payment_status !== "waitingCard") {
            line.set_payment_status("waitingCapture");
        }
        
        return this._call_paymob(paymentData, 'order').then((response) => {
            return this._handle_paymob_response(response);
        });
    }

    _paymob_payment_data(order, line) {
        const timestamp = new Date().toISOString();
        return {
            amount_cents: line.amount,
            currency: this.pos.currency.name,
            merchant_order_id: `${timestamp}--${order.session_id.id}--${line.uuid}`,
            send_pay_notification_to_terminal_id:line.payment_method_id.id,
            terminal_id: line.payment_method_id.id,
            preferred_payment_method :"card",
            transaction_type:"sale",
            delivery_needed: "false",
        };
    }

    _paymob_cancel() {
        const order = this.pos.get_order();
        if (!order) {
            this._show_error(_t("No active order found to cancel the payment."));
            return Promise.resolve();
        }
        const line = order.get_selected_paymentline();
        this._showMsg("Payment Cancelled, Please make sure to cancel it from the terminal too", "Cancel Payment")
        if (!line) {
            return Promise.resolve(true);
        }
        return Promise.resolve(true);
    }
    

    _call_paymob(data, operation) {
        return this.pos.data
            .silentCall("pos.payment.method", "send_paymob_request", [
                [this.payment_method_id.id],
                data,
                operation,
            ])
            .catch(this._handle_connection_failure.bind(this));
    }

    _handle_connection_failure(data = {}) {
        const line = this.pending_paymob_line();
        if (line) {
            line.set_payment_status("retry");
        }
        this._show_error(_t("Could not connect to the Odoo server. Please check your internet connection and try again."));
        
        return Promise.reject(data);
    }
    

    async _handle_paymob_response(response) {
        const line = this.pending_paymob_line();
        if (!line) {
            this._show_error(_t("No pending Paymob payment line found."));
            return false;
        }

        if(!response){
            this._show_error(_t("An error occured while processing the payment, Please try again"));
            line.set_payment_status('force_done');
            return false;
        }

        if (response.error && response.error.status_code === 400) {
            this._show_error(_t(response.error.message));
            line.set_payment_status('force_done');
            return false;
        } else if (response.error) {
            this._show_error(_t(response.error.message));
            line.set_payment_status('force_done');
            return false;
        }


        line.set_payment_status("waitingCard");
        return await new Promise((resolve) => {
            this.paymentNotificationResolver = resolve;
        });
    }

    pending_paymob_line() {
        return this.pos.getPendingPaymentLine("paymob");
    }

    async handlePaymobStatusResponse() {
        const notification = await this.pos.data.silentCall(
            "pos.payment.method",
            "get_latest_paymob_status",
            [[this.payment_method_id.id]]
        );

        const line = this.pending_paymob_line();
        if (!line ) {
            return;
        }

        if (!notification){
            this._handle_connection_failure();
            return;
        }

        if (!notification.obj || !notification.obj.order || !notification.obj.order.merchant_order_id){
            return;
        }

        if (this.pos.get_order().session_id.id !== +notification.obj.order.merchant_order_id.split("--")[1]) {
            return;
        }
        
        if (line.uuid !== notification.obj.order.merchant_order_id.split("--")[2]) {
            return;
        }

        const error_occured = notification.obj.error_occured;
        const success = notification.obj.success;

        if (error_occured ===true){
            this._show_error("An error occured while processing the payment, Please check the terminal");
            this.paymentNotificationResolver(false);
            return false;
        }
        if (success===true){
            line.transaction_id = notification.obj.id;
            if (notification.obj.source_data){
                line.card_brand = notification.obj.source_data.card_type;
                line.card_no = notification.obj.source_data.pan;
    
            }
            if(notification.obj.data && notification.obj.data.extra_detail){
                line.cardholder_name = notification.obj.data.extra_detail.card_holder_name;
            }
            this.paymentNotificationResolver(true);
            return true;
        }
        this.paymentNotificationResolver(false);
        return false;
    }

    _showMsg(msg, title) {
        this.env.services.dialog.add(AlertDialog, {
            title: "Paymob " + title,
            body: msg,
        });
    }

    _show_error(msg) {
        this.env.services.dialog.add(AlertDialog, {
            title: _t("Paymob Error"),
            body: msg,
        });
    }

}
