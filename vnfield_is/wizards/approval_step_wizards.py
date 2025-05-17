# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError


class ApprovalReview(models.TransientModel):
    _name = "vnfield.approval.review"
    _description = "VN Field Approval Review"

    approval_step_id = fields.Many2one(comodel_name="vnfield.approval.step")
    result = fields.Selection(
        selection=[("approve", "Approve"), ("reject", "Reject")], required=True
    )
    comment = fields.Text()
    attachment_ids = fields.Many2many(
        comodel_name="ir.attachment",
        relation="approval_review_attachment_rel",
        column1="approval_review_id",
        column2="attachment_id",
    )

    def handle_confirm(self):
        print(self.approval_step_id.id)
        self.approval_step_id.write(
            {
                "approval_at": fields.Datetime.now(),
                "status": "approved" if self.result == "approve" else "rejected",
                "comment": self.comment,
                "attachment_ids": [(4, item.id) for item in self.attachment_ids],
            }
        )
        approval_step = self.env["vnfield.approval.step"].browse(
            self.approval_step_id.id
        )
        if self.result == "approve":
            approval_step.approval_id.write(
                {"processing_step_ids": [(3, approval_step.id)]}
            )
            for next in approval_step.next_step_ids:
                prevsOfNext = (
                    self.env["vnfield.approval.step"].browse(next.id).prev_step_ids
                )
                flag = True
                for prev in prevsOfNext:
                    if prev.status != "approved":
                        flag = False
                        break
                if flag:
                    next.write({"status": "in-progress"})
                    approval_step.approval_id.write(
                        {"processing_step_ids": [(4, approval_step.id)]}
                    )
            approval = self.env["vnfield.approval"].browse(approval_step.approval_id.id)
            if (
                approval.status == "in-progress"
                and len(approval.processing_step_ids) == 0
            ):
                approval.write({"status": "approved"})
        elif self.result == "reject":
            approval_step.approval_id.write(
                {"processing_step_ids": [(3, approval_step.id)]}
            )
            processing_steps = (
                self.approval_step_id.env["vnfield.approval"]
                .browse(approval_step.approval_id)
                .processing_step_ids
            )
            for step in processing_steps:
                step.write({"status": "canceled"})
            approval_step.approval_id.write(
                {"processing_step_ids": [5], "status": "rejected"}
            )
