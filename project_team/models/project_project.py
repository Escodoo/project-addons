# Copyright 2023 - TODAY Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api, fields, models
from odoo.osv import expression


class ProjectProject(models.Model):
    _inherit = "project.project"

    team_id = fields.Many2one("project.team", string="Team")
    project_status_id = fields.Many2one(
        "project.status",
        string="Project Status IDS",
        group_expand="_read_group_status_ids",
        copy=False,
        domain="[('team_id', '=', team_id)]",
        ondelete="restrict",
        index=True,
    )

    @api.model
    def _read_group_status_ids(self, statuses, domain, order):
        user = self.env.user
        search_domain = expression.OR(
            [[("team_id", "=", False)], [("team_id.user_ids", "in", [user.id])]]
        )
        status_ids = statuses._search(
            search_domain, order=order, access_rights_uid=SUPERUSER_ID
        )
        return statuses.browse(status_ids)

    @api.model
    def create(self, vals):
        project_status_id = vals.get("project_status_id")
        vals["project_status"] = project_status_id
        return super().create(vals)

    @api.onchange("team_id")
    def _onchange_team_id(self):
        if self.team_id:
            project_status_ids = self.env["project.status"].search(
                [("team_id", "=", self.team_id.id)]
            )
        else:
            project_status_ids = self.env["project.status"].search(
                [("team_id", "=", False)]
            )
        if project_status_ids:
            self.project_status_id = project_status_ids[0]
        else:
            self.project_status_id = False
        return {"project_status_id": self.project_status_id.id}
