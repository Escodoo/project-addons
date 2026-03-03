# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class HelpdeskTicket(models.Model):
    _inherit = ["helpdesk.ticket", "shared.stage.mixin"]
    _name = "helpdesk.ticket"
