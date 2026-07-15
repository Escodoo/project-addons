# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools.float_utils import float_compare


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    exceeds_project_purchase_budget = fields.Boolean(
        compute="_compute_exceeds_project_purchase_budget",
        copy=False,
        help="True when confirming this order would make at least one "
        "linked project exceed its purchase budget percentage. "
        "Never copied on duplicate; always recomputed from current budget.",
    )

    def _get_project_amounts_from_order(self):
        """Map project -> amount from this PO allocated via analytic distribution."""
        self.ensure_one()
        Project = self.env["project.project"]
        amounts = {}
        analytic_ids = set()
        for line in self.order_line:
            distribution = line.analytic_distribution or {}
            analytic_ids.update(int(account_id) for account_id in distribution)
        if not analytic_ids:
            return amounts
        projects = Project.search([("analytic_account_id", "in", list(analytic_ids))])
        project_by_analytic = {
            project.analytic_account_id.id: project for project in projects
        }
        for line in self.order_line:
            distribution = line.analytic_distribution or {}
            for account_id_str, percent in distribution.items():
                account_id = int(account_id_str)
                project = project_by_analytic.get(account_id)
                if not project:
                    continue
                contribution = percent / 100.0
                amount = line.price_subtotal * contribution
                amount = project._convert_to_project_currency(
                    amount,
                    line.currency_id,
                    line.company_id,
                )
                amounts[project.id] = amounts.get(project.id, 0.0) + amount
        return amounts

    def _order_exceeds_any_project_budget(self):
        """Return True if this PO would push any controlled project over budget."""
        self.ensure_one()
        Project = self.env["project.project"]
        project_amounts = self._get_project_amounts_from_order()
        if not project_amounts:
            return False
        projects = Project.browse(list(project_amounts.keys()))
        for project in projects:
            if not project._budget_control_enabled():
                continue
            budget = project.purchase_budget_amount
            # Exclude this order from spent so draft/reconfirm is compared fairly
            spent = project._get_confirmed_purchase_spent(
                exclude_order_ids=self.ids,
            )
            projected = spent + project_amounts[project.id]
            if (
                float_compare(
                    projected,
                    budget,
                    precision_rounding=project.currency_id.rounding,
                )
                > 0
            ):
                return True
        return False

    def _compute_exceeds_project_purchase_budget(self):
        # No @api.depends: always recompute on access so project % changes
        # are reflected without stale cache on draft POs.
        for order in self:
            order.exceeds_project_purchase_budget = (
                order._order_exceeds_any_project_budget()
            )

    def copy_data(self, default=None):
        """Ensure budget exceed flag is never copied to a duplicated PO."""
        data_list = super().copy_data(default=default)
        for data in data_list:
            # Computed with copy=False, but strip explicitly so defaults /
            # future store=True cannot carry over the source order's signal.
            data.pop("exceeds_project_purchase_budget", None)
        return data_list

    def write(self, vals):
        projects_before = self._get_affected_budget_projects()
        res = super().write(vals)
        projects_after = self._get_affected_budget_projects()
        (projects_before | projects_after).invalidate_recordset(
            [
                "purchase_budget_sale_amount",
                "purchase_budget_amount",
                "purchase_spent_amount",
                "purchase_remaining_amount",
                "purchase_consumed_percent",
                "project_contribution_amount",
            ]
        )
        return res

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._get_affected_budget_projects().invalidate_recordset(
            [
                "purchase_budget_sale_amount",
                "purchase_budget_amount",
                "purchase_spent_amount",
                "purchase_remaining_amount",
                "purchase_consumed_percent",
                "project_contribution_amount",
            ]
        )
        return orders

    def _get_affected_budget_projects(self):
        """Projects impacted by analytic distribution on these orders."""
        analytic_ids = set()
        for line in self.mapped("order_line"):
            distribution = line.analytic_distribution or {}
            analytic_ids.update(int(account_id) for account_id in distribution)
        if not analytic_ids:
            return self.env["project.project"]
        return self.env["project.project"].search(
            [("analytic_account_id", "in", list(analytic_ids))]
        )
