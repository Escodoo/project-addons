# Copyright 2024 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProjectStatusSLALine(models.Model):
    _name = "project.status.sla.line"
    _description = "Project Status SLA line"

    project_id = fields.Many2one(
        comodel_name="project.project", string="Project", required=True
    )
    sla_id = fields.Many2one(comodel_name="project.status.sla", string="SLA")
    stage_id = fields.Many2one(
        comodel_name="project.status",
        string="Stage",
    )
    sla_deadline = fields.Datetime(string="SLA Deadline")
    sla_expired = fields.Boolean(string="SLA Expired")
    reached_date = fields.Datetime(string="Reached Date")
    status = fields.Selection(
        selection=[("not_met", "Not Met"), ("met", "Met")], string="Status"
    )
