from typing import Any

from graph import Graph
from models import Connection, Zone, ZoneType


class ParseError(Exception):
    """Errore di parsing con riga e causa."""
    def __init__(self, line: int | None, message: str,) -> None:
        self.line = line
        if line is None:
            super().__init__(message)
        else:
            super().__init__(f"Line {line}: {message}")


class MapParser:
    """Legge un file mappa e produce un Graph."""
    ZONE_KEYS = {"zone", "color", "max_drones"}
    CONNECTION_KEYS = {"max_link_capacity"}

    def __init__(self) -> None:
        self.nb_drones: int = 0
        self.zones: dict[str, Zone] = {}
        self.connections: dict[frozenset[str], Connection] = {}
        self.start: str | None = None
        self.end: str | None = None

    def _validate(self) -> None:
        """Controlla che ci siano gli elementi richiesti dopo il parsing."""
        if self.nb_drones == 0:
            raise ParseError(None, "'nb_drones' is missing")
        if self.start is None:
            raise ParseError(None, "'start_hub' is missing")
        if self.end is None:
            raise ParseError(None, "'end_hub' is missing")

    def _build_graph(self) -> Graph:
        """Crea Graph con i dati raccolti dal parsing."""
        if self.start is None or self.end is None:
            raise ParseError(None, "start or end zone is missing")
        graph = Graph(
            zones=self.zones,
            connections=self.connections,
            nb_drones=self.nb_drones,
            start=self.start,
            end=self.end,
        )
        return graph

    def parse_file(self, path: str) -> Graph:
        """Apre il file config ed esegue il parsing su ogni riga,
        successivamente valida i dati e crea il Graph."""
        with open(path, encoding="utf-8") as f:
            for line, raw in enumerate(f, start=1):
                self._parse_line(line, raw)
        self._validate()
        return self._build_graph()

    def _parse_line(self, line: int, raw: str) -> None:
        """Legge ogni riga del file config e le smista al parser appropriato"""

        raw = raw.split("#", 1)[0].strip()
        if not raw:
            return

        if ":" not in raw:
            raise ParseError(
                line, f"correct format is key: value, got '{raw}'")
        key, value = raw.split(":", 1)
        key = key.strip()
        value = value.strip()

        if key != "nb_drones" and self.nb_drones == 0:
            raise ParseError(
                line, "nb_drones must be defined before zones and connections"
            )
        if key == "nb_drones":
            self._parse_drones(line, value)
        elif key == "start_hub" or key == "end_hub" or key == "hub":
            self._parse_zones(line, key, value)
        elif key == "connection":
            self._parse_connections(line, key, value)
        else:
            raise ParseError(line, f"invalid prefix: {key}")

    @staticmethod
    def _parse_positive_int(line: int, value: str) -> int:
        """Controlla che il numero sia positivo e lo trasforma in int"""
        try:
            n = int(value)
        except ValueError:
            raise ParseError(
                line, f"value must be a positive integer, got '{value}'"
            ) from None
        if n <= 0:
            raise ParseError(
                line, f"value must be a positive integer, got '{value}'"
            )
        return n

    def _parse_drones(self, line: int, value: str) -> None:
        """Valida ed imposta il numero di droni"""
        if self.nb_drones != 0:
            raise ParseError(line, "value 'nb_drones' is already set")
        self.nb_drones = self._parse_positive_int(line, value)

    def _parse_coordinate(self, line: int, n: str) -> int:
        """Valida le coordinate delle zone"""
        try:
            coord = int(n)
        except ValueError:
            raise ParseError(
                line, f"coordinates must be integers, got '{n}'"
            ) from None
        return coord

    def _parse_metadata(
                self, line: int, type: str, data: str) -> dict[str, Any]:
        """Controlla che i metadata siano corretti e li salva in un dict"""
        data = data.strip()
        data = data.split("]", 1)[0]

        if type == "connection":
            allowed = self.CONNECTION_KEYS
        else:
            allowed = self.ZONE_KEYS

        metadata: dict[str, Any] = {}
        for token in data.split():
            if "=" not in token:
                raise ParseError(
                    line, f"metadata must be key=value, got '{token}'")
            key, value = token.split("=", 1)
            if not key or not value:
                raise ParseError(line, f"invalid metadata, got {token}")

            if key not in allowed:
                raise ParseError(
                    line,
                    f"invalid key '{key}' for '{type}', "
                    f"expected one of: {', '.join(sorted(allowed))}",
                )
            if key in metadata:
                raise ParseError(line, f"duplicate key: '{key}'")

            if key == "zone":
                try:
                    metadata[key] = ZoneType(value)
                except ValueError:
                    raise ParseError(
                        line,
                        f"invalid zone type '{value}', expected one of: "
                        f"{', '.join(t.value for t in ZoneType)}",
                    ) from None
            elif key == "max_drones":
                if type in ("start_hub", "end_hub"):
                    continue
                metadata[key] = self._parse_positive_int(line, value)
            elif key == "color":
                metadata[key] = value
            elif key == "max_link_capacity":
                metadata[key] = self._parse_positive_int(line, value)

        return metadata

    def _parse_zones(self, line: int, key: str, value: str) -> None:
        """Crea un oggetto Zone con name, x, y e i metadata

        Args:
            line (int): linea del file presa in considerazione
            key (str): "start_hub", "end_hub" o "hub"
            value (str): name x y + metadata se ci sono

        Raises:
            ParseError: se ci sono errori nel file di configurazione"""
        data: str = ""
        if "[" in value:
            value, data = value.split("[", 1)

        tokens = value.split()
        if len(tokens) != 3:
            raise ParseError(
                line, f"correct format is zone_name x y, got '{value}'")
        name, raw_x, raw_y = tokens

        if "-" in name:
            raise ParseError(
                line, f"zone names can't contain '-' or ' ', got {name}"
            )
        if name in self.zones:
            raise ParseError(line, f"duplicate zone name '{name}'")
        if key == "start_hub" and self.start is not None:
            raise ParseError(line, "value 'start_hub' is already set")
        if key == "end_hub" and self.end is not None:
            raise ParseError(line, "value 'end_hub' is already set")
        x = self._parse_coordinate(line, raw_x)
        y = self._parse_coordinate(line, raw_y)

        metadata: dict[str, Any] = {}
        if data:
            metadata = self._parse_metadata(line, key, data)

        if (key in ("start_hub", "end_hub")
                and metadata.get("zone") == ZoneType.BLOCKED):
            raise ParseError(line, f"'{key}' can't be a blocked zone")

        zone = Zone(
            name=name,
            x=x,
            y=y,
            zone_type=metadata.get("zone", ZoneType.NORMAL),
            color=metadata.get("color", None),
            max_drones=metadata.get("max_drones", 1),
            is_start=key == "start_hub",
            is_end=key == "end_hub",
        )
        if key == "start_hub":
            self.start = name
        if key == "end_hub":
            self.end = name
        self.zones[name] = zone

    def _parse_connections(self, line: int, key: str, link: str) -> None:
        """Crea un oggetto Connection che connette due Zone."""
        data: str = ""
        if "[" in link:
            link, data = link.split("[", 1)
        link = link.strip()
        tokens = link.split("-")
        if len(tokens) != 2:
            raise ParseError(
                line, f"correct format is zone1-zone2, got '{link}'")
        zone_a, zone_b = tokens

        if zone_a == zone_b:
            raise ParseError(
                line,
                f"connection has to be between different zones, got '{link}'")
        if zone_a not in self.zones:
            raise ParseError(line,
                             f"invalid zone in connection, got '{zone_a}'")
        if zone_b not in self.zones:
            raise ParseError(line,
                             f"invalid zone in connection, got '{zone_b}'")
        pair = frozenset({zone_a, zone_b})
        if pair in self.connections:
            raise ParseError(line,
                             f"duplicate connection '{zone_a}-{zone_b}'")

        metadata: dict[str, Any] = {}
        if data:
            metadata = self._parse_metadata(line, key, data)

        connection = Connection(
            start_zone=zone_a,
            end_zone=zone_b,
            max_link_capacity=metadata.get("max_link_capacity", 1),
        )
        self.connections[pair] = connection
