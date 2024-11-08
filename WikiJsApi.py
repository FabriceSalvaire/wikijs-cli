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
    locale: str
    title: str
    description: str
    contentType: str
    isPublished: bool
    isPrivate: bool
    privateNS: str
    createdAt: str
    updatedAt: str
    tags: list[str]

    content: str = None

    # hash: str
    # publishStartDate: Date
    # publishEndDate: Date
    # render: str
    # toc: str
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

    def update(self, *args, **kwargs) -> None:
        self.api.update_page(self, *args, **kwargs)

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

# "query ($query: String!) {\n pages {\n searchTags(query: $query)\n __typename\n }\n}\n"

# "query ($path: String, $locale: String!) {\n pages {\n tree(path: $path, mode: ALL, locale: $locale, includeAncestors: true) {\n id\n path\n title\n isFolder\n pageId\n parent\n locale\n __typename\n }\n __typename\n }\n}\n"

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
  {pages {singleByPath(path: $path, locale: $locale) {
    id
    path
    locale
    title
    description
    contentType
    isPublished
    isPrivate
    privateNS
    createdAt
    updatedAt
    tags {
      tag
    }
  }}}
""",
        }
        data = self.query_wikijs(query)
        _ = xpath(data, 'data/pages/singleByPath')
        _['tags'] = [_['tag'] for _ in _['tags']]
        pprint(_)
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
        pprint(query)
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

    ##############################################

    def update_page(self, page: Page, content: str) -> None:
        # "variables":{"id":96,"checkoutDate":"2024-11-07T02:04:57.106Z"}
        # "query ($id: Int!, $checkoutDate: Date!) {\n  pages {\n    checkConflicts(id: $id, checkoutDate: $checkoutDate)\n    __typename\n  }\n}\n"}]'
        query = {
            'variables': {
                'id': page.id,
                'content': content,
                'description': '',
                'editor': 'markdown',
                'locale': page.locale,
                'isPrivate': False,
                'isPublished': True,
                'path': page.path,
                'publishEndDate': '',
                'publishStartDate': '',
                'scriptCss': '',
                'scriptJs': '',
                'tags': page.tags,
                'title': page.title,
            },
            "query": """
 mutation ($id: Int!, $content: String, $description: String, $editor: String, $isPrivate: Boolean, $isPublished: Boolean, $locale: String, $path: String, $publishEndDate: Date, $publishStartDate: Date, $scriptCss: String, $scriptJs: String, $tags: [String], $title: String) {
  pages {
    update(id: $id, content: $content, description: $description, editor: $editor, isPrivate: $isPrivate, isPublished: $isPublished, locale: $locale, path: $path, publishEndDate: $publishEndDate, publishStartDate: $publishStartDate, scriptCss: $scriptCss, scriptJs: $scriptJs, tags: $tags, title: $title) {
      responseResult {
        succeeded
        errorCode
        slug
        message
      }
      page {
        updatedAt
      }
    }
  }
}
""",
        }
        pprint(query)
        data = self.query_wikijs(query)
        pprint(data)
        # {'data': {'pages': {'update': {'page': {'updatedAt': '2024-11-08T02:20:13.890Z'},
        # 'responseResult': {'errorCode': 0,
        # 'message': 'Page has been '
        # 'updated.',
        # 'slug': 'ok',
        # 'succeeded': True}}}}}
