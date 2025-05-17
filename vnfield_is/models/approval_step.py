from odoo import api, fields, models
from odoo.tools.float_utils import float_compare
from odoo.exceptions import ValidationError, UserError


class ApprovalStep(models.Model):
    _name = "vnfield.approval.step"
    _inherit = ["mail.thread"]
    _description = "VN Field Approval Step"

    name = fields.Char(required=True)
    description = fields.Text()
    come_at = fields.Datetime(readonly=True)
    approval_at = fields.Datetime(readonly=True)
    approval_step_period = fields.Float(required=True)
    status = fields.Selection(
        selection=[
            ("waiting", "Waiting"),
            ("in-progress", "In Progress"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        readonly=True,
    )
    comment = fields.Text()
    approval_id = fields.Many2one(comodel_name="vnfield.approval", readonly=True)
    root_of_approval_id = fields.Many2one(
        comodel_name="vnfield.approval", readonly=True
    )
    next_step_ids = fields.Many2many(
        comodel_name="vnfield.approval.step",
        relation="step_nextstep_rel",
        column1="step_id",
        column2="next_step_id",
    )
    prev_step_ids = fields.Many2many(
        comodel_name="vnfield.approval.step",
        relation="step_nextstep_rel",
        column1="next_step_id",
        column2="step_id",
        readonly=True,
    )
    approver_id = fields.Many2one(comodel_name="res.users", required=True)
    step_type_id = fields.Many2one(
        comodel_name="vnfield.approval.step.type", required=True
    )
    attachment_ids = fields.Many2many(
        comodel_name="ir.attachment",
        relation="step_attachment_rel",
        column1="approval_step_id",
        column2="attachment_id",
    )

    @api.model
    def create(self, vals):
        # Thực hiện các xử lý trước khi tạo record
        vals["status"] = "waiting"
        step = super(ApprovalStep, self).create(vals)
        if "root_of_approval_id" in vals:
            step.approval_id = vals["root_of_approval_id"]

        return step

    @api.model
    def unlink(self, vals):
        removeItems = self.env["vnfield.approval.step"].browse(vals)
        for record in removeItems:
            if record.status != "waiting":
                raise UserError(
                    'Cannot delete record because it is in "waiting" status.'
                )
        return super(ApprovalStep, removeItems).unlink()

    @api.constrains("next_step_ids")
    def _check_next_step(self):
        for next_step in self.next_step_ids:
            if next_step.approval_id != self.approval_id:
                raise ValidationError("Next step's approval must be same this step!")
            prevList = set(map(lambda x: x.id, self.prev_step_ids))
            prevList.add(self.id)
            qu = []
            qu = list(map(lambda x: x.id, self.prev_step_ids)) + qu
            while len(qu) != 0:
                removeItem = qu.pop()
                prevs = list(
                    map(
                        lambda x: x.id,
                        self.env["vnfield.approval.step"]
                        .browse(removeItem)
                        .prev_step_ids,
                    )
                )
                print(prevs)
                if next_step.id in prevList:
                    raise ValidationError(
                        "The next task should not be assigned in a circular loop!"
                    )
                prevList.update(prevs)
                qu = prevs + qu

    @api.constrains("approval_id")
    def _check_approval_id(self):
        if self.root_of_approval_id and self.root_of_approval_id != self.approval_id:
            raise ValidationError("'Approval' must be the same as 'Root of approval'!")

    def open_form_view(self):
        form_view_id = self.env.ref("vnfield.approval_step_form_view").id
        result = {
            "type": "ir.actions.act_window",
            "res_model": "vnfield.approval.step",
            "views": [[form_view_id, "form"]],
            "name": "Approval Step",
            "res_id": self.id,
        }
        return result

    def handle_click_review(self):
        print(self.approver_id.id, self.env.user.id)
        if self.approver_id.id != self.env.user.id:
            raise UserError("You are not the approver of this step!")
        result = {
            "type": "ir.actions.act_window",
            "name": "Review",
            "res_model": "vnfield.approval.review",
            "target": "new",
            "view_mode": "form",
            "view_type": "form",
            "context": {"default_approval_step_id": self.id},
        }
        return result
