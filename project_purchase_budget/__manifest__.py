# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Project Purchase Budget",
    "summary": "Limit project purchases to a percentage of the sale value "
    "with tier validation when the budget is exceeded",
    "version": "16.0.1.0.0",
    "category": "Purchases",
    "author": "Escodoo",
    "website": "https://github.com/Escodoo/project-addons",
    "license": "AGPL-3",
    "depends": [
        "project_purchase",
        "sale_project",
        "purchase_tier_validation",
        "base_tier_validation_formula",
    ],
    "data": [
        "security/project_purchase_budget_security.xml",
        "data/tier_definition_data.xml",
        "views/project_project_views.xml",
        "views/purchase_order_views.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "development_status": "Beta",
    "maintainers": ["marcelsavegnago"],
}
