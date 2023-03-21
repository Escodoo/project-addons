# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProjectSlaLine(models.Model):
    _name = "project.sla.line"
    _description = "SLA Line"
    _order = "deadline"

    task_id = fields.Many2one(comodel_name="project.task", string="Task")
    sla_id = fields.Many2one(comodel_name="project.sla", string="SLA")
    status = fields.Selection(
        selection=[("not_met", "Not Met"), ("met", "Met")], string="Status"
    )
    deadline = fields.Datetime(
        string="Deadline",
    )
    reached_date = fields.Datetime(string="Reached Date")
    sla_target_stage_id = fields.Many2one(
        comodel_name="project.task.type",
        string="Target Stage",
        related="sla_id.target_stage_id",
    )
