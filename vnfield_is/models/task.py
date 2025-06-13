from odoo import api, fields, models, _, exceptions
from odoo.tools.float_utils import float_compare


class Task(models.Model):
    _inherit = "vnfield.task"

    @api.model
    def write(self, vals):
        # Gán giá trị mặc định hoặc xử lý logic

        record = super(Task, self).write(vals)
        if record:
            record = self.env["vnfield.approval"].browse(self.id)
            # Hành động sau khi tạo
            integration_service = TaskIntegrationService(self.env)
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
                "external_id",
                "id",
            ]:
                continue
            f = self._fields[field]
            if (
                not isinstance(f, fields.Many2one)
                and not isinstance(f, fields.Many2many)
                and not isinstance(f, fields.One2many)
                and self[field]
            ):
                result[field] = self[field]
                if isinstance(self[field], datetime):
                    result[field] = self[field].isoformat()
        print(result)
        return result
