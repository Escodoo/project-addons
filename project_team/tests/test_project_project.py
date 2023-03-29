# Copyright 2023 - TODAY Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProjectProject(TransactionCase):
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
        self.team1 = self.env["project.team"].create(
            {"name": "Team 1", "user_ids": [(4, self.user.id)]}
        )
        self.team2 = self.env["project.team"].create({"name": "Team 2"})
        self.status1 = self.env["project.status"].create(
            {"name": "Status 1", "team_id": self.team1.id}
        )
        self.status2 = self.env["project.status"].create(
            {"name": "Status 2", "team_id": self.team2.id}
        )
        self.status3 = self.env["project.status"].create(
            {"name": "Status 3", "team_id": False}
        )
        self.project = self.env["project.project"].create(
            {"name": "Test Project", "team_id": self.team1.id}
        )
        self.status_pending = self.env["project.status"].browse(1)
        self.status_progress = self.env["project.status"].browse(2)
        self.status_complete = self.env["project.status"].browse(3)

    def test_read_group_status_ids(self):
        self.assertIsNotNone(self.user)
        statuses = self.env["project.status"].search([])
        self.assertTrue(statuses)
        order = "name ASC"
        domain = expression.OR(
            [[("team_id", "=", False)], [("team_id.user_ids", "in", [self.user.id])]]
        )
        status_ids = statuses._search(
            domain, order=order, access_rights_uid=SUPERUSER_ID
        )
        result = statuses.browse(status_ids)
        expected_statuses = (
            self.status_complete
            + self.status_progress
            + self.status_pending
            + self.status1
            + self.status3
        )
        self.assertEqual(result, expected_statuses)

    def test_create(self):
        self.project_team = self.env["project.team"].create(
            {"name": "Test Team", "user_ids": [(4, self.user.id)]}
        )
        self.project_novo = self.env["project.project"].create(
            {"name": "Test Project 2", "team_id": self.project_team.id}
        )
        self.status_team = self.env["project.status"].create(
            {"name": "Status 1", "team_id": self.project_team.id}
        )
        self.assertEqual(self.project_novo.name, "Test Project 2")
        self.assertEqual(self.project_novo.team_id, self.project_team)
        self.assertEqual(self.status_team.id, self.status_team.id)

    def test_onchange_team_id(self):
        self.project_team = self.env["project.team"].create(
            {"name": "Test Team", "user_ids": [(4, self.user.id)]}
        )
        self.project_novo = self.env["project.project"].create(
            {"name": "Test Project 2", "team_id": self.project_team.id}
        )
        self.status_team = self.env["project.status"].create(
            {"name": "Status 1", "team_id": self.project_team.id}
        )
        self.project_novo._onchange_team_id()
        self.assertEqual(self.project_novo.project_status_id, self.status_team)
        self.project_team2 = self.env["project.team"].create(
            {"name": "Test Team 2", "user_ids": [(4, self.user.id)]}
        )
        self.project_novo.team_id = False
        self.status_team.team_id = False
        self.project_novo._onchange_team_id()
        self.assertFalse(self.project_novo.team_id)

    def test_check_name(self):
        self.team = self.env["project.team"].create(
            {"name": "Test Team", "user_ids": [(4, self.user.id)]}
        )
        self.team._check_name()
        self.assertFalse(self.team._check_name())
        with self.assertRaises(ValidationError):
            self.team.name = False
            self.team._check_name()
            self.assertTrue(self.team._check_name())
