import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    host: str = "0.0.0.0"
    port: int = 8000
    source_mode: str = "ruview"
    ruview_base_url: str = "http://192.168.50.50:3000"
    data_path: Path = Path("data/game.json")
    poll_hz: float = 10.0
    movement_floor: float = 1.0
    arrival_threshold: float = 0.62
    arrival_ticks: int = 8

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            host=os.getenv("GEIST_HOST", "0.0.0.0"),
            port=int(os.getenv("GEIST_PORT", "8000")),
            source_mode=os.getenv("GEIST_SOURCE", "ruview"),
            ruview_base_url=os.getenv("RUVIEW_BASE_URL", "http://192.168.50.50:3000").rstrip("/"),
            data_path=Path(os.getenv("GEIST_DATA_PATH", "data/game.json")),
            poll_hz=float(os.getenv("GEIST_POLL_HZ", "10")),
            movement_floor=float(os.getenv("GEIST_MOVEMENT_FLOOR", "1.0")),
            arrival_threshold=float(os.getenv("GEIST_ARRIVAL_THRESHOLD", "0.62")),
            arrival_ticks=int(os.getenv("GEIST_ARRIVAL_TICKS", "8")),
        )
