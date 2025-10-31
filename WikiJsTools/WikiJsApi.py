####################################################################################################
#
# wikijs-cli - A CLI for Wiki.js
# Copyright (C) 2025 Fabrice SALVAIRE
# SPDX-License-Identifier: GPL-3.0-or-later
#
####################################################################################################

__all__ = ['ApiError', 'WikiJsApi', 'Node', 'Page']

# Fime: use PurePosixPath

####################################################################################################

from dataclasses import dataclass
from datetime import datetime
from typing import Iterator
from pathlib import Path, PurePosixPath
from pprint import pprint
import os

import requests

from . import query as Q
from .unicode import usorted

####################################################################################################

# GraphQL
#  !
#    By default, all value types in GraphQL can result in a null value.
#    If a value type includes an exclamation point, it means that value cannot be null.

####################################################################################################

class Node:

    ##############################################

    def __init__(self, name: str = '') -> None:
        self._name = str(name)
        self._parent = None
        self._childs = {}

    ##############################################

    def __str__(self) -> str:
        return self._name

    @property
    def name(self) -> str:
        return self._name

    @property
    def path(self) -> PurePosixPath:
        if self.is_root:
            return PurePosixPath('/')
        elif self.parent.is_root:
            return PurePosixPath('/', self._name)
        else:
            return self.parent.path.joinpath(self._name)

    @property
    def is_root(self) -> bool:
        return self._parent is None

    @property
    def is_folder(self) -> bool:
        return self._childs

    @property
    def is_leaf(self) -> bool:
        return not self._childs

    @property
    def parent(self) -> 'Node':
        return self._parent

    @parent.setter
    def parent(self, node: 'Node') -> None:
        self._parent = node

    @property
    def childs(self) -> Iterator['Node']:
        childs = list(self._childs.values())
        # childs.sort(key=lambda _: _._name)
        childs = usorted(childs, 'name')
        return iter(childs)

    @property
    def folder_childs(self) -> Iterator['Node']:
        for _ in self.childs:
            if _.is_folder:
                yield _

    @property
    def leaf_childs(self) -> Iterator['Node']:
        for _ in self.childs:
            if _.is_leaf:
                yield _

    @property
    def child_names(self) -> list[str]:
        return usorted(self._childs.keys())

    @property
    def folder_names(self) -> list[str]:
        return [_.name for _ in self.folder_childs]

    @property
    def leaf_names(self) -> list[str]:
        return [_.name for _ in self.leaf_childs]

    ##############################################

    def add_child(self, child: 'Node') -> None:
        if child.name not in self._childs:
            self._childs[child.name] = child
            child.parent = self

    ##############################################

    def __getitem__(self, name: str) -> 'Node':
        return self._childs[name]

    def __contains__(self, name: str) -> bool:
        return name in self._childs

    ##############################################

    def _find_impl(self, path: list[str]) -> 'Node':
        if path:
            _ = path.pop()
            if _ in self:
                return self[_]._find_impl(path)
        #     else:
        #         return self
        # else:
        return self

    def find(self, path: str) -> 'Node':
        it = reversed(str(path).split('/'))
        path = list(filter(bool, it))
        return self._find_impl(path)

    ##############################################

    def join(self, path: str) -> 'str':
        return f'{self.path}/{path}'

####################################################################################################

@dataclass
class ResponseResult:
    succeeded: bool
    errorCode: int
    slug: str
    message: str

####################################################################################################

@dataclass
class Tag:
    id: int
    tag: str
    title: str
    createdAt: str
    updatedAt: str

####################################################################################################

@dataclass
class PageTreeItem:
    api: 'WikiJsApi'

    id: int
    path: str
    depth: int
    title: str
    isPrivate: bool
    isFolder: bool
    privateNS: str
    parent: int
    pageId: int
    locale: str

####################################################################################################

