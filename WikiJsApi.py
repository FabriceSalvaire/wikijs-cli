####################################################################################################

from dataclasses import dataclass
from typing import Iterator
from pprint import pprint

import requests

####################################################################################################

@dataclass
class Page:
    api: 'WikiJsApi'
    id: int
    path: str
    title: str
    locale: str

    content: str = None

    # hash: str
    # description: str
    # isPrivate: bool
    # isPublished: bool
    # privateNS: str
    # publishStartDate: Date
    # publishEndDate: Date
    # tags: [PageTag]
    # render: str
    # toc: str
    # contentType: str
    # createdAt: Date
    # updatedAt: Date
    # editor: str
    # scriptCss: str
    # scriptJs: str
    # authorId: int
    # authorName: str
    # authorEmail: str
    # creatorId: int
    # creatorName: str
    # creatorEmail: str

    ##############################################

    def complete(self) -> None:
        self.api.complete_page(self)

    def move(self, *args, **kwargs) -> None:
        self.api.move_page(self, *args, **kwargs)

####################################################################################################

def xpath(data: dict, path: str) -> dict:
    d = data
    for _ in path.split('/'):
        d = d[_]
    return d

####################################################################################################

# json_query = '{"operationName":null, "variables":{}, "query":"{pages {list(orderBy: TITLE) {id path title}}}"}'
# r = requests.post(API_URL, data=json_query, headers=HEADERS)
# print(r.content)

####################################################################################################

class WikiJsApi:

    ##############################################

    def __init__(self, api_url: str, api_key: str) -> None:
        self._api_url = str(api_url)
        self._api_key = str(api_key)
        self._headers = {
            'Authorization': f'Bearer {api_key}',
            # 'content-type': 'application/json',
        }

    ##############################################

    def query_wikijs(self, query: dict) -> dict:
        # print(f"API {query}")
        response = requests.post(self._api_url, json=query, headers=self._headers)
        if response.status_code != requests.codes.ok:
            raise NameError(f"Error {response}")
        data = response.json()
        if 'errors' in data:
            pprint(data)
            raise NameError
        else:
            return data

    ##############################################

    def page(self, path: str, locale: str='fr') -> Page:
        query = {
            'variables': {
                'path': path,
                'locale': locale,
            },
            'query': """
query ($path: String!, $locale: String!)
  {pages {singleByPath(path: $path, locale: $locale) {id path title locale}}}
""",
        }
        data = self.query_wikijs(query)
        _ = xpath(data, 'data/pages/singleByPath')
        return Page(api=self, **_)

    ##############################################

    def yield_pages(self) -> Iterator[Page]:
        # Query > PageQuery > PageListItem
        # TITLE
        query = {'query': '{pages {list(orderBy: PATH) {id path title locale}}}'}
        data = self.query_wikijs(query)
        # {'data': {'pages': {'list': [{'id': 51,
        #                               'path': 'Vera/a-apporter',
        #                               'title': 'À apporter'},
        for _ in xpath(data, 'data/pages/list'):
            yield Page(api=self, **_)

    ##############################################

    def complete_page(self, page: Page) -> None:
        query = {
            'variables': {
                'id': page.id,
            },
            'query': 'query ($id: Int!) {pages {single(id: $id) {content}}}',
        }
        data = self.query_wikijs(query)
        # pprint(data)
        # {'data': {'pages': {'single': {'content':
        page.content = xpath(data, 'data/pages/single/content')

    ##############################################

    def move_page(self, page: Page, path: str, locale: str='fr') -> None:
        query = {
            'variables': {
                'id': page.id,
                'destinationPath': path,
                'destinationLocale': locale,
            },
            # __typename
            'query': """
mutation ($id: Int!, $destinationPath: String!, $destinationLocale: String!) {
  pages {
    move(id: $id, destinationPath: $destinationPath, destinationLocale: $destinationLocale) {
      responseResult {
        succeeded
        errorCode
        slug
        message
      }
    }
  }
}
""",
        }
        print(query)
        data = self.query_wikijs(query)
        pprint(data)
        # {'data': {'pages': {'__typename': 'PageMutation',
        # 'move': {'__typename': 'DefaultResponse',
        # 'responseResult': {'__typename': 'ResponseStatus',
        # 'errorCode': 0,
        # 'message': 'Page has been '
        # 'moved.',
        # 'slug': 'ok',
        # 'succeeded': True}}}}}
