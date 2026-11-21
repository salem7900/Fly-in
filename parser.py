class ParseError(Exception):
    """Errore di parsing con riga e causa."""

    def __init__(self, line: int, message: str) -> None:
        super().__init__(f"Line {line}: {message}")


class MapParser:
    """Legge un file mappa e produce un Graph."""

    def __init__(self) -> None:
        self.nb_drones: int = 0
        self.zones: dict[str, Zone] = {}
        self.connections: list[Connection] = []
        self.start: str | None = None
        self.end: str | None = None

    def parse_file(self, path: str) -> Graph:
        with open(path, encoding="utf-8") as f:
            for line, raw in enumerate(f, start=1):
                self._parse_line(line, raw)

    def _parse_line(self, line: int, raw: str) -> None:

        raw = raw.split("#", 1)[0].strip()
        if not raw:
            return

        if ":" not in raw:
            raise ParseError(
                line, f"correct format is key:value, got '{raw}'")
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
            self._parse_connections(line, value)
        else:
            raise ParseError(line, f"invalid prefix: {key}")

    def _parse_drones(self, line: int, value: str) -> None:
        """Valida ed imposta il numero di droni"""
        if self.nb_drones != 0:
            raise ParseError(line, "value 'nb_drones' is already set")
        try:
            nb_drones = int(value)
        except ValueError:
            raise ParseError(
                line, f"'nb_drones' must be a positive integer, got '{value}'"
            ) from None
        if nb_drones <= 0:
            raise ParseError(
                line, f"'nb_drones' must be a positive integer, got '{value}'"
            )
        self.nb_drones = nb_drones

    def _parse_coordinate(self, line: int, n: str) -> int:
        """Valida le coordinate delle zone"""
        try:
            coord = int(n)
        except ValueError:
            raise ParseError(
                line, f"coordinates must be integers, got '{n}'"
            ) from None
        return coord

    def _parse_zones(self, line: int, key: str, value: str) -> None:
        """"""
        if "[" in value:
            value, data = value.split("[", 1)

        tokens = value.split()
        if len(tokens) != 3:
            raise ParseError(
                line, f"correct format is zone_name x y, got '{value}'")
        name, raw_x, raw_y = tokens

        if "-" in name:
            raise ParseError(
                line, f"zone names can't contain '-', got {name}"
            )
        if name in self.zones:
            raise ParseError(line, f"duplicate zone name '{name}'")
        if key == "start_hub" and self.start is not None:
            raise ParseError(line, "value 'start_hub' is already set")
        if key == "end_hub" and self.end is not None:
            raise ParseError(line, "value 'end_hub' is already set")
        x = self._parse_coordinate(line, raw_x)
        y = self._parse_coordinate(line, raw_y)

        if data:
            self._parse_metadata(line, key, data)
