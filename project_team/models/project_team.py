# Copyright 2023 - TODAY Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class ProjectTeam(models.Model):
    _name = "project.team"
    _description = "Project Team"

    name = fields.Char(string="Team Name")
    user_ids = fields.Many2many("res.users", string="Team Members")

    @api.constrains("user_ids", "name")
    def _check_name(self):
        for record in self:
            if not record.name:
                raise ValidationError(_("Please provide a name team !"))
