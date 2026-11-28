from dataclasses import dataclass
from enum import Enum


class ZoneType(Enum):
    """Tipo di zona, ne determina il costo e l'accessibilità"""
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"

    @property
    def is_traversable(self) -> bool:
        """Restituisce True se i droni possono passare in questa zona"""
        return self is not ZoneType.BLOCKED

    @property
    def entry_cost(self) -> int:
        """Restituisce il numero di turni necessari per entrare questa zona.

        Raises:
            ValueError: Se la zona è blocked.
        """
        if self is ZoneType.BLOCKED:
            raise ValueError("blocked zones cannot be entered")
        if self is ZoneType.RESTRICTED:
            return 2
        return 1


@dataclass(frozen=True)
class Zone:
    """Una zona nella mappa"""

    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    color: str | None = None
    max_drones: int = 1
    is_start: bool = False
    is_end: bool = False

    @property
    def is_traversable(self) -> bool:
        """Richiama il metodo di ZoneType per vedere se la zona è blocked"""
        return self.zone_type.is_traversable

    @property
    def entry_cost(self) -> int:
        """Richiama ZoneType per calcolare i turni per entrare nella zona"""
        return self.zone_type.entry_cost


@dataclass(frozen=True)
class Connection:
    """Una connessione tra due zone nella mappa"""
    start_zone: str
    end_zone: str
    max_link_capacity: int = 1

    def other(self, name: str) -> str:
        """Restituisce l'altra zona in una Connection.'"""
        return self.end_zone if name == self.start_zone else self.start_zone


class Graph:
    """Da fare"""
