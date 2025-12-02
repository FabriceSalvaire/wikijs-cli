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

import argparse
import logging

from WikiJsTools.fuse import mount
from WikiJsTools.WikiJsApi import WikiJsApi
from WikiJsTools import config as Config

####################################################################################################

def main():
    parser = argparse.ArgumentParser(
        prog='wikijs-fuse',
        description='Fuse mount for Wiki.js',
        epilog='',
    )
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('mount')
    args = parser.parse_args()

    if args.debug:
        Config.DEBUG = True

    config = Config.load_config()
    api = WikiJsApi(api_url=config.API_URL, api_key=config.API_KEY)
    # level = logging.DEBUG
    level = logging.INFO
    logging.basicConfig(level=level)
    mount(api, args.mount)
