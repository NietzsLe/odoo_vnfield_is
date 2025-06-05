from typing import TYPE_CHECKING
from .approval import ISApprovalClient
import traceback
from ...kafka_producer import produce

if TYPE_CHECKING:
    from ...models.approval_step import ApprovalStep

from ...models.res_users import ResUsers


class ApprovalStepKafkaClient:
    def __init__(self, env):
        self.env = env

    def update(self, vals: dict, approval_step: "ApprovalStep", user: "ResUsers"):
        try:
            org_names = [approval_step.approver_id.organization_name]
            org_names = list(filter(lambda x: x != user.organization_name, org_names))
            header = {
                "method": "update",
                "org_names": org_names,
                "entity": "approval.step",
            }
            produce(self.env, vals, header)
        except Exception as e:
            traceback.print_exc()

    def create(self, vals: dict, approval_step: "ApprovalStep", user: "ResUsers"):
        try:
            org_names = [approval_step.approver_id.organization_name]
            org_names = list(filter(lambda x: x != user.organization_name, org_names))
            header = {
                "method": "create",
                "org_names": org_names,
                "entity": "approval.step",
            }
            produce(self.env, vals, header)
        except Exception as e:
            traceback.print_exc()


class ApprovalStepIntegrationService:

    def __init__(self, env):
        self.env = env
        self.approval_step_client = ApprovalStepKafkaClient(self.env)

    def update(self, vals: dict, approval_step: "ApprovalStep", user: "ResUsers"):

        if approval_step.approver_id and not self.helper.user_is_internal(
            approval_step.approver_id
        ):
            if not approval_step["external_id"]:
                if approval_step.approval_id.id:
                    approval_data = approval_step.approval_id.to_dict()
                    response = self.approval_client.create(approval_data, user)
                    approval_step.approval_id.write(
                        {"external_id": response["external_id"]}
                    )
                approval_step_data = approval_step.to_dict()
                approval_step_data["approver_id"] = (
                    approval_step.approver_id.external_id
                )
                response = self.approval_step_client.create(
                    approval_step_data, approval_step, user
                )
                print("@Update response: ", response)
                approval_step.write({"external_id": response["external_id"]})
            else:
                self.approval_step_client.update(vals, approval_step, user)

    def create(self, vals: dict, approval_step: "ApprovalStep", user: "ResUsers"):

        if approval_step.approver_id.id and not self.helper.user_is_internal(
            approval_step.approver_id
        ):
            if approval_step.approval_id.id:
                approval_data = approval_step.approval_id.to_dict()
                approval_data["requester_id"] = (
                    approval_step.approval_id.requester_id.external_id
                )
                response = self.approval_client.create(
                    approval_data, approval_step, user
                )
                approval_step.approval_id.write(
                    {"external_id": response["external_id"]}
                )
            approval_step_data = approval_step.to_dict()
            approval_step_data["approver_id"] = approval_step.approver_id.external_id
            response = self.approval_step_client.create(
                approval_step_data, approval_step, user
            )
            approval_step.write({"external_id": response["external_id"]})
