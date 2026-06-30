from locust import HttpUser, task, between

class FinanceBotUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def check_health(self):
        self.client.get("/health")

    @task(1)
    def check_metrics(self):
        self.client.get(
            "/metrics",
            auth=("admin", "admin123")
        )
