# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import api, fields, models
from odoo.tools.float_utils import float_is_zero, float_round


class ProjectProject(models.Model):
    _inherit = "project.project"

    purchase_budget_percent = fields.Float(
        string="Purchase Budget %",
        help="Maximum percentage of the sale value that can be spent on "
        "purchases for this project. Set by the project manager.",
        digits=(16, 2),
        tracking=True,
    )
    purchase_budget_sale_override = fields.Monetary(
        string="Sale Amount Override",
        currency_field="currency_id",
        help="Optional manual sale amount used instead of linked sales "
        "orders when computing the purchase budget.",
        tracking=True,
    )
    purchase_budget_sale_amount = fields.Monetary(
        string="Sale Amount",
        compute="_compute_purchase_budget_kpis",
        currency_field="currency_id",
        help="Sale value used as the base for the purchase budget "
        "(linked sales orders, or the override when set).",
    )
    purchase_budget_amount = fields.Monetary(
        string="Purchase Budget",
        compute="_compute_purchase_budget_kpis",
        currency_field="currency_id",
        help="Planned purchase budget: sale amount × purchase budget %.",
    )
    purchase_spent_amount = fields.Monetary(
        string="Purchase Spent",
        compute="_compute_purchase_budget_kpis",
        currency_field="currency_id",
        help="Committed purchase spend from confirmed purchase orders "
        "allocated to this project via analytic distribution.",
    )
    purchase_remaining_amount = fields.Monetary(
        string="Purchase Remaining",
        compute="_compute_purchase_budget_kpis",
        currency_field="currency_id",
    )
    purchase_consumed_percent = fields.Float(
        string="Purchase Consumed %",
        compute="_compute_purchase_budget_kpis",
        digits=(16, 2),
    )
    project_contribution_amount = fields.Monetary(
        string="Project Contribution",
        compute="_compute_purchase_budget_kpis",
        currency_field="currency_id",
        help="Sale amount minus committed purchase spend "
        "(contribution after purchases).",
    )
    is_purchase_budget_manager = fields.Boolean(
        compute="_compute_is_purchase_budget_manager",
    )

    @api.depends_context("uid")
    def _compute_is_purchase_budget_manager(self):
        is_manager = self.env.user.has_group(
            "project_purchase_budget.group_purchase_budget_manager"
        )
        for project in self:
            project.is_purchase_budget_manager = is_manager

    def _get_purchase_budget_sale_orders(self):
        """Return confirmed sales orders linked to this project."""
        self.ensure_one()
        orders = self._get_sale_orders()
        if self.sale_order_id:
            orders |= self.sale_order_id
        return orders.filtered(lambda so: so.state in ("sale", "done"))

    def _convert_to_project_currency(self, amount, from_currency, company=None):
        """Convert amount from another currency to the project currency."""
        self.ensure_one()
        company = company or self.company_id or self.env.company
        to_currency = self.currency_id
        if not from_currency or from_currency == to_currency:
            return amount
        return from_currency._convert(
            amount,
            to_currency,
            company,
            date.today(),
        )

    def _get_confirmed_purchase_spent(self, exclude_order_ids=None):
        """Sum confirmed PO line subtotals allocated to this project's analytic."""
        self.ensure_one()
        if not self.analytic_account_id:
            return 0.0
        exclude_order_ids = exclude_order_ids or []
        analytic_id = str(self.analytic_account_id.id)
        domain = [("state", "in", ("purchase", "done"))]
        if exclude_order_ids:
            domain.append(("order_id", "not in", exclude_order_ids))
        query = self.env["purchase.order.line"].sudo()._search(domain)
        query.add_where(
            "purchase_order_line.analytic_distribution ? %s",
            [analytic_id],
        )
        query_string, query_param = query.select(
            '"purchase_order_line".id',
            "price_subtotal",
            "purchase_order_line.currency_id",
            "purchase_order_line.company_id",
            '"purchase_order_line".analytic_distribution',
        )
        self._cr.execute(query_string, query_param)
        spent = 0.0
        for row in self._cr.dictfetchall():
            distribution = row["analytic_distribution"] or {}
            if analytic_id not in distribution:
                continue
            contribution = distribution[analytic_id] / 100.0
            amount = row["price_subtotal"] * contribution
            currency = self.env["res.currency"].browse(row["currency_id"])
            company = self.env["res.company"].browse(row["company_id"])
            spent += self._convert_to_project_currency(amount, currency, company)
        return float_round(spent, precision_rounding=self.currency_id.rounding)

    def _get_purchase_budget_sale_base(self):
        """Return the sale amount used as budget base (override or linked SOs)."""
        self.ensure_one()
        if not float_is_zero(
            self.purchase_budget_sale_override,
            precision_rounding=self.currency_id.rounding,
        ):
            return self.purchase_budget_sale_override
        total = 0.0
        for order in self._get_purchase_budget_sale_orders():
            total += self._convert_to_project_currency(
                order.amount_untaxed,
                order.currency_id,
                order.company_id,
            )
        return float_round(total, precision_rounding=self.currency_id.rounding)

    @api.depends(
        "purchase_budget_percent",
        "purchase_budget_sale_override",
        "analytic_account_id",
        "currency_id",
        "sale_line_id",
        "sale_line_id.price_subtotal",
        "sale_line_id.order_id.amount_untaxed",
        "sale_line_id.order_id.state",
        "allow_billable",
    )
    def _compute_purchase_budget_kpis(self):
        for project in self:
            sale_amount = project._get_purchase_budget_sale_base()
            percent = project.purchase_budget_percent or 0.0
            budget = float_round(
                sale_amount * percent / 100.0,
                precision_rounding=project.currency_id.rounding,
            )
            spent = project._get_confirmed_purchase_spent()
            remaining = float_round(
                budget - spent,
                precision_rounding=project.currency_id.rounding,
            )
            consumed = 0.0
            if not float_is_zero(
                budget, precision_rounding=project.currency_id.rounding
            ):
                consumed = float_round(spent * 100.0 / budget, precision_digits=2)
            project.purchase_budget_sale_amount = sale_amount
            project.purchase_budget_amount = budget
            project.purchase_spent_amount = spent
            project.purchase_remaining_amount = remaining
            project.purchase_consumed_percent = consumed
            project.project_contribution_amount = float_round(
                sale_amount - spent,
                precision_rounding=project.currency_id.rounding,
            )

    def _budget_control_enabled(self):
        """Whether purchase budget control is active for this project."""
        self.ensure_one()
        return bool(self.purchase_budget_percent) and not float_is_zero(
            self.purchase_budget_percent,
            precision_digits=2,
        )
