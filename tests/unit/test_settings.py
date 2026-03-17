"""Unit tests for SettingsStore. Write FIRST — must FAIL before implementation."""
import json

from src.config.settings import DEFAULT_MODEL, Settings


class TestSettingsStore:
    def test_load_returns_defaults_when_no_file(self, tmp_path):
        from unittest.mock import patch

        from src.config.settings import SettingsStore

        with patch("platformdirs.user_config_dir", return_value=str(tmp_path)):
            store = SettingsStore()
            settings = store.load()

        assert settings.model_id == DEFAULT_MODEL

    def test_save_and_load_round_trip(self, tmp_path):
        from unittest.mock import patch

        from src.config.settings import SettingsStore

        with patch("platformdirs.user_config_dir", return_value=str(tmp_path)):
            store = SettingsStore()
            store.save(Settings(model_id="small"))
            loaded = store.load()

        assert loaded.model_id == "small"

    def test_invalid_model_id_resets_to_default(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        settings_file.write_text(json.dumps({"model_id": "invalid-model"}))
        from unittest.mock import patch

        from src.config.settings import SettingsStore

        with patch("platformdirs.user_config_dir", return_value=str(tmp_path)):
            store = SettingsStore()
            settings = store.load()

        assert settings.model_id == DEFAULT_MODEL

    def test_load_handles_corrupt_json(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        settings_file.write_text("not valid json {{{")
        from unittest.mock import patch

        from src.config.settings import SettingsStore

        with patch("platformdirs.user_config_dir", return_value=str(tmp_path)):
            store = SettingsStore()
            settings = store.load()

        assert settings.model_id == DEFAULT_MODEL
