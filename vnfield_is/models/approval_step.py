from odoo import api, fields, models
from odoo.tools.float_utils import float_compare
from odoo.exceptions import ValidationError, UserError
from ..services.integrations.approval_step import ApprovalStepIntegrationService


class ApprovalStep(models.Model):
    _inherit = "vnfield.approval.step"

    @api.model
    def create(self, vals):
        # Gán giá trị mặc định hoặc xử lý logic

        record = super(ApprovalStep, self).create(vals)

        # Hành động sau khi tạo
        print("@Approval step self: ", self.env.user.login)
        integration_service = ApprovalStepIntegrationService(self.env)
        integration_service.update(vals, record, self.env.user)

        return record

    @api.model
    def write(self, vals):
        # Gán giá trị mặc định hoặc xử lý logic

        record = super(ApprovalStep, self).write(vals)

        if record:
            record = self.env["vnfield.approval.step"].browse(self.id)
            # Hành động sau khi tạo
            print("@Approval step self: ", self.env.user.login)
            integration_service = ApprovalStepIntegrationService(self.env)
            integration_service.update(vals, record, self.env.user)

        return record

    def to_dict(self):
        self.ensure_one()
        result = {}
        for field in self._fields:
            if field in [
                "__last_update",
                "create_date",
                "write_date",
            ]:
                continue
            f = self._fields[field]
            if (
                not isinstance(f, fields.Many2one)
                and not isinstance(f, fields.Many2many)
                and not isinstance(f, fields.One2many)
                and self[field]
            ):
                if field == "id":
                    result["external_id"] = self[field]
                else:
                    result[field] = self[field]
        return result
