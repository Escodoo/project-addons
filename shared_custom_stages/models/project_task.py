# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ProjectTask(models.Model):
    _inherit = ["project.task", "shared.stage.mixin"]
    _name = "project.task"
