# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Shared Custom Stages Unified",
    "summary": "Shared Custom Stages Unified",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo",
    "website": "https://github.com/Escodoo/project-addons",
    "depends": ["project", "helpdesk_mgmt"],
    "data": [
        "security/ir.model.access.csv",
        "security/shared_custom_stage_security.xml",
        "views/shared_custom_stage_views.xml",
        "views/unified_task_ticket_views.xml",
    ],
    "installable": True,
}
