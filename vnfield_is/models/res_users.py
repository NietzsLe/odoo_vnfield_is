from odoo import models, fields


class ResUsers(models.Model):
    _inherit = "res.users"

    organization_name = fields.Char(string="Organization")
