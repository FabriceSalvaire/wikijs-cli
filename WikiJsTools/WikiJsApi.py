####################################################################################################

from dataclasses import dataclass
from datetime import datetime
from typing import Iterator
from pathlib import Path
from pprint import pprint
import os

import requests

####################################################################################################

# GraphQL
#  !
#    By default, all value types in GraphQL can result in a null value.
#    If a value type includes an exclamation point, it means that value cannot be null.

####################################################################################################

class BasePage:

    ##############################################

    def file_path(self, dst: Path | str, path: str = None) -> Path:
        if path is None:
            path = self.path
        match self.contentType:
            case 'markdown':
                extension = '.md'
            case _:
                extension = '.txt'
        _ = path.split('/')
        _[-1] += extension
        return Path(dst).joinpath(self.locale, *_)

    ##############################################

    def write(self, dst: Path, check_exists: bool = True) -> Path:
        file_path = self.file_path(dst)

        if check_exists:
            # Check updatedAt
            file_date = None
            if file_path.exists():
                with open(file_path, 'r') as fh:
                    for line in fh:
                        if line.startswith('updatedAt'):
                            i = line.find(':')
                            _ = line[i+1:].strip()
                            file_date = datetime.fromisoformat(_)
                            break
            if file_date is not None:
                # print(f'{self.path} | {old_date} vs {new_date}')
                if file_date == self.updated_at:
                    return

        data = ''
        rule = '-'*50
        # data += rule + os.linesep
        for field in (
                'title',
                'locale',
                'path',
                'description',
                'tags',
                'createdAt',
                'updatedAt',

                'id',
                'versionId'
                'isPublished',
                'isPrivate',
                'privateNS',
                'contentType',
        ):
            try:
                _ = getattr(self, field)
                data += f'{field}: {_}' + os.linesep
            except AttributeError:
                # for example updatedAt
                pass
        data += rule + os.linesep
        data += self.content
        # print(f'{file_path}')
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as fh:
            fh.write(data)
        return file_path

####################################################################################################

@dataclass
class Page(BasePage):
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
        # if 'content' not in self.__dict__:
        self.api.complete_page(self)

    @property
    def history(self) -> list['PageHistory']:
        # order is newer first
        if '_history' not in self.__dict__:
            self._history = self.api.page_history(self)
            # self._history_map = {_.versionId: _ for _ in self._history}
        return self._history

    ##############################################

    @property
    def updated_at(self) -> datetime:
        return datetime.fromisoformat(self.updatedAt)

    @property
    def version_id(self) -> int:
        return self.history[-1].versionId

    ##############################################

    def update(self, *args, **kwargs) -> None:
        self.api.update_page(self, *args, **kwargs)

    def move(self, *args, **kwargs) -> None:
        self.api.move_page(self, *args, **kwargs)

####################################################################################################

@dataclass
class PageVersion(BasePage):
    api: 'WikiJsApi'
    page: Page

    # Page
    pageId: int
    path: str
    locale: str
    title: str
    description: str
    contentType: str
    isPublished: bool
    isPrivate: bool
    createdAt: str
    tags: list[str]
    content: str
    publishEndDate: str
    publishStartDate: str
    editor: str

    # Version
    versionId: int
    versionDate: str
    action: str
    authorId: str
    authorName: str

    ##############################################

    @property
    def prev(self) -> 'PageVersion':
        print(f"prev for {self.versionId}")
        for i, _ in enumerate(self.page.history):
            # print(f"{i} {_}")
            if _.versionId == self.versionId:
                break
        try:
            _ = self.page.history[i+1]
            # print(f"{i+1} {_}")
            # print(f"{_.versionId} -> {self.versionId}")
            return _.page_version
        except IndexError:
            return None

    # @property
    # def old_path(self) -> str:
    #     return self.prev.path

####################################################################################################

