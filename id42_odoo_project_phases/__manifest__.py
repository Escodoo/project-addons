# -*- coding: utf-8 -*-
# Part of ID42 Sistemas. See LICENSE file for full copyright and licensing details.

{
    'name': 'Project by Phases',
    'version': '12.0.0.1',
    'category': 'Projects',
    'author': 'ID42 Sistemas',
    'website': 'http://www.id42.com.br',
    'summary': 'This apps helps to manage Project and Task Phases',
    'description': """
        Project Phases.
        Task phases.
        Project by Phases
        Task by Project phases
        Task by Phases
        Project with phases
        Task with phases

""",
    'depends': ['project'],
    'data': [
        'security/ir.model.access.csv',
        'views/project_view.xml',
        'views/project_portal_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
    "images":['static/description/Banner.png'],
}
