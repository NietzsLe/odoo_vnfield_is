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
from ..services.integrations.approval import ApprovalIntegrationService


class Approval(models.Model):
    _inherit = "vnfield.approval"

    @api.model
    def write(self, vals):
        # Gán giá trị mặc định hoặc xử lý logic

        record = super(Approval, self).write(vals)
        if record:
            record = self.env["vnfield.approval"].browse(self.id)
            # Hành động sau khi tạo
            integration_service = ApprovalIntegrationService(self.env)
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
