# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    "name": "VN Field For Integration System",
    "version": "17.0.1.0.1",
    "author": "Nhan Le",
    "category": "Approval",
    "depends": ["base", "mail", "web_m2x_options", "rest_api_odoo", "vnfield"],
    "data": [
        # "views/actions.xml",
        # "views/project_views.xml",
        # "views/task_type_views.xml",
        # "views/issue_type_views.xml",
        # "views/approval_step_type_views.xml",
        # "views/approval_views.xml",
        # "views/issue_views.xml",
        # "views/task_views.xml",
        # "views/approval_step_views.xml",
        # "wizards/approval_step_wizards.xml",
        # "views/menu.xml",
        # "data/rest_api_odoo.xml",
        # "data/task_type.xml",
        # "security/security.xml",
        # "data/ir_cron.xml",
        "data/default_res_users.xml"
    ],
    # "post_init_hook": "start_kafka_consumers",
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "application": True,
}
