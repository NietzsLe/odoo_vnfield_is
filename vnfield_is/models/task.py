from odoo import api, fields, models, _, exceptions
from odoo.tools.float_utils import float_compare


class Task(models.Model):
    _inherit = "vnfield.task"
