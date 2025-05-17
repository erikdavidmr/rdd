from odoo import models, fields


class PosPayment(models.Model):
    _inherit = "pos.payment"

    verifone_payload_raw = fields.Text(
        string="Verifone Payload (JSON)",
        help="Respuesta completa recibida desde la terminal Verifone."
    )
    verifone_status = fields.Char(
        string="Verifone Status",
        help="Estado final de la transacción Verifone (approved, declined, etc.)"
    )
    verifone_card_type = fields.Char(
        string="Verifone Card Type",
        help="Tipo de tarjeta reportado por la terminal Verifone."
    )

