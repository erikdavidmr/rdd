from odoo import http, fields
from odoo.http import request
import logging
import json

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

            # Buscar orden POS por referencia
            reference = payload.get("InvoiceID") or payload.get("LocalPaymentID")
            if not reference:
                _logger.warning("[Verifone] Falta referencia en el payload.")
                return {"status": "missing_reference"}

            order = request.env["pos.order"].sudo().search([("name", "=", reference)], limit=1)
            if not order:
                _logger.warning(f"[Verifone] No se encontró orden POS con nombre {reference}")
                return {"status": "order_not_found"}

            session = order.session_id
            if not session or not session.config_id:
                _logger.warning(f"[Verifone] Orden {order.name} sin sesión o config asociada.")
                return {"status": "no_session"}

            # Registrar el pago si fue aprobado
            if payload["status"] == "approved":
                journal = request.env['account.journal'].sudo().search([
                    ('name', 'ilike', 'Verifone'),
                    ('type', '=', 'cash'),
                ], limit=1)

                payment_method = (
                    order.payment_ids and order.payment_ids[0].payment_method_id
                ) or request.env['pos.payment.method'].sudo().search([
                    ('use_payment_terminal', '=', 'verifone_middleware')
                ], limit=1)

                if not journal:
                    _logger.warning("[Verifone] Diario 'Verifone' no encontrado.")
                elif not payment_method:
                    _logger.warning("[Verifone] Método de pago 'verifone_middleware' no encontrado.")
                else:
                    payment = request.env["pos.payment"].sudo().create({
                        "amount": payload["amount"],
                        "payment_date": fields.Date.context_today(request),
                        "payment_method_id": payment_method.id,
                        "journal_id": journal.id,
                        "pos_order_id": order.id,
                        "transaction_id": payload.get("auth_code") or payload.get("transaction_id"),
                        "verifone_payload_raw": json.dumps(payload),
                        "verifone_status": payload.get("status"),
                        "verifone_card_type": payload.get("card_type"),
                    })
                    _logger.info(f"[Verifone] Pago aprobado registrado en orden {order.name}")

                    # Recalcular pagos y actualizar estado si está completamente pagada
                    order._compute_amount_all()
                    if order.amount_paid >= order.amount_total:
                        order.state = 'paid'
                        _logger.info(f"[Verifone] Orden {order.name} marcada como pagada.")

            elif payload["status"] == "declined":
                _logger.warning(f"[Verifone] Pago rechazado para orden {order.name}")

            # Enviar evento al POS
            payload["type"] = "VERIFONE_LATEST_RESPONSE"
            request.env["bus.bus"].sudo().sendone(
                (request.env.cr.dbname, "pos.config", session.config_id.id),
                payload
            )

            _logger.info(f"[Verifone] Notificación enviada al POS '{session.config_id.name}' para orden {order.name}")
            return {"status": "notified"}

        except Exception as e:
            _logger.exception("[Verifone] Excepción en webhook_pago")
            return {"status": "error", "message": str(e)}
