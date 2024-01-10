from odoo import api, fields, models

class ProjectTask(models.Model):
    _inherit = "project.task"


    advancement_percentage = fields.Float(string='% ' 'actual advancement')

    progress_bar = fields.Float(
        string='actual advancement',
        compute='_compute_progress_bar',
        store=True,
        readonly=True,
    )

    @api.depends('advancement_percentage')
    def _compute_progress_bar(self):
        for task in self:
            task.progress_bar = task.advancement_percentage * 100






