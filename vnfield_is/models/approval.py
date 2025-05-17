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
from odoo import api, fields, models, http
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError

from ..integration.approval_client import ApprovalClient


class Approval(models.Model):
    _name = "vnfield.approval"
    _inherit = ["mail.thread"]
    _description = "VN Field Approval"

    name = fields.Char(required=True)
    description = fields.Text()
    approval_period = fields.Float(required=True)
    status = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("in-progress", "In progress"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        readonly=True,
    )
    request_at = fields.Datetime(readonly=True)
    # approvalAt = fields.Datetime(compute="_compute_approvalAt")
    # workflowStage = fields.Char(compute="_compute_workflowStage")
    priority = fields.Selection(
        selection=[("high", "High"), ("medium", "Medium"), ("low", "Low")]
    )
    approval_step_ids = fields.One2many(
        comodel_name="vnfield.approval.step", inverse_name="approval_id"
    )
    root_step_ids = fields.One2many(
        comodel_name="vnfield.approval.step", inverse_name="root_of_approval_id"
    )
    project_id = fields.Many2one(comodel_name="vnfield.project")
    requester_id = fields.Many2one(comodel_name="res.users", readonly=True)
    processing_step_ids = fields.Many2many(
        comodel_name="vnfield.approval.step",
        relation="approval_processing_step_rel",
        column1="approval_id",
        column2="step_id",
        readonly=True,
        store=True,
    )

    @api.model
    def create(self, vals):
        # Thực hiện các xử lý trước khi tạo record
        vals["status"] = "draft"
        if not vals["priority"]:
            vals["priority"] = "low"
        approval = super(Approval, self).create(vals)
        config = self.env["ir.config_parameter"].sudo()
        ApprovalClient.post(approval, approval.id, config.get_param("connector_host"))
        return approval

    @api.model
    def unlink(self, vals):
        print(vals)
        removeItems = self.env["vnfield.approval"].browse(vals)
        for record in removeItems:
            if record.status != "draft":
                raise UserError('Cannot delete record because it is in "draft" status.')
        approval = super(Approval, removeItems).unlink()
        config = self.env["ir.config_parameter"].sudo()
        print(vals)
        if approval:
            for item in removeItems:
                ApprovalClient.delete(item.id, config.get_param("connector_host"))
        return approval

    @api.model
    def write(self, vals):
        approval = super(Approval, self).write(vals)
        config = self.env["ir.config_parameter"].sudo()
        print(self)
        if approval:
            ApprovalClient.put(self, self.id, config.get_param("connector_host"))
        return approval

    def handle_send(self):
        self.request_at = fields.Datetime.now()
        self.status = "in-progress"
        self.requester_id = self.env.user.id
        self.write(
            {"processing_step_ids": [(4, item.id) for item in self.root_step_ids]}
        )
        for root_step in self.root_step_ids:
            root_step.status = "in-progress"
            root_step.come_at = fields.Datetime.now()
        return True

    @api.model
    def read(self, fields=None, load="_classic_read"):
        # Gọi super để lấy dữ liệu gốc
        # print(http.request.env["ir.attachment"].search_read(fields=["datas"]))
        return super(Approval, self).read(fields=fields, load=load)
