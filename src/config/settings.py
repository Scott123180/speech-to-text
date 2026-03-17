import json
from dataclasses import asdict, dataclass
from pathlib import Path

import platformdirs

from src.exceptions import SettingsError

VALID_MODELS = frozenset(
    {"tiny", "base", "small", "medium", "large-v3", "distil-large-v3"}
)
DEFAULT_MODEL = "base"
APP_NAME = "speech-to-text"


@dataclass
class Settings:
    model_id: str = DEFAULT_MODEL


class SettingsStore:
    """Persists user preferences to the OS user config directory."""

    def __init__(self) -> None:
        config_dir = Path(platformdirs.user_config_dir(APP_NAME))
        config_dir.mkdir(parents=True, exist_ok=True)
        self._path = config_dir / "settings.json"

    def load(self) -> Settings:
        """Return saved settings, or defaults if missing/corrupt."""
        if not self._path.exists():
            return Settings()
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            model_id = data.get("model_id", DEFAULT_MODEL)
            if model_id not in VALID_MODELS:
                model_id = DEFAULT_MODEL
            return Settings(model_id=model_id)
        except (json.JSONDecodeError, KeyError, OSError):
            return Settings()

    def save(self, settings: Settings) -> None:
        """Write settings to disk atomically."""
        try:
            self._path.write_text(
                json.dumps(asdict(settings), indent=2), encoding="utf-8"
            )
        except OSError as exc:
            raise SettingsError(str(exc)) from exc
