from odoo import api, fields, models

import logging

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_pos_paymob = fields.Boolean(
        string="Paymob Payment Terminal",
        help="The transactions are processed by Paymob.",
    )
