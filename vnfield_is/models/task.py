from odoo import api, fields, models, _, exceptions
from odoo.tools.float_utils import float_compare


class Task(models.Model):
    _name = "vnfield.task"
    _description = "VN Field Task"
    _inherit = ["mail.thread"]

    name = fields.Char()
    description = fields.Text()
    priority = fields.Selection(
        selection=[("high", "High"), ("medium", "Medium"), ("low", "Low")],
        default="low",
    )
    status = fields.Selection(
        selection=[
            ("not-started", "Not started"),
            ("waiting", "Waiting"),
            ("in-progress", "In progress"),
            ("cancelled", "Cancelled"),
            ("expired", "Expired"),
            ("stopped", "Stopped"),
            ("resolved", "Resolved"),
            ("done", "Done"),
        ],
        default="not-started",
    )
    is_issue_task = fields.Boolean(
        compute="_compute_is_issue_task"
    )  # Xem task này có phải là một task của issue hay không
    resolve_for_issue_id = fields.Many2one(comodel_name="vnfield.issue")
    assign_at = fields.Datetime()
    deadline = fields.Datetime()
    start_at = fields.Datetime()
    end_at = fields.Datetime()
    related_issue_id = fields.Many2one(comodel_name="vnfield.issue")
    assigner_id = fields.Many2one(comodel_name="res.users")
    assignee_id = fields.Many2one(comodel_name="res.users")
    verifier_id = fields.Many2one(comodel_name="res.users")
    approval_to_verify_id = fields.Many2one(comodel_name="vnfield.approval")
    child_task_ids = fields.One2many(
        comodel_name="vnfield.task", inverse_name="parent_task_id"
    )
    task_tree_id = fields.Many2one(comodel_name="vnfield.task.tree")
    parent_task_id = fields.Many2one(comodel_name="vnfield.task")
    dependent_task_ids = fields.Many2many(
        comodel_name="vnfield.task",
        relation="dependency_task_rel",
        column1="task_id",
        column2="dependent_task_id",
    )
    predecessor_task_ids = fields.Many2many(
        comodel_name="vnfield.task",
        relation="dependency_task_rel",
        column1="task_id",
        column2="dependent_task_id",
    )
    project_id = fields.Many2one(comodel_name="vnfield.project")
    task_type_id = fields.Many2one(comodel_name="vnfield.task.type")
    attachment_ids = fields.Many2many(
        comodel_name="ir.attachment",
        relation="task_attachment_rel",
        column1="task_id",
        column2="attachment_id",
    )

    def condition_for_done(self):
        if self.status != "resolved":
            return False

        for child in self.child_task_ids:
            if not (child.status == "cancelled" or child.status == "done"):
                return False
        return True

    def condition_for_cancelled(self):
        if (
            self.status != "done"
            and self.status != "not-started"
            and self.status != "cancelled"
        ):
            return True
        return False

    def condition_for_in_progress(self):
        if self.status == "resolved":
            return True

        if self.status == "waiting":
            for predecessor in self.predecessor_task_ids:
                if not (
                    predecessor.status == "cancelled" or predecessor.status == "done"
                ):
                    return False
            return True

        return False

    def condition_for_resolved(self):
        if self.status == "in-progress":
            for child in self.child_task_ids:
                if not (child.status == "done" or child.status == "cancelled"):
                    return False
            return True
        return False

    def condition_for_expired(self):
        now = fields.Datetime.now()
        if not self.deadline or (self.deadline and self.deadline > now):
            return False
        if self.status == "waiting" or self.status == "in-progress":
            return True
        return False

    def condition_for_stopped(self):
        if self.status == "waiting" or self.status == "in-progress":
            return True
        return False

    def condition_for_waiting(self):
        if (
            (not self.parent_task_id.id) or self.parent_task_id.status == "waiting"
        ) and self.status == "not-started":
            return True
        return False

    @api.model
    def search(self, args, offset=0, limit=None, order=None):
        # Cập nhật trước khi thực hiện tìm kiếm
        result = super().search(args, offset=offset, limit=limit, order=order)
        return result

    @api.model
    def create(self, vals):
        vals["assigner_id"] = self.env.uid
        return super(Task, self).create(vals)

    @api.model
    def write(self, vals):
        if not (self.access_control_is_related_user() or self.access_control_is_root()):
            raise exceptions.AccessError(
                "You do not have permission to modify the record!"
            )
        return super(Task, self).write(vals)

    # @api.constrains("deadline")
    # def trigger_when_change_deadline(self):
    #     print("\n@Trigger deadline: ", self.status)
    #     expired = self.condition_for_expired()
    #     if expired:
    #         self.write({"status": "expired"})

    @api.depends("resolve_for_issue_id")
    def _compute_is_issue_task(self):
        for rec in self:
            if rec.resolve_for_issue_id.id:
                rec.is_issue_task = True
            else:
                rec.is_issue_task = False

    @api.constrains("assignee_id")
    def trigger_when_change_assignee(self):
        self.write({"assign_at": fields.Datetime.now()})

    @api.constrains("status")
    def trigger_when_change_status(self):
        print("\n@Trigger Status: ", self.status)
        if self.status == "cancelled":
            self.write({"end_at": fields.Datetime.now()})
            for dependency in self.dependent_task_ids:
                canChange = dependency.condition_for_in_progress()
                if canChange:
                    dependency.write({"status": "in-progress"})
            for child in self.child_task_ids:
                canChange = child.condition_for_cancelled()
                if canChange:
                    child.write({"status": "cancelled"})
        elif self.status == "done":
            message = _(
                "Task %s has done!",
                self._get_html_link(title=self.name),
            )
            user1 = self.assigner_id
            user2 = self.assignee_id
            if user1.id:
                self.send_message(message, user1)
            if user2.id:
                self.send_message(message, user2)
            self.write({"end_at": fields.Datetime.now()})
            for dependency in self.dependent_task_ids:
                canChange = dependency.condition_for_in_progress()
                if canChange:
                    dependency.write({"status": "in-progress"})
        elif self.status == "expired":
            message = _(
                "Task %s has expired!",
                self._get_html_link(title=self.name),
            )
            user = self.assigner_id
            self.send_message(message, user)
            for child in self.child_task_ids:
                canChange = child.condition_for_stopped()
                if canChange:
                    child.write({"status": "stopped"})
        elif self.status == "resolved":
            message = _(
                "Task %s has been resolved!",
                self._get_html_link(title=self.name),
            )
            if self.verifier_id.id:
                user = self.verifier_id
            else:
                user = self.assigner_id
            self.send_message(message, user)
        elif self.status == "in-progress":
            if not bool(self.start_at):
                self.write({"start_at": fields.Datetime.now()})
            message = _(
                "Task %s has started!",
                self._get_html_link(title=self.name),
            )
            user = self.assignee_id
            if user:
                self.send_message(message, user)
            for child in self.child_task_ids:
                canChange = child.condition_for_in_progress()
                if canChange:
                    child.write({"status": "in-progress"})
        elif self.status == "waiting":
            flag = self.condition_for_in_progress()
            if flag:
                self.write({"status": "in-progress"})
        elif self.status == "stopped":
            for child in self.child_task_ids:
                canChange = child.condition_for_stopped()
                if canChange:
                    child.write({"status": "stopped"})

    def send_message(self, message, user):
        # odoo runbot
        odoobot = self.env.ref("base.partner_root").with_user(
            self.env.ref("base.user_root")
        )

        # find if a channel was opened for this user before
        channel = odoobot.env["discuss.channel"].channel_get([user.partner_id.id])
        print(
            "\n@Send message: ",
            odoobot.env.uid,
            odoobot.id,
            self.env.uid,
            user.partner_id.id,
        )
        channel_id = odoobot.env["discuss.channel"].browse(channel["id"])
        # send a message to the related user
        channel_id.message_post(
            body=message,
            subject="Task is resolved",
            author_id=odoobot.id,
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
        )

    def _cron_check_expired(self):
        now = fields.Datetime.now()
        records = self.search([("deadline", "<", now), ("status", "!=", "expired")])
        print("\n@Cron: ", now)
        for record in records:
            print(record)
            expired = record.condition_for_expired()
            if expired:
                record.write({"status": "expired"})

    def action_handle_click_for_start(self):
        if self.condition_for_waiting():
            self.write({"status": "waiting"})
        else:
            raise exceptions.ValidationError("Cannot change status to waiting!")

    def action_handle_click_for_resolve(self):
        if self.condition_for_resolved():
            self.write({"status": "resolved"})
        else:
            raise exceptions.ValidationError("Cannot change status to resolved!")

    def action_handle_click_for_done(self):
        if self.condition_for_done():
            self.write({"status": "done"})
        else:
            raise exceptions.ValidationError("Cannot change status to done!")

    def action_handle_click_for_cancelled(self):
        if self.condition_for_cancelled():
            self.write({"status": "cancelled"})
        else:
            raise exceptions.ValidationError("Cannot change status to cancelled!")

    def access_control_to_done_and_in_progress(self):
        if self.env.uid == self.assigner_id:
            raise exceptions.AccessError(
                "Only verifier and assigner have the right to change status to done!"
            )

    def access_control_to_cancelled(self):
        if self.env.uid == self.assigner_id:
            raise exceptions.AccessError(
                "Only assigner have the right to change status to cancelled!"
            )

    def access_control_is_related_user(self):
        if (
            (self.assignee_id.id and self.env.uid == self.assignee_id.id)
            or (self.assigner_id.id and self.env.uid == self.assigner_id.id)
            or (self.verifier_id.id and self.env.uid == self.verifier_id.id)
        ):
            return True
        return False

    def access_control_is_root(self):
        odoobot = self.env.ref("base.partner_root")
        if self.env.uid == odoobot.id:
            return True
        return False
