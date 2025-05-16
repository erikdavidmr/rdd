from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    verifone_middleware_ip = fields.Char("Verifone Middleware IP")
    verifone_middleware_port = fields.Integer("Verifone Middleware Port", default=5000)

    def _get_payment_terminal_selection(self):
        res = super()._get_payment_terminal_selection()
        res.append(("verifone_middleware", _("Verifone Terminal (LAN Middleware)")))
        return res

    @api.constrains("use_payment_terminal", "verifone_middleware_ip", "verifone_middleware_port")
    def _check_verifone_middleware_config(self):
        for method in self:
            if method.use_payment_terminal == "verifone_middleware":
                if not method.verifone_middleware_ip:
                    raise ValidationError(_("IP no configurada para '%s'") % method.display_name)
                if not method.verifone_middleware_port or not (1 <= method.verifone_middleware_port <= 65535):
                    raise ValidationError(_("Puerto no válido para '%s'") % method.display_name)

    def export_for_ui_data(self, session=None):
        result = super().export_for_ui_data(session)
        if not isinstance(result, list):
            _logger.error("Expected list from export_for_ui_data, got: %s", type(result))
            return []

        for method in result:
            if (
                    method.get("use_payment_terminal") == "verifone_middleware"
                    and method.get("id")
            ):
                try:
                    rec = self.browse(method["id"])
                    method["verifone_middleware_ip"] = rec.verifone_middleware_ip
                    method["verifone_middleware_port"] = rec.verifone_middleware_port
                    _logger.debug(
                        "[Verifone] Expuesto método '%s' con IP %s y puerto %s",
                        rec.display_name,
                        rec.verifone_middleware_ip,
                        rec.verifone_middleware_port,
                    )
                except Exception as e:
                    _logger.exception("Error exportando datos de Verifone al POS: %s", e)

        return result

    def get_verifone_config(self):
        self.ensure_one()
        return {
            "verifone_middleware_ip": self.verifone_middleware_ip,
            "verifone_middleware_port": self.verifone_middleware_port,
        }
