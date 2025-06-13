from typing import TYPE_CHECKING
import traceback
from ...kafka_producer import produce

if TYPE_CHECKING:
    from ...models.approval import Approval

from ...models.res_users import ResUsers


class ApprovalKafkaClient:
    def __init__(self, env):
        self.env = env

    def update(self, vals: dict, approval_step: "Approval", user: "ResUsers"):
        try:
            org_names = [approval_step.requester_id.organization_name]
            org_names = list(filter(lambda x: x != user.organization_name, org_names))
            header = {
                "method": "update",
                "org_names": org_names,
                "entity": "approval",
            }
            produce(self.env, vals, header)
        except Exception as e:
            traceback.print_exc()

    def create(self, vals: dict, approval_step: "Approval", user: "ResUsers"):
        try:
            org_names = [approval_step.requester_id.organization_name]
            org_names = list(filter(lambda x: x != user.organization_name, org_names))
            header = {
                "method": "create",
                "org_names": org_names,
                "entity": "approval.step",
            }
            produce(self.env, vals, header)
        except Exception as e:
            traceback.print_exc()


class ApprovalIntegrationService:

    def __init__(self, env):
        self.env = env
        self.approval_client = ApprovalKafkaClient(self.env)

    def update(self, vals: dict, approval_step: "Approval", user: "ResUsers"):

        self.approval_client.update(vals, approval_step, user)

    def create(self, vals: dict, approval_step: "Approval", user: "ResUsers"):

        self.approval_client.create(vals, approval_step, user)
