# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SharedCustomStage(models.Model):
    _name = "shared.custom.stage"
    _description = "Shared Custom Stage"
    _order = "sequence, id"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        index=True,
    )
    is_default = fields.Boolean(string="Default Stage", default=False)

    @api.constrains("is_default", "company_id")
    def _check_single_default(self):
        for record in self:
            if record.is_default:
                domain = [("is_default", "=", True), ("id", "!=", record.id)]
                if record.company_id:
                    domain.append(("company_id", "=", record.company_id.id))
                else:
                    domain.append(("company_id", "=", False))

                if self.search_count(domain) > 0:
                    raise ValidationError(_("There can only be one default stage."))

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        return self.search([], order=order)
