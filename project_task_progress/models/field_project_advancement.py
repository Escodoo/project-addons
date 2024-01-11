from odoo import api, fields, models

class ProjectTask(models.Model):
    _inherit = "project.task"


    advancement_percentage = fields.Float(string='% ' 'Actual advancement')

    advancement_progress = fields.Float(
        string='Actual advancement',
        compute='_compute_progress_bar',
        store=True,
        readonly=True,
    )

    @api.depends('advancement_percentage')
    def _compute_progress_bar(self):
        for task in self:
            task.advancement_progress = task.advancement_percentage * 100






