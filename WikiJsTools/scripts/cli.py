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

from pathlib import Path

from WikiJsTools.Cli import Cli
from WikiJsTools.WikiJsApi import WikiJsApi
from WikiJsTools.config import load_config

####################################################################################################

def main():
    config = load_config()
    api = WikiJsApi(api_url=config.API_URL, api_key=config.API_KEY)
    cli = Cli(api)
    cli.cli(query='')
