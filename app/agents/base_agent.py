from abc import ABC, abstractmethod


class BaseAgent(ABC):
    @abstractmethod
    def run(self, data: dict) -> dict:
        pass