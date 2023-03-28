# Copyright 2023 - TODAY Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProjectStatus(models.Model):
    _inherit = "project.status"

    team_id = fields.Many2one("project.team", string="Team")
