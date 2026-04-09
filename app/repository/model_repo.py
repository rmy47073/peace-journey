class ModelRepository:
    def __init__(self):
        self._models = {}

    def save(self, name, metadata):
        self._models[name] = metadata

    def get(self, name):
        return self._models.get(name)
