# Contract: SettingsStore

**Module**: `src/config/settings.py`
**Type**: Internal service interface

## Responsibility

Persist and retrieve user preferences (selected model) to/from the OS
user config directory. Has no knowledge of the UI or transcription engine.

## Interface

```
SettingsStore
│
├── load() → Settings
│     Reads settings from disk. Returns defaults if file does not exist.
│
└── save(settings: Settings) → None
      Writes settings to disk atomically.
      Raises: SettingsError on I/O failure.
```

## Settings (value object)

```
Settings
├── model_id: str   # Default: "base"
                    # Valid values: "tiny", "base", "small", "medium",
                    #               "large-v3", "distil-large-v3"
```

## Storage

- Format: JSON
- Path (Linux): `~/.config/speech-to-text/settings.json`
- Path (macOS): `~/Library/Application Support/speech-to-text/settings.json`
- Path (Windows): `%APPDATA%\speech-to-text\settings.json`
- Resolved via `platformdirs.user_config_dir("speech-to-text")`

## Constraints

- MUST return safe defaults if config file is missing or corrupted.
- MUST validate `model_id` on load; reset to `"base"` if value is unrecognized.
- MUST NOT raise on missing file (treat as first run).
