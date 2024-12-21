from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestProjectSLA(TransactionCase):
    def setUp(self):
        super().setUp()
        self.project = self.env.ref("project.project_project_1")
        self.project.write(
            {"project_status": self.env.ref("project_status.project_status_pending").id}
        )
        self.stage = self.env.ref("project_status.project_status_complete")
        self.sla = self.env["project.status.sla"].create(
            {
                "project_id": self.project.id,
                "stage_id": self.stage.id,
                "days": 5,
                "hours": 4,
                "note": "Test SLA",
            }
        )

    def test_sla_deadline_calculation(self):
        """Test if the SLA deadline is correctly calculated."""
        deadline = self.sla._calculate_sla_deadline()
        expected_deadline = self.sla.create_date + timedelta(
            days=self.sla.days, hours=self.sla.hours
        )
        self.assertEqual(
            deadline, expected_deadline, "SLA deadline calculation is incorrect."
        )

    def test_sla_expiration_check(self):
        """Test if the SLA expiration is set correctly."""
        # Set a past deadline to ensure the SLA is expired
        past_date = fields.Datetime.now() - timedelta(days=10)
        self.sla.create_date = past_date

        self.sla._check_and_update_project_sla()
        self.assertTrue(
            self.project.sla_expired,
            "SLA expiration was not correctly identified as True.",
        )

    def test_sla_not_expired(self):
        """Test if the SLA is still valid (not expired)."""
        # Ensure the deadline is in the future
        self.sla._check_and_update_project_sla()
        self.assertFalse(
            self.project.sla_expired, "SLA was incorrectly identified as expired."
        )

    def test_sla_history_creation(self):
        """Test if SLA history is created properly."""
        self.sla._check_and_update_project_sla()
        history_count = self.env["project.status.sla.line"].search_count(
            [("sla_id", "=", self.sla.id)]
        )
        self.assertEqual(history_count, 1, "SLA history was not created correctly.")

    def test_sla_line_creation(self):
        """Test if the SLA line is created correctly for the project."""
        self.project.sla_expired = True
        self.project.sla_deadline = fields.Datetime.now() + timedelta(days=5)
        self.project._create_project_sla_history(self.sla)

        sla_lines = self.env["project.status.sla.line"].search(
            [("project_id", "=", self.project.id)]
        )
        self.assertEqual(len(sla_lines), 1, "SLA line was not created correctly.")
        self.assertEqual(sla_lines.status, "not_met", "SLA status was incorrect.")

    def test_no_duplicate_sla_lines(self):
        """Test that SLA history is not created again if it already exists."""
        self.project.sla_expired = True
        self.project._create_project_sla_history(self.sla)

        # Attempt to create again
        self.project._create_project_sla_history(self.sla)

        sla_lines = self.env["project.status.sla.line"].search(
            [("project_id", "=", self.project.id)]
        )
        self.assertEqual(len(sla_lines), 1, "Duplicate SLA line was created.")
