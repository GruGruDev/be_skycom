import json

import requests


class Airflow:
    host = "https://airflow.skycom.vn/api/v1"

    @classmethod
    def call_trigger_new_dag_run(cls, dag_id, data=None):
        url = cls.host + f"/dags/{dag_id}/dagRuns"

        data = data if data is not None else {}
        payload = json.dumps(data)
        headers = {"Content-Type": "application/json", "Accept": "application/json", "Authorization": "Basic c2t5Y29tOlNreWNvbUAxMjM="}

        response = requests.request("POST", url, headers=headers, data=payload)

        return response
