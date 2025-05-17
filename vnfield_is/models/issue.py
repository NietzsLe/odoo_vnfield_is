from odoo import api, fields, models, exceptions
from odoo.tools.float_utils import float_compare


class Issue(models.Model):
    _name = "vnfield.issue"
    _description = "VN Field Issue"
    _inherit = ["mail.thread"]

    name = fields.Char()
    description = fields.Text()
    comment = fields.Text()
    priority = fields.Selection(
        selection=[("high", "High"), ("medium", "Medium"), ("low", "Low")]
    )
    status = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("open", "Open"),
            ("in-progress", "In Progress"),
            ("resolved", "Resolved"),
            ("closed", "Closed"),
            ("reopen", "Reopen"),
        ]
    )
    result_type = fields.Selection(
        selection=[
            ("fixed", "Fixed"),
            ("wont-fix", "Won't Fix"),
            ("invalid", "Invalid"),
            ("duplicate", "Duplicate"),
        ]
    )
    resolve_task_ids = fields.One2many(
        comodel_name="vnfield.task", inverse_name="resolve_for_issue_id"
    )
    resolve_period = fields.Float()
    report_at = fields.Datetime()
    resolve_at = fields.Datetime()
    assign_at = fields.Datetime()
    reporter_id = fields.Many2one(comodel_name="res.users")
    resolver_id = fields.Many2one(comodel_name="res.users")
    related_task_ids = fields.One2many(
        comodel_name="vnfield.task", inverse_name="related_issue_id"
    )
    project_id = fields.Many2one(comodel_name="vnfield.project")
    issue_type_id = fields.Many2one(comodel_name="vnfield.issue.type")
    attachment_ids = fields.Many2many(
        comodel_name="ir.attachment",
        relation="issue_attachment_rel",
        column1="issue_id",
        column2="attachment_id",
    )
