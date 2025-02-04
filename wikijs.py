####################################################################################################

from dataclasses import dataclass

from yaml import load
from yaml import Loader

from WikiJsApi import Page, WikiJsApi
from Cli import Cli

####################################################################################################

@dataclass
class Config:
    API_URL: str
    API_KEY: str

####################################################################################################

with open('config.yaml') as fh:
    _ = load(fh, Loader=Loader)
    config = Config(**_)

api = WikiJsApi(api_url=config.API_URL, api_key=config.API_KEY)
cli = Cli(api)
cli.cli(query='')
