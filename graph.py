from models import Connection, Zone


class Graph:
    """Static map of zones and connections, with adjacency lists."""

    def __init__(
        self,
        zones: dict[str, Zone],
        connections: dict[frozenset[str], Connection],
        nb_drones: int,
        start: str,
        end: str,
    ) -> None:
        """Crea la mappa delle zone e la lista dei vicini di ogni zona.

        Args:
        zones: Tutte le Zone nella mappa.
        connections: Tutte le Connection, come key hanno i nomi delle due zone.
        nb_drones: Numero di droni.
        start: Nome della zona d'inizio.
        end: Nome della zona finale.

        Raises:
            ValueError: Se start o end non sono una zona valida."""
        if start not in zones or end not in zones:
            raise ValueError("start or end zone is not in the graph")

        self._zones: dict[str, Zone] = zones
        self._connections: dict[frozenset[str], Connection] = connections
        self._nb_drones: int = nb_drones
        self._start: str = start
        self._end: str = end
        self._adjacency: dict[str, list[Connection]] = {
            name: [] for name in zones
        }

        for conn in connections.values():
            if conn.start_zone not in zones or conn.end_zone not in zones:
                raise ValueError(
                    f"connection {conn.start_zone}-{conn.end_zone} "
                    "refers to an unknown zone"
                )
            self._adjacency[conn.start_zone].append(conn)
            self._adjacency[conn.end_zone].append(conn)

    @property
    def start(self) -> Zone:
        """Restituisce la zona Start"""
        return self.get_zone(self._start)

    @property
    def end(self) -> Zone:
        """Restituisce la zona End"""
        return self.get_zone(self._end)

    @property
    def nb_drones(self) -> int:
        """Restituisce il numero di droni"""
        return self._nb_drones

    def get_zone(self, name: str) -> Zone:
        """Restituisce l'oggetto Zona associato a 'name'"""
        return self._zones[name]

    def get_all_zones(self) -> dict[str, Zone]:
        """Restituisce tutte le Zone"""
        return self._zones

    def get_neighbors(self, name: str) -> list[tuple[Zone, Connection]]:
        """Restituisce le zone vicine che non sono Blocked
        e la Connection usata"""
        result: list[tuple[Zone, Connection]] = []
        for conn in self._adjacency[name]:
            neighbor = self.get_zone(conn.other(name))
            if neighbor.is_traversable:
                result.append((neighbor, conn))
        return result
