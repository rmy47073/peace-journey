class VideoSourceRepository:
    def __init__(self):
        self._sources = {}

    def save(self, source_id, config):
        self._sources[source_id] = config

    def get(self, source_id):
        return self._sources.get(source_id)
