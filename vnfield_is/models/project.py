from odoo import api, fields, models, exceptions
from odoo.tools.float_utils import float_compare


class Project(models.Model):
    _name = "vnfield.project"
    _description = "VN Field Team"

    name = fields.Char()
    description = fields.Text()
    status = fields.Selection(
        selection=[
            ("not-started", "Not started"),
            ("in-progress", "In progress"),
            ("canceled", "Canceled"),
            ("done", "Done"),
        ]
    )
    start_at = fields.Datetime()
    end_at = fields.Datetime()
    # team_ids = fields.One2many(
    #     comodel_name="vnfield.team", inverse_name="belong_to_project_id"
    # )
    # subcontractor_ids = fields.One2many(
    #     comodel_name="vnfield.subcontractor", inverse_name="hired_for_project_id"
    # )
    member_ids = fields.Many2many(
        comodel_name="res.users",
        relation="project_member_rel",
        column1="project_id",
        column2="member_id",
    )
    manager_id = fields.Many2one(comodel_name="res.users")
    task_ids = fields.One2many(comodel_name="vnfield.task", inverse_name="project_id")
