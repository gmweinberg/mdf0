from dataclasses import dataclass
from configparser import ConfigParser

@dataclass
class  Mdf0SqlConfig:
    user: str
    password: str
    database: str
    host: str


def get_config(config_filename):
    """Return a Mdf0SqlConfig from the filename."""
    config = ConfigParser()
    config.read(config_filename)
    sqlconf = Mdf0SqlConfig(host=config.get('sql', 'host'), user=config.get('sql', 'user'), password=config.get('sql', 'password'), database=config.get('sql', 'database'))
    print(repr(sqlconf))
    return sqlconf

