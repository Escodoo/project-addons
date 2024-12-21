# Copyright 2024 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# flake8: noqa: B950

from odoo import _, fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    sla_deadline = fields.Datetime(string="SLA Deadline")
    sla_expired = fields.Boolean(string="SLA Expired")

    def _prepare_sla_message(self, sla_line, sla):
        """Prepare the message to notify about the SLA status, including reached_date,
        SLA line ID, current stage, and estimated stage from project.status.sla."""
        current_stage = (
            self.project_status.name
        )  # Assuming project_status is the current stage
        sla_stage = (
            sla.stage_id.name
        )  # Fetching the estimated stage from project.status.sla

        # Format the dates explicitly
        estimated_date = (
            sla_line.sla_deadline.strftime("%d/%m/%Y %H:%M")
            if sla_line.sla_deadline
            else "N/A"
        )
        reached_date = (
            sla_line.reached_date.strftime("%d/%m/%Y %H:%M")
            if sla_line.reached_date
            else "N/A"
        )

        if self.sla_expired:
            message = _(
                "<p>The SLA for Project <b>%s</b> in Stage <b>%s</b> has been exceeded.</p>"
                "<p>Current Stage: <b>%s</b></p>"
                "<p>Estimated Stage: <b>%s</b></p>"
                "<p>SLA ID: <b>%s</b></p>"
                "<p>Estimated Date: <b>%s</b></p>"
                "<p>Reached Date: <b>%s</b></p>"
                % (
                    self.name,
                    current_stage,
                    current_stage,
                    sla_stage,
                    sla.id,
                    estimated_date,
                    reached_date,
                )
            )
        else:
            message = _(
                "<p>The SLA for Project <b>%s</b> in Stage <b>%s</b> has been successfully met within the proposed deadline.</p>"
                "<p>Current Stage: <b>%s</b></p>"
                "<p>Estimated Stage: <b>%s</b></p>"
                "<p>SLA ID: <b>%s</b></p>"
                "<p>Estimated Date: <b>%s</b></p>"
                "<p>Reached Date: <b>%s</b></p>"
                % (
                    self.name,
                    current_stage,
                    current_stage,
                    sla_stage,
                    sla.id,
                    estimated_date,
                    reached_date,
                )
            )
        return message

    def _post_sla_message(self, sla_line, sla):
        """Post a message to notify users about the SLA status, including additional information."""
        message = self._prepare_sla_message(sla_line, sla)
        self.message_post(
            body=message, message_type="notification", subtype="mail.mt_comment"
        )

    def _prepare_sla_line_values(self, sla):
        """Prepare the values to create an SLA line for the current project."""
        status = "not_met" if self.sla_expired else "met"
        return {
            "project_id": self.id,
            "stage_id": self.project_status.id,  # Assuming project_status is the current stage
            "sla_id": sla.id,
            "sla_deadline": self.sla_deadline,
            "sla_expired": self.sla_expired,
            "reached_date": fields.Datetime.now(),
            "status": status,
        }

    def _create_sla_line(self, sla):
        """Create a new SLA line record for the project."""
        sla_line_vals = self._prepare_sla_line_values(sla)
        return self.env["project.status.sla.line"].create(sla_line_vals)

    def _create_project_sla_history(self, sla):
        """Create SLA history records for the project if not already present."""
        # Check if SLA history already exists for this project and SLA
        existing_history_count = self.env["project.status.sla.line"].search_count(
            [("sla_id", "=", sla.id)]
        )

        # If history exists, do not create another one
        if existing_history_count:
            return

        # Create new SLA line and post a notification message
        sla_line = self._create_sla_line(sla)
        self._post_sla_message(sla_line, sla)
