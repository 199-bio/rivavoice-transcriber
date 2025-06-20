import pytest
import os
import json
from rivavoice.config import Config
from rivavoice import constants

# Use pytest's tmp_path fixture for temporary files/directories
def test_config_load_defaults_no_file(tmp_path):
    """Test loading config when the config file doesn't exist."""
    # Use a non-existent file path within the temp directory
    non_existent_file = tmp_path / "non_existent_config.json"
    config = Config(config_file=str(non_existent_file))
    config.load()

    # Check if the config dictionary matches the defaults
    assert config.data == constants.DEFAULT_CONFIG
    assert config.get(constants.CONFIG_KEYBIND) == constants.DEFAULT_KEYBIND

def test_config_save_load_cycle(tmp_path):
    """Test saving config and then loading it back."""
    config_file = tmp_path / "test_config.json"
    config1 = Config(config_file=str(config_file))

    # Modify a value
    new_keybind = "ctrl+shift+a"
    config1.set(constants.CONFIG_KEYBIND, new_keybind)
    config1.save()

    # Ensure file was created
    assert config_file.is_file()

    # Create a new config instance and load from the saved file
    config2 = Config(config_file=str(config_file))
    config2.load()

    # Check if the loaded config has the modified value
    assert config2.get(constants.CONFIG_KEYBIND) == new_keybind
    # Check if other values are still defaults (assuming only keybind was changed)
    assert config2.get(constants.CONFIG_SOUND_EFFECTS) == constants.DEFAULT_SOUND_EFFECTS

def test_config_load_existing_file(tmp_path):
    """Test loading an existing config file with custom values."""
    config_file = tmp_path / "existing_config.json"
    custom_settings = {
        constants.CONFIG_KEYBIND: "alt+k",
        constants.CONFIG_SOUND_EFFECTS: False,
        constants.CONFIG_TRANSCRIPT_FOLDER: "/custom/path",
        # Add other settings as needed
    }
    # Create the config file manually
    with open(config_file, "w") as f:
        json.dump(custom_settings, f)

    config = Config(config_file=str(config_file))
    config.load()

    # Check if loaded values match the custom settings
    assert config.get(constants.CONFIG_KEYBIND) == "alt+k"
    assert config.get(constants.CONFIG_SOUND_EFFECTS) is False
    assert config.get(constants.CONFIG_TRANSCRIPT_FOLDER) == "/custom/path"
    # Check if a default value is still present if not in the custom file
    assert config.get(constants.CONFIG_SELECTED_MODEL_ID) == constants.DEFAULT_MODEL_ID