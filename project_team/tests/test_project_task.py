# Copyright 2023 - TODAY Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProjectTask(TransactionCase):
    def setUp(self):
        super().setUp()

        self.user = self.env["res.users"].create(
            {
                "name": "Test User",
                "login": "test_user",
                "password": "test",
                "email": "test_user@example.com",
            }
        )
        self.project_team = self.env["project.team"].create(
            {"name": "Test Team", "user_ids": [(4, self.user.id)]}
        )
        self.project = self.env["project.project"].create(
            {"name": "Test Project", "team_id": self.project_team.id}
        )
        self.status = self.env["project.status"].create({"name": "Status 1"})
        self.task = self.env["project.task"].create(
            {"name": "Test Task", "project_id": self.project.id}
        )
        self.all_users = self.env["res.users"].search([])

    def test_compute_team_member_ids_with_team(self):
        self.task.team_id = self.project_team
        self.task._compute_team_member_ids()
        self.assertEqual(len(self.task.team_member_ids), 1)
        self.assertEqual(self.task.team_member_ids.name, "Test User")

    def test_compute_team_member_ids_without_team(self):
        self.task.team_id = False
        self.task._compute_team_member_ids()
        self.assertEqual(len(self.task.team_member_ids), len(self.all_users))
        self.assertEqual(
            set(self.task.team_member_ids.mapped("id")),
            set(self.all_users.mapped("id")),
        )

    def test_create_task(self):
        self.task = self.env["project.task"].create(
            {"name": "Test Task 2", "project_id": self.project.id}
        )
        self.assertEqual(len(self.task.team_member_ids), 1)
        self.assertEqual(self.task.team_member_ids.name, self.user.name)
