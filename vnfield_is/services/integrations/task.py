from typing import TYPE_CHECKING
import traceback
from ...kafka_producer import produce

if TYPE_CHECKING:
    from ...models.task import Task

from ...models.res_users import ResUsers


class TaskKafkaClient:
    def __init__(self, env):
        self.env = env

    def update(self, vals: dict, task: "Task", user: "ResUsers"):
        try:
            org_names = [task.approver_id.organization_name]
            org_names = list(filter(lambda x: x != user.organization_name, org_names))
            header = {
                "method": "update",
                "org_names": org_names,
                "entity": "approval.step",
                "id": task.id,
            }
            produce(self.env, vals, header)
        except Exception as e:
            traceback.print_exc()

    def create(self, vals: dict, task: "Task", user: "ResUsers"):
        try:
            org_names = [task.approver_id.organization_name]
            org_names = list(filter(lambda x: x != user.organization_name, org_names))
            header = {
                "method": "create",
                "org_names": org_names,
                "entity": "approval.step",
                "id": task.id,
            }
            produce(self.env, vals, header)
        except Exception as e:
            traceback.print_exc()


class TaskIntegrationService:

    def __init__(self, env):
        self.env = env
        self.task_client = TaskKafkaClient(self.env)

    def update(self, vals: dict, task: "Task", user: "ResUsers"):

        self.task_client.update(vals, task, user)

    def create(self, vals: dict, task: "Task", user: "ResUsers"):

        self.task_client.create(vals, task, user)
