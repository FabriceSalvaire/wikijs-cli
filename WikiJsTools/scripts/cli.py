#! /usr/bin/env python3

####################################################################################################
#
# wikijs-cli - A CLI for Wiki.js
# Copyright (C) 2025 Fabrice SALVAIRE
# SPDX-License-Identifier: GPL-3.0-or-later
#
####################################################################################################

__all__ = ['main']

####################################################################################################

from dataclasses import dataclass
from pathlib import Path

from yaml import load
from yaml import Loader

from WikiJsTools.WikiJsApi import WikiJsApi
from WikiJsTools.Cli import Cli

####################################################################################################

@dataclass
class Config:
    API_URL: str
    API_KEY: str

####################################################################################################

def load_config(path: Path | str) -> Config:
    with open(path) as fh:
        _ = load(fh, Loader=Loader)
    return Config(**_)

####################################################################################################

def main():
    CONFIG_PATH = Path('~/.config/wikijs-cli/config.yaml').expanduser()
    config = load_config(CONFIG_PATH)
    api = WikiJsApi(api_url=config.API_URL, api_key=config.API_KEY)
    cli = Cli(api)
    cli.cli(query='')
