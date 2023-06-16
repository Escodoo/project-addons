# Copyright 2023 - TODAY Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    team_id = fields.Many2one(
        "project.team", string="Team", related="project_id.team_id"
    )
    team_member_ids = fields.Many2many(
        "res.users", string="Team Members", compute="_compute_team_member_ids"
    )

    @api.depends("team_id")
    def _compute_team_member_ids(self):
        for task in self:
            if task.team_id:
                team_members = task.team_id.user_ids.ids
                task.team_member_ids = [(6, 0, team_members)]
            else:
                all_users = self.env["res.users"].search([])
                if all_users:
                    task.team_member_ids = [(6, 0, all_users.ids)]

    @api.model
    def create(self, vals):
        task = super().create(vals)
        task._compute_team_member_ids()
        return task
