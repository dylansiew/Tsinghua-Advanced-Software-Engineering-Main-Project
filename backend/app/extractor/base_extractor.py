from types import Recommendation

class BaseExtractor:
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url

    def extract(self, url: str) -> list[Recommendation]:
        pass
