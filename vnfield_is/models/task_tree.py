from odoo import api, fields, models, exceptions
from odoo.tools.float_utils import float_compare


class TaskTree(models.Model):
    _name = "vnfield.task.tree"
    _description = "VN Field Task Tree"

    root_task_id = fields.One2many(
        comodel_name="vnfield.task", inverse_name="task_tree_id"
    )
    dependent_tree_ids = fields.Many2many(
        comodel_name="vnfield.task.tree",
        relation="dependency_task_tree_rel",
        column1="tree_id",
        column2="dependent_tree_id",
    )
    dependent_on_tree_ids = fields.Many2many(
        comodel_name="vnfield.task.tree",
        relation="dependency_task_tree_rel",
        column1="dependent_tree_id",
        column2="tree_id",
    )
