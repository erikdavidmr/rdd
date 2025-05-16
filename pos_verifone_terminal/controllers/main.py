from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class VerifoneWebhook(http.Controller):
    @http.route('/verifone/webhook_pago', type='json', auth='none', csrf=False)
    def webhook_pago(self):
        try:
            payload = request.get_json_data()
            _logger.info("[Verifone] Payload recibido: %s", payload)

            # Validar token
            expected_token = request.env['ir.config_parameter'].sudo().get_param("verifone.webhook.token")
            token = request.httprequest.headers.get("X-Verifone-Token")
            if not expected_token or token != expected_token:
                _logger.warning("[Verifone] Token inválido o no configurado.")
                return {"status": "unauthorized"}

            # Obtener sesión POS desde merchant_order_id
            merchant_order_id = payload.get("merchant_order_id", "")
            parts = merchant_order_id.split("--")
            if len(parts) < 3:
                _logger.error("[Verifone] merchant_order_id malformado: %s", merchant_order_id)
                return {"status": "invalid_merchant_order_id"}

            pos_session_id = int(parts[1])
            session = request.env['pos.session'].sudo().browse(pos_session_id)
            if not session or not session.exists():
                _logger.warning("[Verifone] No se encontró sesión POS con ID %s", pos_session_id)
                return {"status": "no_session"}

            # Enviar notificación al POS
            session.config_id._notify("VERIFONE_LATEST_RESPONSE", payload)

            _logger.info("[Verifone] Notificación enviada al POS Config ID %s", session.config_id.id)
            return {"status": "notified"}

        except Exception as e:
            _logger.exception("[Verifone] Excepción en webhook_pago")
            return {"status": "error", "message": str(e)}
