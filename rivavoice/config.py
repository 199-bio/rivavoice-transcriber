"""
Handles loading and saving application configuration from a JSON file.
"""
import os
import json
import logging
from . import constants  # Import constants

logger = logging.getLogger(constants.APP_NAME)  # Use constant for logger name

# Default config file location - Use constant
# DEFAULT_CONFIG_FILE = os.path.expanduser("~/.rivavoiceconfig.json")


class Config:
    def __init__(self, config_file=None):
        self.config_file = config_file or constants.DEFAULT_CONFIG_FILE  # Use constant
        self.data = (
            constants.DEFAULT_CONFIG.copy()
        )  # Use constant default config, ensure it's a copy
        self.load()

        logger.info(f"Config initialized with file: {self.config_file}")

    # _default_config method is no longer needed as we use constants.DEFAULT_CONFIG

    def load(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    loaded_data = json.load(f)

                    # Update config with loaded values
                    self.data.update(loaded_data)

                logger.info("Config loaded successfully")
                return True
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading config: {e}")
                return False
        else:
            logger.info(f"No config file found at {self.config_file}, using defaults")
            # No need to return False explicitly, load just didn't update data
            pass  # Or return False if needed elsewhere

    def save(self):
        """Save current configuration to file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            with open(self.config_file, "w") as f:
                json.dump(self.data, f, indent=2)

            logger.info("Config saved successfully")
            return True
        except IOError as e:
            logger.error(f"Error saving config: {e}")
            return False

    def get(self, key, default=None):
        """Get configuration value"""
        return self.data.get(key, default)

    def set(self, key, value):
        """Set configuration value"""
        self.data[key] = value

    def update(self, config_dict):
        """Update multiple configuration values at once"""
        self.data.update(config_dict)


# For testing purposes
if __name__ == "__main__":
    # Setup console logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger_test = logging.getLogger(constants.APP_NAME)  # Use constant
    logger_test.info("--- Testing Config ---")

    # Test config
    config = Config()

    # Print current config
    logger_test.info("Initial config (defaults or loaded):")
    for key, value in config.data.items():
        logger_test.info(f"  {key}: {value}")

    # Update a value using constant key
    config.set(constants.CONFIG_API_KEY, "test_key_123")
    config.set(constants.CONFIG_SOUND_EFFECTS, False)
    logger_test.info(
        f"Updated '{constants.CONFIG_API_KEY}' and '{constants.CONFIG_SOUND_EFFECTS}'"
    )

    # Save config
    if config.save():
        # Load again into a new instance
        logger_test.info("Loading config again...")
        new_config = Config()
        logger_test.info("Loaded config:")
        for key, value in new_config.data.items():
            logger_test.info(f"  {key}: {value}")

        # Clean up test file
        try:
            os.remove(constants.DEFAULT_CONFIG_FILE)
            logger_test.info(
                f"Cleaned up test config file: {constants.DEFAULT_CONFIG_FILE}"
            )
        except OSError as e:
            logger_test.error(f"Could not remove test config file: {e}")
    else:
        logger_test.error("Failed to save config during test.")

    logger_test.info("--- Config Test End ---")
