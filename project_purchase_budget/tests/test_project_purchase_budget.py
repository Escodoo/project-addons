# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

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
