# Copyright 2023 - TODAY Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Project Team",
    "summary": """Creates teams of users for project and task assignments in Odoo""",
    "author": "Escodoo",
    "website": "https://github.com/Escodoo/project-addons",
    "category": "Project Management",
    "version": "12.0.1.0.1",
    "license": "AGPL-3",
    "depends": ["project_status"],
    "data": [
        "views/project_project.xml",
        "views/project_task.xml",
        "views/project_team.xml",
        "views/project_status.xml",
        "security/project_team.xml",
    ],
}
