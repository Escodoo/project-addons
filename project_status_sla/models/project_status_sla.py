# Copyright 2024 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from datetime import timedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ProjectStatusSLA(models.Model):
    _name = "project.status.sla"
    _description = "Project Status SLA"

    project_id = fields.Many2one(
        comodel_name="project.project", string="Project", required=True
    )
    stage_id = fields.Many2one(
        comodel_name="project.status", string="Stage", required=True
    )
    days = fields.Integer(string="Days", default=0, required=True)
    hours = fields.Integer(string="Hours", default=0, required=True)
    note = fields.Char(string="Note")

    @api.model
    def check_sla(self):
        """Iterate through all SLAs and check the status for each project's SLA."""
        slas = self.search([])
        for sla in slas:
            sla._check_and_update_project_sla()

    def _calculate_sla_deadline(self):
        """Calculate the SLA deadline based on creation date, days, and hours."""
        return self.create_date + timedelta(days=self.days, hours=self.hours)

    def _log_sla_status(self, project, deadline):
        """Log important details related to SLA deadlines and expiration status."""
        _logger.info("Create Date: %s", self.create_date)
        _logger.info("Calculated Deadline: %s", deadline)
        _logger.info("Current Time: %s", fields.Datetime.now())
        _logger.info("Expired: %s", project.sla_expired)

    def _check_and_update_project_sla(self):
        """Check and update the project's SLA status based on the calculated deadline."""
        project = self.project_id
        deadline = self._calculate_sla_deadline()

        # Update project SLA deadline
        project.sla_deadline = deadline

        # Check if the SLA is expired
        project.sla_expired = deadline < fields.Datetime.now()

        # Log the details of the SLA check
        self._log_sla_status(project, deadline)

        # Create or update the project SLA history
        project._create_project_sla_history(self)
