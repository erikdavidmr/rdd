/** @odoo-module */

import { register_payment_method } from "@point_of_sale/app/store/pos_store";
import { PaymentPaymob } from "@pos_paymob/app/payment_paymob";

register_payment_method("paymob", PaymentPaymob);
