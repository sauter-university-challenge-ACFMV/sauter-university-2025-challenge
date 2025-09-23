from abc import ABC, abstractmethod
from typing import IO

class FileRepository(ABC):
    @abstractmethod
    def upload(self, file: IO[bytes], filename: str, content_type: str) -> str:
        """Upload the given bytes stream and return a public URL or path."""
        raise NotImplementedError

