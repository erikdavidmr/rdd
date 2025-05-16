import hashlib
import hmac
import json
import logging
import pprint

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PosPaymobController(http.Controller):

    @http.route(
        "/pos_paymob/notification",
        type="json",
        auth="public",
        csrf=False,
        methods=["POST"],
    )
    def paymob_return(self, **kwargs):
        raw_data = request.httprequest.get_data()

        try:
            json_data = json.loads(raw_data)
        except json.JSONDecodeError:
            _logger.error("Invalid JSON data received.")
            return {"error": "Invalid JSON data"}, 400

        _logger.info("Paymob Parsed JSON data: %s", pprint.pformat(json_data))
        event_type = json_data.get("type")

        if event_type == "TRANSACTION":
            return self._handle_transaction(json_data)

        else:
            _logger.error("Invalid data received %s", json_data)
            return {"error": "Invalid event type"}, 400

    def _handle_transaction(self, json_data):
        try:

            # Verify HMAC
            received_hmac = request.httprequest.args.get("hmac")
            terminal_id = json_data["obj"]["terminal_id"]
            record = (
                request.env["pos.payment.method"]
                .sudo()
                .search([("paymob_terminal_id", "=", terminal_id)], limit=1)
            )
            hmac_secret = record.paymob_hmac if record else None
            calculated_hmac = self._calculate_hmac(hmac_secret, json_data)
            if received_hmac != calculated_hmac:
                _logger.error("HMAC verification failed")
                return {"error": "HMAC mismatch"}, 400

            # extract information and validate
            terminal_id = json_data["obj"]["terminal_id"]
            transaction_info = json_data["obj"]["order"]["merchant_order_id"]
            time_stamp, pos_session_id, order_uuid = transaction_info.split("--")

            paymob_pm_sudo = (
                request.env["pos.payment.method"]
                .sudo()
                .search([("paymob_terminal_id", "=", terminal_id)], limit=1)
            )
            if not paymob_pm_sudo:
                _logger.error("Terminal ID not found in odoo system")
                return {"error": "Terminal ID not found"}, 400
            pos_session_sudo = (
                request.env["pos.session"].sudo().browse(int(pos_session_id))
            )
            if not pos_session_sudo:
                _logger.error("POS session not found in odoo system")
                return {"error": "POS session not found"}, 400

            # update the transaction, notify the POS session
            paymob_pm_sudo.paymob_latest_response = json.dumps(json_data)
            pos_session_sudo.config_id._notify(
                "PAYMOB_LATEST_RESPONSE", {}
            )
            return "OK", 200

        except Exception as e:
            _logger.error("Error handling transaction: %s", e)
            return {"error": "Error handling transaction"}, 400

    def _calculate_hmac(self, key, json_data):
        try:
            data = json_data["obj"].copy()
            data["order"] = data["order"]["id"]

            data["is_3d_secure"] = "true" if data["is_3d_secure"] else "false"
            data["is_auth"] = "true" if data["is_auth"] else "false"
            data["is_capture"] = "true" if data["is_capture"] else "false"
            data["is_refunded"] = "true" if data["is_refunded"] else "false"
            data["is_standalone_payment"] = (
                "true" if data["is_standalone_payment"] else "false"
            )
            data["is_voided"] = "true" if data["is_voided"] else "false"
            data["success"] = "true" if data["success"] else "false"
            data["error_occured"] = "true" if data["error_occured"] else "false"
            data["has_parent_transaction"] = (
                "true" if data["has_parent_transaction"] else "false"
            )
            data["pending"] = "true" if data["pending"] else "false"
            data["source_data_pan"] = data["source_data"]["pan"]
            data["source_data_type"] = data["source_data"]["type"]
            data["source_data_sub_type"] = data["source_data"]["sub_type"]

            concatenated_string = (
                str(data["amount_cents"])
                + str(data["created_at"])
                + str(data["currency"])
                + str(data["error_occured"])
                + str(data["has_parent_transaction"])
                + str(data["id"])
                + str(data["integration_id"])
                + str(data["is_3d_secure"])
                + str(data["is_auth"])
                + str(data["is_capture"])
                + str(data["is_refunded"])
                + str(data["is_standalone_payment"])
                + str(data["is_voided"])
                + str(data["order"])
                + str(data["owner"])
                + str(data["pending"])
                + str(data["source_data_pan"])
                + str(data["source_data_sub_type"])
                + str(data["source_data_type"])
                + str(data["success"])
            )
            calculated_hmac = hmac.new(
                key.encode("utf-8"), concatenated_string.encode("utf-8"), hashlib.sha512
            ).hexdigest()

            return calculated_hmac
        except Exception as e:
            _logger.error("Error calculating HMAC: %s", e)
            return None
