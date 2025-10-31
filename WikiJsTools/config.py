####################################################################################################
#
# wikijs-cli - A CLI for Wiki.js
# Copyright (C) 2025 Fabrice SALVAIRE
# SPDX-License-Identifier: GPL-3.0-or-later
#
####################################################################################################

__all__ = [
    'CONFIG_PATH',
    'CONFIG_YAML_PATH',
    'CLI_HISTORY_PATH',
    'load_config', 
]

####################################################################################################

from dataclasses import dataclass
from pathlib import Path

from yaml import load
from yaml import Loader

####################################################################################################

CONFIG_PATH = Path('~/.config/wikijs-cli').expanduser()
CONFIG_YAML_PATH = CONFIG_PATH.joinpath('config.yaml')
CLI_HISTORY_PATH = CONFIG_PATH.joinpath('cli_history')

####################################################################################################

@dataclass
class Config:
    API_URL: str
    API_KEY: str

####################################################################################################

def load_config(path: Path | str = CONFIG_YAML_PATH) -> Config:
    with open(path) as fh:
        _ = load(fh, Loader=Loader)
    return Config(**_)
