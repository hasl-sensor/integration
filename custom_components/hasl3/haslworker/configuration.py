"""HACS Configuration."""
import attr
from integrationhelper import Logger
from custom_components.hasl3.haslworker.exceptions import HaslException


@attr.s(auto_attribs=True)
class Configuration:
    """Configuration class."""

    # Main configuration:
    config: dict = {}
    config_entry: dict = {}
    config_type: str = None
    options: dict = {}
    name: str = None

    # Config options:
    debug: bool = False
    api_minimization: bool = True
    ri4key: str = None
    si2key: str = None
    tl2key: str = None

    def to_json(self):
        """Return a dict representation of the configuration."""
        return self.__dict__

    def print(self):
        """Print the current configuration to the log."""
        logger = Logger("hacs.configuration")
        config = self.to_json()
        for key in config:
            if key in ["config", "config_entry", "options"]:
                continue
            logger.debug(f"{key}: {config[key]}")

    @staticmethod
    def from_dict(configuration: dict, options: dict):
        """Set attributes from dicts."""
        if isinstance(options, bool) or isinstance(configuration.get("options"), bool):
            raise HacsException("Configuration is not valid.")

        if options is None:
            options = {}

        if not configuration:
            raise HaslException("Configuration is not valid.")

        config = Configuration()

        config.config = configuration
        config.options = options

        for conf_type in [configuration, options]:
            for key in conf_type:
                setattr(config, key, conf_type[key])

        return config
