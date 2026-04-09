class AlertRepository:
    def __init__(self):
        self._items = []

    def add(self, item):
        self._items.append(item)

    def list(self):
        return list(self._items)
