# Copyright 2025 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    bank_usage = fields.Selection(
        selection=[
            ("expense", "Expense"),
            ("salary", "Salary"),
        ],
        string="Account Usage",
    )
