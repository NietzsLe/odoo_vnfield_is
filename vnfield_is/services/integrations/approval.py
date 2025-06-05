import requests
from .helper import IntegrationHelperService
from typing import TYPE_CHECKING
from .auth import AuthIntegrationService
import traceback

if TYPE_CHECKING:
    from ...models.approval import Approval
    from ...models.res_users import ResUsers


class ISApprovalClient:
    def __init__(self, env):
        self.env = env

        self.org_name = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("vnfield_cs.organization_name")
        )

        self.base_url = (
            self.env["ir.config_parameter"].sudo().get_param("vnfield_cs.host_of_is")
            + "/send_request?model=vnfield.approval"
        )

        self.auth_service = AuthIntegrationService(env)

    def update(self, vals: dict, approval: "Approval", user: "ResUsers"):
        try:
            body = {"fields": vals.keys(), "values": vals}
            if approval["external_id"]:
                url = self.base_url + "&Id=" + str(approval["external_id"])
                headers = {
                    "Content-Type": "application/json",
                    "login": user.external_login,
                    "password": user.external_password,
                    "api-key": self.auth_service.get_api_key(user),
                }
                print(body)
                requests.put(url, json=body, headers=headers)
        except Exception as e:
            traceback.print_exc()

    def create(self, vals: dict, user: "ResUsers"):
        try:
            body = {"fields": vals.keys(), "values": vals}
            url = self.base_url
            headers = {
                "Content-Type": "application/json",
                "login": user.external_login,
                "password": user.external_password,
                "api-key": self.auth_service.get_api_key(user),
            }
            print(body)
            response = requests.post(url, json=body, headers=headers)
            response_json = response.json()
            print("Approval create res: ", response_json)
            return {"external_id": response_json["New resource"][0]["id"]}
        except Exception as e:
            traceback.print_exc()


class ApprovalIntegrationService:

    def __init__(self, env):
        self.env = env

        self.helper = IntegrationHelperService(self.env)

        self.approval_client = ISApprovalClient(self.env)

    def update(self, vals: dict, approval: "Approval", user: "ResUsers"):

        if approval.requester_id and not self.helper.user_is_internal(
            approval.requester_id
        ):
            self.approval_client.update(vals, approval, user)
