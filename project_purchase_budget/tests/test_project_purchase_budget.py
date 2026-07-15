# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestProjectPurchaseBudget(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.partner = cls.env["res.partner"].create(
            {
                "name": "REVARE Customer",
                "company_type": "company",
            }
        )
        cls.vendor = cls.env["res.partner"].create(
            {
                "name": "Supplier Materials",
                "company_type": "company",
                "supplier_rank": 1,
            }
        )
        cls.analytic_plan = cls.env["account.analytic.plan"].create(
            {
                "name": "Projects Plan",
            }
        )
        cls.analytic_account = cls.env["account.analytic.account"].create(
            {
                "name": "Store Fit-out AA",
                "plan_id": cls.analytic_plan.id,
            }
        )
        cls.project = cls.env["project.project"].create(
            {
                "name": "Store Fit-out Project",
                "partner_id": cls.partner.id,
                "analytic_account_id": cls.analytic_account.id,
                "allow_billable": True,
            }
        )
        cls.product_sale = cls.env["product.product"].create(
            {
                "name": "Furniture Package",
                "type": "service",
                "list_price": 100000.0,
                "invoice_policy": "order",
                "taxes_id": False,
            }
        )
        cls.product_purchase = cls.env["product.product"].create(
            {
                "name": "Raw Material",
                "type": "consu",
                "standard_price": 1000.0,
                "list_price": 1000.0,
                "purchase_ok": True,
                "taxes_id": False,
                "supplier_taxes_id": False,
            }
        )
        cls.sale_order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_sale.id,
                            "product_uom_qty": 1.0,
                            "price_unit": 100000.0,
                            "tax_id": False,
                        },
                    )
                ],
            }
        )
        cls.sale_order.action_confirm()
        cls.project.write(
            {
                "sale_line_id": cls.sale_order.order_line[:1].id,
                "purchase_budget_percent": 60.0,
            }
        )
        cls.budget_manager_group = cls.env.ref(
            "project_purchase_budget.group_purchase_budget_manager"
        )

    def _create_purchase_order(self, amount, analytic_percent=100.0):
        analytic_id = str(self.analytic_account.id)
        return self.env["purchase.order"].create(
            {
                "partner_id": self.vendor.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_purchase.id,
                            "name": self.product_purchase.name,
                            "product_qty": 1.0,
                            "price_unit": amount,
                            "taxes_id": False,
                            "analytic_distribution": {analytic_id: analytic_percent},
                        },
                    )
                ],
            }
        )

    def test_budget_from_sale_order(self):
        self.assertAlmostEqual(self.project.purchase_budget_sale_amount, 100000.0)
        self.assertAlmostEqual(self.project.purchase_budget_amount, 60000.0)
        self.assertAlmostEqual(self.project.purchase_spent_amount, 0.0)
        self.assertAlmostEqual(self.project.project_contribution_amount, 100000.0)

    def test_sale_override_changes_budget_and_margin(self):
        self.project.purchase_budget_sale_override = 80000.0
        self.assertAlmostEqual(self.project.purchase_budget_sale_amount, 80000.0)
        self.assertAlmostEqual(self.project.purchase_budget_amount, 48000.0)
        self.assertAlmostEqual(self.project.project_contribution_amount, 80000.0)

    def test_po_within_budget_does_not_exceed(self):
        po = self._create_purchase_order(50000.0)
        self.assertFalse(po.exceeds_project_purchase_budget)
        po.button_confirm()
        self.assertEqual(po.state, "purchase")
        self.project.invalidate_recordset()
        self.assertAlmostEqual(self.project.purchase_spent_amount, 50000.0)
        self.assertAlmostEqual(self.project.purchase_remaining_amount, 10000.0)
        self.assertAlmostEqual(self.project.project_contribution_amount, 50000.0)

    def test_po_exceeding_budget_sets_flag(self):
        po = self._create_purchase_order(70000.0)
        self.assertTrue(po.exceeds_project_purchase_budget)

    def test_partial_analytic_distribution(self):
        # Only 50% of a 100000 PO is allocated to the project (= 50000)
        po = self._create_purchase_order(100000.0, analytic_percent=50.0)
        self.assertFalse(po.exceeds_project_purchase_budget)
        po.button_confirm()
        self.project.invalidate_recordset()
        self.assertAlmostEqual(self.project.purchase_spent_amount, 50000.0)

        # Another 50% of 30000 (= 15000) stays within remaining 10000? 50000+15000=65000 > 60000
        po2 = self._create_purchase_order(30000.0, analytic_percent=50.0)
        self.assertTrue(po2.exceeds_project_purchase_budget)

    def test_cumulative_spend_triggers_exceed(self):
        po1 = self._create_purchase_order(40000.0)
        self.assertFalse(po1.exceeds_project_purchase_budget)
        po1.button_confirm()

        po2 = self._create_purchase_order(25000.0)
        # 40000 + 25000 = 65000 > 60000
        self.assertTrue(po2.exceeds_project_purchase_budget)

    def test_no_percent_means_no_control(self):
        self.project.purchase_budget_percent = 0.0
        po = self._create_purchase_order(999999.0)
        self.assertFalse(po.exceeds_project_purchase_budget)

    def test_duplicate_does_not_copy_exceed_flag(self):
        po = self._create_purchase_order(70000.0)
        self.assertTrue(po.exceeds_project_purchase_budget)

        # Flag must not be present in copy_data (never copied as stored value)
        copy_vals = po.copy_data()[0]
        self.assertNotIn("exceeds_project_purchase_budget", copy_vals)

        # Duplicate recalculates from current budget/lines (same lines → still True)
        duplicate = po.copy()
        self.assertTrue(duplicate.exceeds_project_purchase_budget)

        # After lowering the amount on the duplicate, flag must reflect new data
        duplicate.order_line[0].price_unit = 10000.0
        duplicate.invalidate_recordset(["exceeds_project_purchase_budget"])
        self.assertFalse(duplicate.exceeds_project_purchase_budget)
        # Source order must keep its own recomputed value
        po.invalidate_recordset(["exceeds_project_purchase_budget"])
        self.assertTrue(po.exceeds_project_purchase_budget)

    def test_is_purchase_budget_manager_compute(self):
        manager_user = self.env["res.users"].create(
            {
                "name": "Budget Manager",
                "login": "budget_manager_test",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_user").id,
                            self.budget_manager_group.id,
                        ],
                    )
                ],
            }
        )
        plain_user = self.env["res.users"].create(
            {
                "name": "Plain User",
                "login": "plain_budget_test",
                "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
            }
        )
        self.assertTrue(self.project.with_user(manager_user).is_purchase_budget_manager)
        self.assertFalse(self.project.with_user(plain_user).is_purchase_budget_manager)

    def test_sale_orders_without_sale_order_id(self):
        project = self.env["project.project"].create(
            {
                "name": "No SO Link",
                "partner_id": self.partner.id,
                "analytic_account_id": self.analytic_account.id,
                "allow_billable": True,
                "purchase_budget_percent": 50.0,
                "purchase_budget_sale_override": 20000.0,
            }
        )
        self.assertFalse(project.sale_order_id)
        self.assertFalse(project._get_purchase_budget_sale_orders())
        self.assertAlmostEqual(project.purchase_budget_sale_amount, 20000.0)

    def test_sale_orders_includes_sale_order_id(self):
        orders = self.project._get_purchase_budget_sale_orders()
        self.assertIn(self.sale_order, orders)
        self.assertTrue(self.project.sale_order_id)

    def test_spent_without_analytic_account_is_zero(self):
        project = self.env["project.project"].create(
            {
                "name": "No Analytic",
                "partner_id": self.partner.id,
                "purchase_budget_percent": 50.0,
                "purchase_budget_sale_override": 10000.0,
            }
        )
        project.analytic_account_id = False
        self.assertEqual(project._get_confirmed_purchase_spent(), 0.0)
        self.assertAlmostEqual(project.purchase_spent_amount, 0.0)

    def test_convert_to_project_currency_same_or_empty(self):
        amount = 1234.56
        self.assertAlmostEqual(
            self.project._convert_to_project_currency(amount, False),
            amount,
        )
        self.assertAlmostEqual(
            self.project._convert_to_project_currency(amount, self.project.currency_id),
            amount,
        )

    def test_convert_to_project_currency_different_currency(self):
        company_currency = self.project.currency_id
        other_currency = self.env.ref("base.USD")
        if other_currency == company_currency:
            other_currency = self.env.ref("base.EUR")
        other_currency.active = True
        self.env["res.currency.rate"].create(
            {
                "name": fields.Date.today(),
                "currency_id": other_currency.id,
                "rate": 2.0,
                "company_id": self.env.company.id,
            }
        )
        converted = self.project._convert_to_project_currency(100.0, other_currency)
        expected = other_currency._convert(
            100.0,
            company_currency,
            self.env.company,
            fields.Date.today(),
        )
        self.assertAlmostEqual(converted, expected)

    def test_spent_skips_rows_without_project_analytic_key(self):
        """Cover defensive continue when distribution lacks the project analytic."""
        company = self.project.company_id or self.env.company
        currency = self.project.currency_id
        # Warm currency/company cache (do not mock cr.execute — it breaks ORM reads)
        _ = currency.rounding
        rows = [
            {
                "id": 1,
                "price_subtotal": 5000.0,
                "currency_id": currency.id,
                "company_id": company.id,
                "analytic_distribution": {},
            },
            {
                "id": 2,
                "price_subtotal": 1000.0,
                "currency_id": currency.id,
                "company_id": company.id,
                "analytic_distribution": {str(self.analytic_account.id): 100.0},
            },
        ]
        with patch.object(self.env.cr, "dictfetchall", return_value=rows):
            spent = self.project._get_confirmed_purchase_spent()
        self.assertAlmostEqual(spent, 1000.0)

    def test_spent_with_exclude_order_ids(self):
        po1 = self._create_purchase_order(10000.0)
        po1.button_confirm()
        po2 = self._create_purchase_order(5000.0)
        po2.button_confirm()
        self.project.invalidate_recordset()
        spent_all = self.project._get_confirmed_purchase_spent()
        spent_excl = self.project._get_confirmed_purchase_spent(
            exclude_order_ids=po1.ids,
        )
        self.assertAlmostEqual(spent_all, 15000.0)
        self.assertAlmostEqual(spent_excl, 5000.0)

    def test_budget_control_enabled(self):
        self.assertTrue(self.project._budget_control_enabled())
        self.project.purchase_budget_percent = 0.0
        self.assertFalse(self.project._budget_control_enabled())

    def test_po_without_analytic_has_no_project_amounts(self):
        po = self.env["purchase.order"].create(
            {
                "partner_id": self.vendor.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_purchase.id,
                            "name": self.product_purchase.name,
                            "product_qty": 1.0,
                            "price_unit": 99999.0,
                            "taxes_id": False,
                        },
                    )
                ],
            }
        )
        self.assertEqual(po._get_project_amounts_from_order(), {})
        self.assertFalse(po._order_exceeds_any_project_budget())
        self.assertFalse(po.exceeds_project_purchase_budget)
        self.assertFalse(po._get_affected_budget_projects())

    def test_po_analytic_without_project_is_ignored(self):
        orphan_aa = self.env["account.analytic.account"].create(
            {
                "name": "Orphan Analytic",
                "plan_id": self.analytic_plan.id,
            }
        )
        po = self.env["purchase.order"].create(
            {
                "partner_id": self.vendor.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_purchase.id,
                            "name": self.product_purchase.name,
                            "product_qty": 1.0,
                            "price_unit": 99999.0,
                            "taxes_id": False,
                            "analytic_distribution": {str(orphan_aa.id): 100.0},
                        },
                    )
                ],
            }
        )
        self.assertEqual(po._get_project_amounts_from_order(), {})
        self.assertFalse(po._order_exceeds_any_project_budget())
        self.assertFalse(po.exceeds_project_purchase_budget)
        self.assertFalse(po._get_affected_budget_projects())

    def test_po_with_project_and_orphan_analytic_only_counts_project(self):
        orphan_aa = self.env["account.analytic.account"].create(
            {
                "name": "Orphan Analytic Mix",
                "plan_id": self.analytic_plan.id,
            }
        )
        po = self.env["purchase.order"].create(
            {
                "partner_id": self.vendor.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_purchase.id,
                            "name": "Project share",
                            "product_qty": 1.0,
                            "price_unit": 10000.0,
                            "taxes_id": False,
                            "analytic_distribution": {
                                str(self.analytic_account.id): 50.0,
                                str(orphan_aa.id): 50.0,
                            },
                        },
                    )
                ],
            }
        )
        amounts = po._get_project_amounts_from_order()
        self.assertEqual(list(amounts.keys()), [self.project.id])
        self.assertAlmostEqual(amounts[self.project.id], 5000.0)
        self.assertFalse(po.exceeds_project_purchase_budget)
