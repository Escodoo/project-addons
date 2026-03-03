# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestUnifiedTaskTicket(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.ref("base.main_company")
        cls.user = cls.env.user

        cls.default_stage = cls.env["shared.custom.stage"].create(
            {
                "name": "Default Stage",
                "is_default": True,
                "company_id": cls.company.id,
                "sequence": 1,
            }
        )
        cls.other_stage = cls.env["shared.custom.stage"].create(
            {
                "name": "Other Stage",
                "is_default": False,
                "company_id": cls.company.id,
                "sequence": 2,
            }
        )

        cls.project = cls.env["project.project"].create({"name": "Test Project"})
        cls.task = cls.env["project.task"].create(
            {
                "name": "Test Task",
                "project_id": cls.project.id,
            }
        )

        cls.team = cls.env["helpdesk.ticket.team"].create({"name": "Test Team"})
        cls.ticket = cls.env["helpdesk.ticket"].create(
            {
                "name": "Test Ticket",
                "team_id": cls.team.id,
                "description": "Test Ticket",
            }
        )

    def test_search_data(self):
        """Ensure both tasks and tickets appear in the view with correct icons"""
        self.env["unified.task.ticket"].flush_model()

        task_view = self.env["unified.task.ticket"].search(
            [("res_model", "=", "project.task"), ("res_id", "=", self.task.id)]
        )
        ticket_view = self.env["unified.task.ticket"].search(
            [("res_model", "=", "helpdesk.ticket"), ("res_id", "=", self.ticket.id)]
        )

        self.assertTrue(task_view.exists())
        self.assertEqual(task_view.name, "Test Task")
        self.assertEqual(task_view.icon, "fa-tasks")

        self.assertTrue(ticket_view.exists())
        self.assertEqual(ticket_view.name, "Test Ticket")
        self.assertEqual(ticket_view.icon, "fa-ticket")

    def test_default_stage(self):
        """Ensure the view shows the default stage when no custom_stage_id is set"""
        self.task.write({"custom_stage_id": False})
        self.env["unified.task.ticket"].flush_model()

        view_record = self.env["unified.task.ticket"].search(
            [("res_model", "=", "project.task"), ("res_id", "=", self.task.id)]
        )

        self.assertEqual(view_record.custom_stage_id.id, self.default_stage.id)

    def test_change_stage_id(self):
        """Ensure writing to the view updates the actual underlying record"""
        view_record = self.env["unified.task.ticket"].search(
            [("res_model", "=", "project.task"), ("res_id", "=", self.task.id)]
        )

        view_record.write({"custom_stage_id": self.other_stage.id})

        self.assertEqual(self.task.custom_stage_id.id, self.other_stage.id)

    def test_action_open_record(self):
        """Ensure the action returns the correct dictionary for navigation"""
        view_record = self.env["unified.task.ticket"].search(
            [("res_model", "=", "helpdesk.ticket"), ("res_id", "=", self.ticket.id)]
        )

        action = view_record.action_open_record()

        self.assertEqual(action["res_model"], "helpdesk.ticket")
        self.assertEqual(action["res_id"], self.ticket.id)
        self.assertEqual(action["view_mode"], "form")
        self.assertEqual(action["type"], "ir.actions.act_window")
