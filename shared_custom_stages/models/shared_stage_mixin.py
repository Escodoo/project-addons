# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SharedStageMixin(models.AbstractModel):
    _name = "shared.stage.mixin"
    _description = "Shared Stage Mixin"

    custom_stage_id = fields.Many2one(
        comodel_name="shared.custom.stage",
        string="Custom Stage",
        group_expand="_read_group_custom_stage_ids",
        tracking=True,
        index=True,
    )

    def _read_group_custom_stage_ids(self, stages, domain, order):
        return self.env["shared.custom.stage"].search([], order=order)
