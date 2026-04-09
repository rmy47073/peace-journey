from app.repository.alert_repo import AlertRepository


class AlertService:
    def __init__(self, repository=None):
        self.repository = repository or AlertRepository()

    def record(self, alert_event):
        self.repository.add(alert_event)

    def list_all(self):
        return self.repository.list()
