import json
import logging
import pprint

import requests
from odoo import _, fields, models
from odoo.exceptions import AccessDenied, ValidationError

_logger = logging.getLogger(__name__)

BASE_URL = {
    "test": "https://accept-alpha.paymob.com/",
    "egy": "https://accept.paymob.com/",
    "are": "https://uae.paymob.com/",
    "omn": "https://oman.paymob.com/",
    "sau": "https://ksa.paymob.com/",
}


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    def _get_payment_terminal_selection(self):
        return super(PosPaymentMethod, self)._get_payment_terminal_selection() + [
            ("paymob", "Paymob")
        ]

    paymob_api_key = fields.Char("API Key", help="API Key for Paymob", groups="base.group_erp_manager")
    paymob_terminal_id = fields.Char("Terminal ID", help="Terminal ID for Paymob", groups="base.group_erp_manager")
    paymob_hmac = fields.Char("HMAC Secret", help="HMAC Secret", groups="base.group_erp_manager")
    paymob_latest_response = fields.Char(copy=False, groups="base.group_erp_manager")
    paymob_country_selection = fields.Selection(
        [
            ("test", "Test Mode"),
            ("egy", "Egypt"),
            ("omn", "Oman"),
            ("sau", "Saudi Arabia"),
            ("are", "United Arab Emirates"),
        ],
        string="Country",
    )

    def _is_write_forbidden(self, fields):
        return super(PosPaymentMethod, self)._is_write_forbidden(
            fields - {"paymob_latest_response"}
        )

    def get_latest_paymob_status(self):
        """
        Get the latest Paymob response for the POS Payment Method. Called from the POS front-end.
        """

        self.ensure_one()
        if not self.env.su and not self.env.user.has_group(
            "point_of_sale.group_pos_user"
        ):
            raise AccessDenied()

        latest_response = self.sudo().paymob_latest_response
        latest_response = json.loads(latest_response) if latest_response else False
        return latest_response

    def send_paymob_request(self, data, operation):
        """
        Send a request to Paymob API. Called from the POS front-end.
        """

        self.ensure_one()
        try:
            if not self.paymob_api_key:
                return {
                    "error": {
                        "status_code": 400,
                        "message": "Authentication Failed, Please set your API Key first.",
                    }
                }
            
            auth_url = self._get_paymob_endpoint("auth")
            auth_response = requests.post(auth_url, json={"api_key": self.paymob_api_key})
            token = auth_response.json().get("token", "")
            if auth_response.status_code != 201 or not token:
                return {
                    "error": {
                        "status_code": 400,
                        "message": "Authentication Failed, Please check your API key.",
                    }
                }

            url = self._get_paymob_endpoint(operation)
            if operation == "order":
                data = self.update_request_body(data, token)
                if not self.paymob_hmac:
                    # Prevent problems in the webhook
                    _logger.warning(
                        "HMAC Secret is not set for Paymob, while creating order."
                    )
                    return {
                        "error": {
                            "status_code": 400,
                            "message": "HMAC Secret is not set for Paymob, Please set it first.",
                        }
                    }
                if self.paymob_latest_response:
                    # Prevent using the same response for multiple orders
                    self.sudo().paymob_latest_response = ""

            headers = {
                "Content-Type": "application/json",
            }

            # Token is sent in the body for order creation
            if operation != "order":
                headers.update({"Authorization": f"Bearer {token}"})

            
            response = requests.post(url, json=data, headers=headers)
            if response.status_code != 201:
                return {
                    "error": {
                        "status_code": response.status_code,
                        "message": response.json().get("message", "Failed to create order. Please try again later."),
                    }
                }
            response_data = response.json()
            _logger.info(
                "Paymob create order response: %s", pprint.pformat(response_data)
            )
            return response_data
        
        except Exception as e:
            # If any error occurs when sending requests to Paymob
            _logger.error("Failed to create order in Paymob. %s", e)
            return {
                "error": {
                    "status_code": 400,
                    "message": "Failed to create order in Paymob. Please try again later.",
                }
            }

    def _get_paymob_endpoint(self, operation):
        """
        Get the Paymob endpoint based on the operation and country selection.
        """

        if not self.paymob_country_selection:
            raise ValidationError(_("Please select a country for Paymob."))
        endpoints = {
            "auth": "api/auth/tokens",
            "order": "api/ecommerce/orders",
            "hmac": "api/auth/hmac_secret/get_hmac",
        }
        return BASE_URL.get(self.paymob_country_selection) + endpoints.get(operation)

    def action_get_paymob_hmac(self):
        """
        Get HMAC Secret from Paymob and set it in the POS Payment Method.
        """

        self.ensure_one()
        
        if not self.paymob_api_key:
            raise ValidationError(_("Please set the API Key first."))
        
        # Authenticate with Paymob
        auth_url = self._get_paymob_endpoint("auth")
        auth_response = requests.post(auth_url, json={"api_key": self.paymob_api_key})
        token = auth_response.json().get("token", "")
        if auth_response.status_code != 201 or not token:
            _logger.error("Failed to Authenticate with Paymob. %s", auth_response.json())
            raise ValidationError(_("Failed to Authenticate with Paymob, Please check your API key."))
        
        # Get HMAC Secret
        hmac_url = self._get_paymob_endpoint("hmac")
        hmac_response = requests.get(hmac_url, headers={"Authorization": f"Bearer {token}"})
        hmac_secret = hmac_response.json().get("hmac_secret", "")
        if hmac_response.status_code != 201 or not hmac_secret:
            _logger.error("Failed to get HMAC Secret from Paymob. %s", hmac_response.json())
            raise ValidationError(_("Failed to get HMAC Secret from Paymob. Please try again later."))
        self.paymob_hmac = hmac_secret

        # Show success message
        message = "Your HMAC Secret has been successfully set."
        notification_type = "info"

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "message": message,
                "sticky": False,
                "type": notification_type,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def update_request_body(self, data, token):
        """
        Update the request body before sending it to Paymob.
        """
        data.update({"send_pay_notification_to_terminal_id": self.paymob_terminal_id})
        data.update({"terminal_id": self.paymob_terminal_id})
        data.update({"auth_token": token})
        if (self.paymob_country_selection or "").lower() == "omn":
            data.update({"amount_cents": int(data.get("amount_cents", 0) * 1000)})
        else:
            data.update({"amount_cents": int(data.get("amount_cents", 0) * 100)})
        return data
