"""
Definition of streaming module interfaces
"""

from abc import ABC
from abc import abstractmethod
from typing import Generic
from typing import List
from typing import Optional
from typing import TypeVar

# pylint: disable=invalid-name
T = TypeVar('T')
I = TypeVar('I')
O = TypeVar('O')


class Device(ABC, Generic[T]):
    """Represents a data stream adapter to a physical media device."""

    @abstractmethod
    def device_id(self) -> str:
        """ID of device."""

    @abstractmethod
    def start(self) -> None:
        """Start streaming data."""

    @abstractmethod
    def read(self, timeout: int) -> Optional[T]:
        """Read data frame with timeout."""

    @abstractmethod
    def stop(self) -> None:
        """Stop streaming data."""

    @abstractmethod
    def is_active(self) -> bool:
        """True if active, False otherwise."""

    @abstractmethod
    def more(self) -> bool:
        """True if data is available to be read, false otherwise."""


class Consumer(ABC, Generic[T]):
    """Represents a consumer of the transformed device data."""

    @abstractmethod
    def consumer_id(self) -> str:
        """ID of consumer."""

    @abstractmethod
    def consume(self, device_id: str, data: List[T]) -> None:
        """Dispatch data to downstream service"""

    @abstractmethod
    def batch_size(self) -> int:
        """Batch size for consumer."""


class Transformer(ABC, Generic[I, O]):
    """Transform source data."""

    @abstractmethod
    def transformer_id(self) -> str:
        """ID of transformer."""

    @abstractmethod
    def transform(self, data: I) -> O:
        """Transform source data into desired data type."""
