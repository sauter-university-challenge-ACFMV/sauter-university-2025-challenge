from abc import ABC, abstractmethod
from typing import Optional

class FileRepository(ABC):
    @abstractmethod
    def upload(self, file, filename: str, content_type: str) -> str:
        pass

