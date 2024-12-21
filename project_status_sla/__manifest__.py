# Copyright 2024 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Project Status SLA",
    "summary": """
        Add SLA for Project Status""",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo",
    "website": "https://github.com/Escodoo/project-addons",
    "depends": [
        "project_status",
    ],
    "data": [
        "data/project_status_sla_cron.xml",
        "security/ir.model.access.csv",
        "views/project_project.xml",
        "views/project_status_sla.xml",
        "views/project_status_sla_line.xml",
    ],
}
