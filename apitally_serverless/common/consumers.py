from dataclasses import dataclass


_seen_consumer_hashes: set[int] = set()


@dataclass
class ApitallyConsumer:
    identifier: str
    name: str | None = None
    group: str | None = None

    def __post_init__(self) -> None:
        self.identifier = str(self.identifier).strip()[:128]
        self.name = str(self.name).strip()[:64] if self.name else None
        self.group = str(self.group).strip()[:64] if self.group else None

        if self.name or self.group:
            h = hash((self.identifier, self.name, self.group))
            if h in _seen_consumer_hashes:
                self.name = None
                self.group = None
            else:
                _seen_consumer_hashes.add(h)
