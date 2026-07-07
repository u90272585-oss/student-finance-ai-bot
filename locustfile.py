from locust import HttpUser, task, between

print("LOADED LOCUSTFILE")

class FinanceBotUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def check_health(self):
        print("TASK RUNNING")
        self.client.get("/health")