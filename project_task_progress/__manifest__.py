# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{

    'name': 'project advancement',
    'category': 'Project',
    'summary': 'managing actual project progress',
    'description': "",
    "author": "Escodoo, Matheus Marques",
    'version': '1.0',
    'depends': ['base','project'],
    'data': [
        'views/project_advancement_field.xml',

    ],
    'installable': True,
    'auto_install': True,
    'application': False,
    'license': 'LGPL-3',
}
