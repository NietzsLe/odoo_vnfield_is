from odoo import api, fields, models
from odoo.tools.float_utils import float_compare
from odoo.exceptions import ValidationError, UserError


class ApprovalStep(models.Model):
    _inherit = "vnfield.approval.step"