@dataclass
class PageHistory:
    api: 'WikiJsApi'
    page: Page

    versionId: int
    versionDate: str
    authorId: int
    authorName: str
    actionType: str

    valueBefore: str
    valueAfter: str

    ##############################################

    @property
    def page_version(self) -> None:
        if '_page_version' not in self.__dict__:
            self._page_version = self.api.page_version(self)
        return self._page_version

    @property
    def date(self) -> datetime:
        return datetime.fromisoformat(self.versionDate)

    @property
    def changed(self) -> bool:
        return self.valueAfter != self.valueBefore

    @property
    def old_path(self) -> str:
        return self.valueBefore

    @property
    def new_path(self) -> str:
        return self.valueAfter

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
        self.info()

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

    def info(self) -> None:
        query = {
            'query': """
{system
  {info {
    currentVersion
    latestVersion
    groupsTotal
    pagesTotal
    usersTotal
    tagsTotal
}}}
""",
        }
        data = self.query_wikijs(query)
        _ = xpath(data, 'data/system/info')
        # pprint(data)
        self._number_of_pages = _['pagesTotal']

    ##############################################

    def page(self, path: str, locale: str = 'fr') -> Page:
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
        query = {
            'query': '''
{pages {
  list(orderBy: PATH) {
    id
    path
    title
    locale
    description
    contentType
    isPublished
    isPrivate
    privateNS
    createdAt
    updatedAt
    tags
}}}''',
        }
        data = self.query_wikijs(query)
        # {'data': {'pages': {'list': [{'id': 51,
        #                               'path': 'Vera/a-apporter',
        #                               'title': 'À apporter'},
        for _ in xpath(data, 'data/pages/list'):
            yield Page(api=self, **_)

    ##############################################

    def yield_tree(self, path: str) -> Iterator[Page]:
        # Query > PageQuery > PageTreeItem
        # TITLE
        query = {
            'variables': {
                'path': path,
                # 'parent': 3,
                'locale': 'fr'
            },
# query ($parent: Int, $locale: String!)
# {pages {
#   tree(parent: $parent, mode: ALL, locale: $locale) {
# PAGES
            'query': '''
query ($path: String!, $locale: String!)
{pages {
  tree(path: $path, mode: ALL, locale: $locale, includeAncestors: false) {
    id
    path
    depth
    title
    isPrivate
    isFolder
    privateNS
    parent
    pageId
    locale
}}}
''',
        }
        data = self.query_wikijs(query)
        pprint(data)
        # for _ in xpath(data, 'data/pages/list'):
        #     yield Page(api=self, **_)

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

    def page_history(self, page: Page) -> None:
        query = {
            'variables': {
                'id': page.id,
            },
            'query': '''
query ($id: Int!)
{pages {
  history(id: $id) {
    trail {
    versionId
    versionDate
    authorId
    authorName
    actionType
    valueBefore
    valueAfter
    }
    total
}}}''',
        }
        data = self.query_wikijs(query)
        history = xpath(data, 'data/pages/history/trail')
        # _ = xpath(data, 'data/pages/history/total')
        return [PageHistory(api=self, page=page, **_) for _ in history]

    ##############################################

    def page_version(self, page_history: PageHistory) -> None:
        query = {
            'variables': {
                'id': page_history.page.id,
                'version_id': page_history.versionId,
            },
            'query': '''
query ($id: Int!, $version_id: Int!)
{pages {
  version(pageId: $id, versionId: $version_id) {
  action
  authorId
  authorName
  content
  contentType
  createdAt
  versionDate
  description
  editor
  isPrivate
  isPublished
  locale
  pageId
  path
  publishEndDate
  publishStartDate
  tags
  title
  versionId
}}}''',
        }
        data = self.query_wikijs(query)
        _ = xpath(data, 'data/pages/version')
        return PageVersion(api=self, page=page_history.page, **_)

    ##############################################

    def move_page(self, page: Page, path: str, locale: str = 'fr') -> None:
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

    ##############################################

    def history(self) -> list[PageHistory]:
        # , progress_callback
        history = [_ for page in self.yield_pages() for _ in page.history]
        # history = []
        # for page in self.yield_pages():
        #     print(f'{page.path}')
        #     for _ in page.history:
        #         history.append(_)
        history.sort(key=lambda _: _.date)
        # for _ in history:
        #     print(f'{_.versionId} {_.date} {_.page.id} {_.page.path} {_.actionType}')
        return history
