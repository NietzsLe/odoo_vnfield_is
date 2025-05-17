import requests


class ApprovalClient:

    @classmethod
    def post(cls, approval, id, url):
        try:
            body = cls.filterProperty(approval)
            print(body, url)
            requests.post(
                url + "/approvals/" + str(id),
                json=body,
            )
        except:
            print("An exception occurred")

    @classmethod
    def put(cls, approval, id, url):
        try:
            body = cls.filterProperty(approval)
            print(body, url)
            requests.put(
                url + "/approvals/" + str(id),
                json=body,
            )
        except:
            print("An exception occurred")

    @classmethod
    def delete(cls, id, url):
        print(url)
        try:
            requests.delete(url + "/approvals/" + str(id))
        except:
            print("An exception occurred")

    @classmethod
    def filterProperty(cls, approval):
        fields_to_check = [
            "name",
            "description",
            "approval_period",
            "status",
            "priority",
        ]

        data = {}

        for field in fields_to_check:
            value = approval[field]
            if value != None and value != False:
                data[field] = value

        return data
