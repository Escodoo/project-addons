# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, tools


class UnifiedTaskTicket(models.Model):
    _name = "unified.task.ticket"
    _description = "Unified Task and Ticket View"
    _auto = False
    _order = "id desc"

    name = fields.Char(string="Title", readonly=True)
    icon = fields.Char(string="Display Icon", readonly=True)
    res_model = fields.Selection(
        [
            ("project.task", "Task"),
            ("helpdesk.ticket", "Ticket"),
        ],
        string="Type",
        readonly=True,
    )
    res_id = fields.Integer(string="Resource ID", readonly=True)
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Assigned To",
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        readonly=True,
    )
    custom_stage_id = fields.Many2one(
        comodel_name="shared.custom.stage",
        string="Stage",
        group_expand="_read_group_custom_stage_ids",
    )

    def _read_group_custom_stage_ids(self, stages, domain, order):
        return self.env["shared.custom.stage"].search([], order=order)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    t.id AS id,
                    t.id AS res_id,
                    'project.task' AS res_model,
                    'fa-tasks' AS icon,
                    t.name AS name,
                    (
                        SELECT user_id
                        FROM project_task_user_rel
                        WHERE task_id = t.id LIMIT 1
                    ) AS user_id,
                    t.company_id AS company_id,
                    COALESCE(
                        t.custom_stage_id,
                        (
                            SELECT s.id
                            FROM shared_custom_stage s
                            WHERE s.is_default = true
                            AND (s.company_id = t.company_id OR s.company_id IS NULL)
                            ORDER BY s.company_id DESC
                            LIMIT 1
                        )
                    ) AS custom_stage_id
                FROM project_task t

                UNION ALL

                SELECT
                    h.id + 1000000 AS id,
                    h.id AS res_id,
                    'helpdesk.ticket' AS res_model,
                    'fa-ticket' AS icon,
                    h.name AS name,
                    h.user_id AS user_id,
                    h.company_id AS company_id,
                    COALESCE(
                        h.custom_stage_id,
                        (
                            SELECT s.id
                            FROM shared_custom_stage s
                            WHERE s.is_default = true
                            AND (s.company_id = h.company_id OR s.company_id IS NULL)
                            ORDER BY s.company_id DESC
                            LIMIT 1
                        )
                    ) AS custom_stage_id
                FROM helpdesk_ticket h
            )
        """
        )

    def write(self, vals):
        # pylint: disable=method-required-super
        if "custom_stage_id" in vals:
            for record in self:
                original_record = (
                    self.env[record.res_model].sudo().browse(record.res_id)
                )
                original_record.write(
                    {
                        "custom_stage_id": vals["custom_stage_id"],
                    }
                )
        return True

    def action_open_record(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": self.res_model,
            "res_id": self.res_id,
            "view_mode": "form",
            "target": "current",
        }
