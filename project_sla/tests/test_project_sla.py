from odoo.tests.common import TransactionCase


class TestProjectSLA(TransactionCase):
    def setUp(self):
        super().setUp()
        self.project = self.env["project.project"].create(
            {
                "name": "Test Projects Project",
                "use_sla": True,
            }
        )

        self.stage_target_1 = self.env["project.task.type"].create(
            {
                "name": "Stage 1",
                "sequence": 20,
            }
        )
        self.partner_1 = self.env["res.partner"].create({"name": "Test Partner 1"})
        self.partner_2 = self.env["res.partner"].create({"name": "Test Partner 2"})

        self.sla = self.env["project.sla"].create(
            {
                "name": "Test SLA",
                "project_id": self.project.id,
                "partner_ids": [(4, self.partner_1.id)],
                "duration": 8,
                "target_stage_id": self.stage_target_1.id,
            }
        )

        self.task_1 = self.env["project.task"].create(
            {
                "name": "Test Task 1",
                "project_id": self.project.id,
                "partner_id": self.partner_1.id,
            }
        )
        self.task_2 = self.env["project.task"].create(
            {
                "name": "Test Task 2",
                "project_id": self.project.id,
                "partner_id": self.partner_2.id,
            }
        )
        self.task_1._sync_sla_lines()
        self.task_2._sync_sla_lines()

    def test_sla_task_ids(self):
        self.assertIn(
            self.task_1, self.sla.task_ids, "Test Task 1 should be in SLA Task IDs"
        )
        self.assertNotIn(
            self.task_2, self.sla.task_ids, "Test Task 2 should not be in SLA Task IDs"
        )

    def test_sla_reached_date(self):
        # Move task 1 to target stage after 5 days (within SLA duration)
        self.task_1.write({"stage_id": self.stage_target_1.id})
        self.task_1._sync_sla_lines()
        self.assertEqual(
            len(self.sla.sla_line_ids),
            1,
            "SLA Line should be created for the Task 1",
        )
        self.assertTrue(
            self.sla.sla_line_ids.reached_date,
            "Date reached should be set for the Task 1 SLA Line",
        )
