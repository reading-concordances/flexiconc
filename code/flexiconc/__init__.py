import os
import subprocess
from platformdirs import user_config_dir
from configparser import ConfigParser

from jsonschema import validate as jsonschema_validate
import builtins

# Make the jsonschema validate function globally available as "validate"
builtins.validate = jsonschema_validate

# Function to read configuration variables
def load_config():
    # load defaults for platform
    config_file_path = os.path.join(user_config_dir("flexiconc"), "config.ini")

    if not os.path.exists(config_file_path):
        # print(f"Configuration file not found, creating defaults at {config_file_path}")

        os.makedirs(user_config_dir("flexiconc"), exist_ok=True)

        try:
            result = subprocess.run(["cwb-config", "-r"], capture_output=True)
            result.check_returncode()
            default_registry = result.stdout.decode().strip()
            # print("Default CWB Registry:", default_registry)
        except Exception as e:
            # raise Exception(f"Cannot create config file: cwb-config could not be run: {e}")
            default_registry = "/home"

        # load template from package dir and apply variables
        with open(os.path.join(os.path.dirname(__file__), "flexiconc_config_default.ini")) as f:
            defaults = f.read().format(default_registry)   

        with open(config_file_path, mode="w") as f:
            f.write(defaults)

    config = ConfigParser()

    config.read(config_file_path)
    return config


# Load configuration
CONFIG = load_config()

# Import Concordance class
from .concordance import Concordance

# Import TextImport class
from .text_import import TextImport