class BasePage:

    RULE = '-'*50

    @property
    def split_path(self) -> list[str]:
        return str(self.path).split('/')

    @property
    def path_str(self) -> str:
        return str(self.path)

    ##############################################

    @property
    def url(self) -> str:
        return f'{self.api.api_url}/{self.locale}/{self.path}'

    ##############################################

    @staticmethod
    def extension_for(content_type: str = 'markdown'):
        match content_type:
            case 'markdown':
                return '.md'
            case _:
                return '.txt'

    ##############################################

    @classmethod
    def file_path_impl(
            cls,
            dst: Path | str,
            locale: str,
            path: str = None,
            content_type: str = 'markdown',
    ) -> Path:
        _ = str(path).split('/')
        _[-1] += cls.extension_for(content_type)
        return Path(dst).joinpath(locale, *_)

    ##############################################

    def file_path(self, dst: Path | str, path: str = None) -> Path:
        # Note: path is used to move page version
        if path is None:
            path = self.path
        return self.file_path_impl(dst, self.locale, path, self.contentType)

    ##############################################

    def add_extension(self, dst: str) -> Path:
        extension = self.extension_for(self.contentType)
        if not dst.endswith(extension):
            dst += extension
        return Path(dst)

    ##############################################

    @classmethod
    def template(
            cls,
            dst: Path | str,
            locale: str,
            path: str = None,
            content_type: str = 'markdown',
            check_exists: bool = True,
    ) -> Path:
        dst = Path(dst)
        if check_exists and dst.exists():
            return

        data = ''
        # data += cls.RULE + os.linesep
        for field, value in dict(
                title='',
                locale=locale,
                path=path,
                description='',
                tags=[],
                # createdAt='',
                # updatedAt='',

                isPublished=True,
                isPrivate=False,
                privateNS=None,
                contentType=content_type,
        ).items():
            data += f'{field}: {value}' + os.linesep
        data += cls.RULE + os.linesep
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(data, encoding='utf8')
        return dst

    ##############################################

    def sync(self, dst: Path | str, check_exists: bool = True) -> Path:
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
        self.write(file_path)
        return file_path

    ##############################################

    def export(self) -> str:
        data = ''
        # data += self.RULE + os.linesep
        for field in (
                'title',
                'locale',
                'path',
                'description',
                'tags',
                'createdAt',
                'updatedAt',

                'id', 'pageId',
                'versionId',
                'versionDate',
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
        data += self.RULE + os.linesep
        data += self.content.rstrip()
        return data

    ##############################################

    def write(self, dst: Path | str) -> Path:
        path = Path(dst)
        data = self.export()
        path.parent.mkdir(parents=True, exist_ok=True)
        # if not path.exists():
        path.write_text(data, encoding='utf8')
        return path

    ##############################################

    @classmethod
    def read(self, input: Path | str, api: 'WikiJsApi') -> 'Page':
        input = Path(input)
        data = dict(id=None, createdAt=None, updatedAt=None)
        with open(input, 'r', encoding='utf8') as fh:
            content = None
            for line in fh.readlines():
                if content is None:
                    line = line.strip()
                    if line == self.RULE:
                        content = ''
                    else:
                        index = line.find(":")
                        key = line[:index].strip()
                        value = line[index+1:].strip()
                        if key == 'id' and value:
                            value = int(value)
                        data[key] = value
                else:
                    content += line
            data['content'] = content
        data['tags'] = [_.strip() for _ in data['tags'][1:-1].split(',') if _.strip()]
        for _ in ('isPublished', 'isPrivate'):
            data[_] = True if data[_] == 'True' else False
        pprint(data)
        return Page(api, **data)

####################################################################################################

@dataclass
class Page(BasePage):
    api: 'WikiJsApi'

    id: int
    path: PurePosixPath
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

    def __post_init__(self):
        self.path = PurePosixPath(self.path)

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
        if self.updatedAt:
            return datetime.fromisoformat(self.updatedAt)
        else:
            return None

    @property
    def version_id(self) -> int:
        return self.history[-1].versionId

    ##############################################

    def update(self, *args, **kwargs) -> 'ResponseResult':
        return self.api.update_page(self, *args, **kwargs)

    def move(self, *args, **kwargs) -> 'ResponseResult':
        return self.api.move_page(self, *args, **kwargs)

    ##############################################

    def reload(self) -> 'Page':
        return self.api.page(self.path, self.locale)

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
    def page_version(self) -> PageVersion:
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

@dataclass
class PageLinkItem:
    id: int
    path: str
    title: str
    links: list[str]

####################################################################################################

@dataclass
class PageSearchResult:
    id: str
    title: str
    description: str
    path: str
    locale: str

@dataclass
class PageSearchResponse:
    results: list[PageSearchResult]
    suggestions: list[str]
    totalHits: int

####################################################################################################

@dataclass
class AssetFolder:
    api: 'WikiJsApi'

    id: int
    name: str
    slug: str

    path: str = None

    # parent: 'AssetFolder'

    ##############################################

    def list(self) -> Iterator['Asset']:
        yield from self.api.list_asset(self.id)

    ##############################################

    def upload(self, path: Path | str, name: str = None) -> None:
        self.api.upload(self.id, path, name)

####################################################################################################

@dataclass
class Asset:
    id: int
    filename: str
    ext: str
    kind: str
    mime: str
    fileSize: int
    metadata: str
    createdAt: str
    updatedAt: str

    path: str = None

    ##############################################

    @property
    def created_at(self) -> datetime:
        return datetime.fromisoformat(self.createdAt)

    @property
    def updated_at(self) -> datetime:
        return datetime.fromisoformat(self.updatedAt)

####################################################################################################

def xpath(data: dict, path: str) -> dict:
    d = data
    for _ in str(path).split('/'):
        d = d[_]
    return d

####################################################################################################

class ApiError(NameError):
    pass

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

    @property
    def api_url(self) -> str:
        return self._api_url

    ##############################################

    def is_valid_path(self, path: str) -> bool:
        # Space (use dashes instead)
        # Period (reserved for file extensions)
        # Unsafe URL characters (such as punctuation marks, quotes, math symbols, etc.)
        for c in path:
            if c in ' .,;!?&|+=*^~#%$@{}[]<>\\\'"':
                return False
        return True

    ##############################################

    def query_wikijs(self, query: dict) -> dict:
        # print(f"API {query}")
        response = requests.post(f'{self._api_url}/graphql', json=query, headers=self._headers)
        if response.status_code != requests.codes.ok:
            raise NameError(f"Error {response}")
        data = response.json()
        if 'errors' in data:
            # pprint(data)
            raise ApiError(data['errors'][0]['message'])
        else:
            return data

    ##############################################

    def upload(self, folder_id: int, path: Path | str, name: str = None) -> None:
        path = Path(path).expanduser().resolve()
        if name is None:
            name = path.name
        payload = path.read_bytes()
        multipart_form_data = (
            ('mediaUpload', (None, '{"folderId":' + str(folder_id) + '}')),
            ('mediaUpload', (name, payload, 'image/png')),
        )
        # _ = requests.Request('POST', f'{self._api_url}/u', files=multipart_form_data)
        # print(_.prepare().body[:100])
        response = requests.post(f'{self._api_url}/u', files=multipart_form_data, headers=self._headers)
        if response.status_code != requests.codes.ok:
            raise NameError(f"Error {response}")
        # pprint(response)

    ##############################################

    def get(self, url: str) -> bytes:
        url = f'{self._api_url}/{url}'
        response = requests.get(url, headers=self._headers)
        if response.status_code != requests.codes.ok:
            raise NameError(f"Error {response}")
        return response.content

    ##############################################

    def info(self) -> None:
        query = {
            'query': Q.INFO,
        }
        data = self.query_wikijs(query)
        _ = xpath(data, 'data/system/info')
        # pprint(data)
        self._number_of_pages = _['pagesTotal']

    ##############################################

    @property
    def number_of_pages(self) -> int:
        return self._number_of_pages

    ##############################################

    def page(self, path: str, locale: str = 'fr') -> Page:
        path = str(path)
        # remove / from cd
        if path.startswith('/'):
            path = path[1:]
        query = {
            'variables': {
                'path': path,
                'locale': locale,
            },
            'query': Q.PAGE,
        }
        data = self.query_wikijs(query)
        _ = xpath(data, 'data/pages/singleByPath')
        _['tags'] = [_['tag'] for _ in _['tags']]
        # pprint(_)
        return Page(api=self, **_)

    ##############################################

    def list_pages(self, order_by: str = 'PATH', reverse: bool = False, limit: int = 0) -> Iterator[Page]:
        order_by_direction = 'DESC' if reverse else 'ASC'
        # Fixme: cannot pass PageOrderBy as string ???
        query = {
            'variables': {
                'limit': limit,
                # 'order_By': order_by,
                # 'orderByDirection': order_by_direction,
            },
            # eval(f'f"""{Q.LIST_PAGE}"""')
            'query': Q.LIST_PAGE(order_by, order_by_direction),
        }
        # pprint(query)
        data = self.query_wikijs(query)
        for _ in xpath(data, 'data/pages/list'):
            yield Page(api=self, **_)

    ##############################################

    def list_page_for_tags(self, tags: list[str], order_by: str = 'PATH', limit: int = 0) -> Iterator[Page]:
        query = {
            'variables': {
                'tags': list(tags),
                'limit': limit,
            },
            'query': Q.LIST_PAGE_FOR_TAGS(order_by),
        }
        data = self.query_wikijs(query)
        for _ in xpath(data, 'data/pages/list'):
            yield Page(api=self, **_)

    ##############################################

    def tree(self, path: str = 'home') -> Iterator[Page]:
        """List the pages and folders in the parent of the page at `path`.
        When `includeAncestors` is True, the parent directories are also listed.
        """
        query = {
            'variables': {
                'path': path,
                # 'parent': 3,
                'locale': 'fr'
            },
            # parent: Int
            'query': Q.TREE,
        }
        data = self.query_wikijs(query)
        for _ in xpath(data, 'data/pages/tree'):
            yield PageTreeItem(api=self, **_)

    ##############################################

    def build_page_tree(self, progress_bar_cls) -> Node:
        root = Node()

        def process_page(page: Page) -> None:
            # print('-'*10)
            # print(page.path)
            path = page.split_path
            prev = root
            for _ in path:
                try:
                    node = prev[_]
                except KeyError:
                    node = Node(_)
                    prev.add_child(node)
                # print(f'{prev} // {node}')
                prev = node
            prev.page = page

        pages = self.list_pages()
        if progress_bar_cls is not None:
            with progress_bar_cls() as pb:
                for page in pb(pages, total=self._number_of_pages):
                    process_page(page)
        else:
            for page in pages:
                process_page(page)

        return root

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
        page.content = xpath(data, 'data/pages/single/content')

    ##############################################

    def page_history(self, page: Page) -> None:
        query = {
            'variables': {
                'id': page.id,
            },
            'query': Q.PAGE_HISTORY,
        }
        data = self.query_wikijs(query)
        history = xpath(data, 'data/pages/history/trail')
        # _ = xpath(data, 'data/pages/history/total')
        return [PageHistory(api=self, page=page, **_) for _ in history]

    ##############################################

    def list_asset_subfolder(self, folder_id: int = 0) -> Iterator[AssetFolder]:
        query = {
            'variables': {
                'parentFolderId': folder_id,
            },
            'query': Q.LIST_ASSET_SUBFOLDER,
        }
        data = self.query_wikijs(query)
        for _ in xpath(data, 'data/assets/folders'):
            yield AssetFolder(self, **_)

    ##############################################

    def build_asset_tree(self) -> Node:
        # We cannot implement a progress bar since we don't know the number of nodes.
        # A workaround would be to save the number of nodes in a config file.
        # And to use it for the next run.

        root = Node()

        def process_folder(parent: Node, folder_id: int) -> None:
            for _ in self.list_asset_subfolder(folder_id):
                node = Node(_.name)
                parent.add_child(node)
                process_folder(node, _.id)

        process_folder(root, 0)
        return root

    ##############################################

    def list_asset(self, folder_id: int) -> Iterator[Asset]:
        query = {
            'variables': {
                'folderId': folder_id,
                'kind': 'ALL',
            },
            'query': Q.LIST_ASSET,
            # folder: AssetFolder
            # author: Author
        }
        data = self.query_wikijs(query)
        for _ in xpath(data, 'data/assets/list'):
            yield Asset(**_)

    ##############################################

    def page_version(self, page_history: PageHistory) -> None:
        query = {
            'variables': {
                'id': page_history.page.id,
                'version_id': page_history.versionId,
            },
            'query': Q.PAGE_VERSION,
        }
        data = self.query_wikijs(query)
        _ = xpath(data, 'data/pages/version')
        return PageVersion(api=self, page=page_history.page, **_)

    ##############################################

    def move_page(self, page: Page, path: str, locale: str = 'fr') -> ResponseResult:
        query = {
            'variables': {
                'id': page.id,
                'destinationPath': str(path),
                'destinationLocale': locale,
            },
            'query': Q.MOVE_PAGE,
        }
        # pprint(query)
        data = self.query_wikijs(query)
        # pprint(data)
        _ = xpath(data, 'data/pages/move/responseResult')
        return ResponseResult(**_)

    ##############################################

    def create_page(self, page: Page) -> ResponseResult:
        variables = {_: getattr(page, _) for _ in (
            'content',
            'description',
            'isPublished',
            'isPrivate',
            'locale',
            # 'path',
            'tags',
            'title',
        )}
        variables['path'] = page.path_str
        variables.update({
            'editor': page.contentType,
            'publishEndDate': '',
            'publishStartDate': '',
            'scriptCss': '',
            'scriptJs': '',
        })
        query = {
            'variables': variables,
            "query": Q.CREATE_PAGE,
        }
        # pprint(query)
        data = self.query_wikijs(query)
        # pprint(data)
        _ = xpath(data, 'data/pages/create/responseResult')
        return ResponseResult(**_)

    ##############################################

    def update_page(self, page: Page) -> ResponseResult:
        # Fixme: checkConflicts
        # "variables":{"id":96,"checkoutDate":"2024-11-07T02:04:57.106Z"}
        # "query ($id: Int!, $checkoutDate: Date!) { pages {
        #   checkConflicts(id: $id, checkoutDate: $checkoutDate) }}"}]'
        query = {
            'variables': {
                'id': page.id,
                'content': page.content,
                'description': '',
                'editor': 'markdown',
                'isPrivate': False,
                'isPublished': True,
                'locale': page.locale,
                'path': page.path_str,
                'publishEndDate': '',
                'publishStartDate': '',
                'scriptCss': '',
                'scriptJs': '',
                'tags': page.tags,
                'title': page.title,
            },
            "query": Q.UPDATE_PAGE,
        }
        # pprint(query)
        data = self.query_wikijs(query)
        # pprint(data)
        _ = xpath(data, 'data/pages/update/responseResult')
        return ResponseResult(**_)

    ##############################################

    def history(self, progress_callback, preload_version: bool = True) -> list[PageHistory]:
        # history = [_ for page in self.list_pages() for _ in page.history]
        history = []
        P_STEP = 10
        next_p = P_STEP
        for i, page in enumerate(self.list_pages()):
            p = 100 * i / self._number_of_pages
            if p > next_p:
                progress_callback(int(p))
                next_p += P_STEP
            print(f'{page.path}')
            for _ in page.history:
                if preload_version:
                    _.page_version
                history.append(_)
        history.sort(key=lambda _: _.date)
        # for _ in history:
        #     print(f'{_.versionId} {_.date} {_.page.id} {_.page.path} {_.actionType}')
        return history

    ##############################################

    def search(self, query: str) -> PageSearchResponse:
        query = {
            'variables': {
                'query': query,
            },
            'query': Q.SEARCH,
        }
        data = self.query_wikijs(query)
        results = [PageSearchResult(**_) for _ in xpath(data, 'data/pages/search/results')]
        _ = {
            key: value
            for key, value in xpath(data, 'data/pages/search').items()
            if key != 'results'
        }
        return PageSearchResponse(
            results=results,
            **_,
        )

    ##############################################

    def tags(self) -> Iterator[Tag]:
        query = {
            'query': Q.TAGS,
        }
        data = self.query_wikijs(query)
        for _ in xpath(data, 'data/pages/tags'):
            yield Tag(**_)

    ##############################################

    def search_tags(self, query: str) -> list[str]:
        query = {
            'variables': {
                'query': query,
            },
            'query': Q.SEARCH_TAGS,
        }
        data = self.query_wikijs(query)
        return xpath(data, 'data/pages/searchTags')

    ##############################################

    def links(self) -> Iterator[PageLinkItem]:
        query = {
            'variables': {
                'locale': 'fr',
            },
            'query': Q.LINKS,
        }
        data = self.query_wikijs(query)
        # pprint(data)
        for _ in xpath(data, 'data/pages/links'):
            link = PageLinkItem(**_)
            if link.links:
                yield link
