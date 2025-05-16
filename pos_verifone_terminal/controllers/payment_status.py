from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)


class VerifoneStatusController(http.Controller):

    @http.route('/verifone/payment_status', type='http', auth='public', csrf=False)
    def payment_status(self, **kwargs):
        reference = kwargs.get('reference')
        if not reference:
            return request.make_response(
                json.dumps({'status': 'missing_reference'}),
                headers=[('Content-Type', 'application/json')],
                status=400
            )

        _logger.info(f"[Verifone] Consulta de estado para referencia: {reference}")

        order = request.env['pos.order'].sudo().search([('name', '=', reference)], limit=1)
        if not order:
            return request.make_response(
                json.dumps({'status': 'not_found'}),
                headers=[('Content-Type', 'application/json')]
            )

        status = 'approved' if order.amount_total == order.amount_paid else 'pending'

        result = {
            'status': status,
            'card_type': order.statement_ids.mapped('journal_id').name[0] if order.statement_ids else '',
            'transaction_id': order.pos_reference,
        } if status == 'approved' else {'status': 'pending'}

        return request.make_response(
            json.dumps(result),
            headers=[('Content-Type', 'application/json')]
        )
