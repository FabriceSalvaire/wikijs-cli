###################################################################################################

__all__ = ['Cli']

####################################################################################################

from datetime import datetime
from pprint import pprint
import json
# import logging
import os
import re
import subprocess
import traceback

from pathlib import Path

# See also [cmd — Support for line-oriented command interpreters — Python documentation](https://docs.python.org/3/library/cmd.html)
# Python Prompt Toolkit](https://python-prompt-toolkit.readthedocs.io/en/master/)
from prompt_toolkit import PromptSession, HTML
from prompt_toolkit import print_formatted_text, shortcuts
from prompt_toolkit.completion import WordCompleter
# from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style

from .WikiJsApi import Page, WikiJsApi, AssetFolder

####################################################################################################

# _module_logger = logging.getLogger('')

LINESEP = os.linesep

####################################################################################################

class Cli:

    CLI_HISTORY = Path('cli_history')
    GIT = '/usr/bin/git'
    GIT_SYNC = 'git_sync'
    HISTORY_JSON = 'history.json'

    STYLE = Style.from_dict({
        # User input (default text)
        # '': '#000000',
        '': '#ffffff',
        # Prompt
        'prompt': '#ff0000',
        # Output
        # 'red': '#ff0000',
        # 'green': '#00ff00',
        # 'blue': '#0000ff',
        'red': '#ed1414',
        'green': '#10cf15',
        'blue': '#1b99f3',
        'orange': '#f57300',
        'violet': '#9b58b5',
        'greenblue': '#19bb9c',
    })

    ##############################################

    def __init__(self, api: WikiJsApi) -> None:
        self._api = api
        self.COMMANDS = [
            _
            for _ in dir(self)
            if not (_.startswith('_') or _[0].isupper() or _ in ('cli', 'run'))
        ]
        self.COMMANDS.sort()
        self.COMPLETER = WordCompleter(self.COMMANDS)
        self._asset_folders = None
        self._asset_folder = None

    ##############################################

    @staticmethod
    def to_bool(value: str) -> bool:
        if isinstance(value, bool):
            return value
        match str(value).lower():
            case 'true' | 't':
                return True
            case _:
                return False

    ##############################################

    def _run_line(self, query: str) -> bool:
        # try:
        command, *argument = query.split()
        # except ValueError:
        #     if query.strip() == 'quit':
        #         return False
        # print(f"|{command}|{argument}|")
        try:
            if command == 'quit':
                return False
            method = getattr(self, command)
            try:
                method(*argument)
            except Exception as e:
                print(traceback.format_exc())
                print(e)
        except AttributeError:
            self.print(f"<red>Invalid command</red> <blue>{query}</blue>")
            self.usage()
        return True

    ##############################################

    def run(self, query: str) -> bool:
        commands = filter(bool, [_.strip() for _ in query.split(';')])
        for _ in commands:
            if not self._run_line(_):
                return False
        return True

    ##############################################

    def cli(self, query: str) -> None:
        if query:
            if not self.run(query):
                return

        history = FileHistory(self.CLI_HISTORY)
        session = PromptSession(
            completer=self.COMPLETER,
            history=history,
        )
        self.usage()
        while True:
            try:
                message = [
                    ('class:prompt', '> '),
                ]
                query = session.prompt(
                    message,
                    style=self.STYLE,
                )
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            else:
                if query:
                    if not self.run(query):
                        break
                else:
                    self.usage()

    ##############################################

    def print(self, message: str) -> None:
        print_formatted_text(
            HTML(message),
            style=self.STYLE,
        )

    ##############################################

    def clear(self) -> None:
        shortcuts.clear()

    ##############################################

    def usage(self) -> None:
        for _ in (
            "<red>Enter</red>: <blue>command argument</blue>",
            "    or <blue>command1 argument; command2 argument; ...</blue>",
            "<red>Commands are</red>: " + ', '.join([f"<blue>{_}</blue>" for _ in self.COMMANDS]),
            "  <blue>dump</blue> <green>@page_url@ [output]</green>: dump the page",
            "  <blue>list</blue>: list all the pages",
            "  <blue>move</blue> <green>@page_url@ @new_page_url@</green>: move a page",
            "  <blue>update</blue> <green>@page_url@ input</green>: update the page",
            "  <blue>create</blue> <green>input</green>: create a page",
            "  <blue>template</blue> <green>output</green>: create a page template",
            "  <blue>check</blue>: check pages",
            "  <blue>asset</blue>: list all the assets",
            "  <blue>sync</blue>: sync wiki on disk",
            "  <blue>git_sync</blue>: sync wiki on a Git repo",
            "<red>Exit</red> using command <blue>quit</blue> or <blue>Ctrl+d</blue>"
        ):
            self.print(_)

    ##############################################

    def list(self) -> None:
        for page in self._api.list_pages():
            page.complete()
            self.print(f"<green>{page.path:60}</green> <blue>{page.title:40}</blue> {len(page.content):5} @{page.locale} {page.id:3}")

    ##############################################

    def last(self) -> None:
        for page in self._api.list_pages(order_by='UPDATED', reverse=True, limit=10):
            self.print(f"<green>{page.path:60}</green> <blue>{page.title:40}</blue>{LINESEP}  {page.updated_at}   @{page.locale}   {page.id:3}")

    ##############################################

    def tree(self, path: str) -> None:
        pages = list(self._api.tree(path))
        pages.sort(key=lambda _: _.path)
        for page in pages:
            is_folder = '/' if page.isFolder else ''
            path = f"{page.path}{is_folder}"
            self.print(f"<green>{path:60}</green> <blue>{page.title:40}</blue>")

    ##############################################

    def dump(self, path: str, output: str = None) -> None:
        page = self._api.page(path)
        page.complete()
        _ = f"<green>{page.path}</green> @{page.locale}{LINESEP}"
        _ += f"  <blue>{page.title}</blue>{LINESEP}"
        _ += f"  {page.id}{LINESEP}"
        self.print(_)
        if output:
            output = Path(output)
            if not output.parent.exists():
                raise NameError(f"path doesn't exists {output.parent}")
            output.write_text(page.content, encoding='utf8')
        else:
            rule = '\u2500' * 100
            print(rule)
            print(page.content)
            print(rule)

    ##############################################

    def template(self, dst: str, path: str, locale: str = 'fr', content_type: str = 'markdown') -> None:
        if Page.template(dst, locale, path, content_type) is None:
            self.print(f"<red>Error: file exists</red>")

    ##############################################

    def create(self, input: str) -> None:
        page = Page.read(input, self._api)
        response = self._api.create_page(page)
        self.print(f"<red>{response.message}</red>")

    ##############################################

    def update(self, path: str, input: str = None) -> None:
        page = self._api.page(path)
        page.complete()
        _ = f"<green>{page.path}</green> @{page.locale}{LINESEP}"
        _ += f"  <blue>{page.title}</blue>{LINESEP}"
        _ += f"  {page.id}{LINESEP}"
        self.print(_)
        content = input.readtext(encoding='utf8')
        rule = '\u2500' * 100
        print(rule)
        print(page.content)
        print(rule)
        page.update(content)

    ##############################################

    def move(self, old_path: str, new_path: str, dryrun: bool = False) -> None:
        dryrun = self.to_bool(dryrun)
        self.print(f"  Move: <green>{old_path}</green> <red>-></red> <blue>{new_path}</blue>")
        for page in self._api.list_pages():
            # for _ in ('portail',):
            # if page.path.lower().startswith('.../' + _):
            # print(page.path)
            if page.path.startswith(old_path):
                dest = page.path.replace(old_path, new_path)
                self.print(f"  Move page: <green>{page.path}</green> <red>-></red> <blue>{dest}</blue>")
                if not dryrun:
                    response = page.move(dest)
                    self.print(f"<red>{response.message}</red>")

    ##############################################

    def asset(self, show_files: bool = True, show_folder_path: bool = False) -> None:
        show_files = self.to_bool(show_files)
        # Build asset folder tree
        self._asset_folders = {
            '/': AssetFolder(self, id=0, name='', slug='')
        }
        def show_folder(folder_id: int = 0, indent: int = 0, stack: list = []):
            indent_str = '  '*indent
            if show_files:
                for asset in self._api.list_asset(folder_id):
                    self.print(f"{indent_str}- <blue>{asset.filename}</blue>   {asset.updated_at}   <green>{asset.id}</green>")
                    url = '/'.join([self._api.api_url] + stack + [asset.filename])
                    self.print(f"{indent_str}  {url}")
            for _ in self._api.list_asset_subfolder(folder_id):
                path = '/'.join(stack + [_.name])
                _.path = path
                self._asset_folders[path] = _
                # print(f"{indent_str}- {_.name} {_.slug} {_.id}")
                if show_folder_path:
                    self.print(f"<red>{path}</red>    <green>{_.id}</green>")
                else:
                    self.print(f"{indent_str}+ <red>{_.name}</red>    <green>{_.id}</green>")
                show_folder(_.id, indent + 1, stack + [_.name])
        self.print('<blue>/</blue>')
        show_folder()

    ##############################################

    def cd_asset(self, path: str) -> None:
        if self._asset_folders is None:
            self.asset(show_files=False, show_folder_path=True)
        try:
            self._asset_folder = self._asset_folders[path]
            self.print(f"<red>moved to</red> <blue>{path}</blue>")
        except KeyError:
            self.print(f"<red>Error:</red> <blue>{path}</blue> <red>not found</red>")

    ##############################################

    def upload(self, path: Path | str, name: str = None) -> None:
        if self._asset_folder is not None:
            self._asset_folder.upload(path, name)
            assets = list(self._asset_folder.list())
            assets.sort(key=lambda _: _.updated_at, reverse=True)
            self.print(f'<blue>{self._asset_folder.path}</blue>')
            for asset in assets:
                self.print(f'- <blue>{asset.filename}</blue>   {asset.updated_at}')
        else:
            self.print(f"<red>Error: run cd_asset before</red>")

    ##############################################

    def search(self, query: str) -> None:
        response = self._api.search(query)
        self.print(f'Suggestions: <blue>{response.suggestions}</blue>')
        for _ in response.results:
            self.print(f'- <blue>{_.path:60}</blue> <green>{_.title}</green>')

    ##############################################

    def sync(self, path: Path = None) -> None:
        if path is None:
            path = Path('.', 'sync')
        path.mkdir(exist_ok=True)

        # i = 0
        for page in self._api.list_pages():
            page.complete()
            file_path = page.sync(path)
            if file_path is not None:
                print(f"Wrote {file_path}")
            # i += 1
            # if i > 3:
            #    break

    ##############################################

    def git_sync(self, path: Path = None) -> None:
        # Protection
        if Path.cwd().joinpath('.git').exists():
            print(f"Current path is a git repo. Exit")
            return

        if path is None:
            sync_dir = Path('.', self.GIT_SYNC).resolve()
        else:
            sync_dir = Path(path)
        print(f"Git path {sync_dir}")

        created = False
        if sync_dir.exists():
            print("Git already initialised")
        else:
            sync_dir.mkdir()
            created = True
        os.chdir(sync_dir)
        json_versions = []
        last_version_date = None
        if created:
            subprocess.check_call((self.GIT, 'init'))
        else:
            with open(self.HISTORY_JSON, 'r') as fh:
                json_versions = json.load(fh)
                last_version = json_versions[-1]
                # How versionID are generated ???
                # last_version_id = last_version['versionId']
                last_version_date = datetime.fromisoformat(last_version['versionDate'])
            print(f"Last version date {last_version_date}")

        def commit(version, message: str) -> None:
            subprocess.check_call((
                self.GIT,
                'commit',
                '-m', message,
                f'--date={version.versionDate}',
            ))

        # Fixme: progress callback
        #  how to get number of versions ?
        def progress_callback(p: int) -> None:
            print(f"{p} % done")

        # Fixme: skip ?
        history = self._api.history(progress_callback)

        for page_history in history:
            if last_version_date is not None:
                _ = datetime.fromisoformat(page_history.versionDate)
                if _ <= last_version_date:
                    continue

            version = page_history.page_version
            if 'content' in version.path:
                pprint(page_history)
                pprint(version)
            # /!\ In some case page_history.actionType = initial and version.action = moved
            match page_history.actionType:
                case 'initial' | 'edit':
                    print(f'{version.action} {version.path}')
                    file_path = version.write('.', check_exists=False)
                    subprocess.check_call((self.GIT, 'add', file_path))
                    commit(version, 'update')
                case 'move':
                    if page_history.changed:
                        page = version.page
                        print(f'{version.action} {page.locale} {page_history.old_path} -> {page_history.new_path}')
                        old_path = page.file_path('.', page_history.old_path)
                        if not old_path.exists():
                            raise NameError(f"Error {old_path} is missing")
                        else:
                            new_path = page.file_path('.', page_history.new_path)
                            new_path.parent.mkdir(parents=True, exist_ok=True)
                            # Fixme: remove old directory
                            subprocess.check_call((self.GIT, 'mv', old_path, new_path))
                            # update file
                            file_path = version.write('.', check_exists=False)
                            subprocess.check_call((self.GIT, 'add', file_path))
                            commit(version, 'move')
                    else:
                        print(f'{version.action} unchanged')
                case _:
                    raise NotImplementedError(f"Action {version.action}")

        # Assets
        # asset_path = sync_dir.joinpath('_assets')
        asset_path = Path('_assets')
        asset_path.mkdir(parents=True, exist_ok=True)
        # Collect current asset list
        paths = []
        for dirpath, dirnames, filenames in asset_path.walk():
            dirpath = Path(dirpath)
            for filename in filenames:
                _ = dirpath.joinpath(filename)
                paths.append(_)

        def process_folder(folder_id: int = 0, stack: list = []):
            for asset in self._api.list_asset(folder_id):
                # url = '/'.join([self._api.api_url] + stack + [asset.filename])
                asset.path = '/'.join(stack + [asset.filename])
                yield asset
            for _ in self._api.list_asset_subfolder(folder_id):
                yield from process_folder(_.id, stack + [_.name])

        # To Git add, we must sort by date
        for asset in process_folder():
            data = self._api.get(asset.path)
            path = asset_path.joinpath(asset.path)   # .split('/')
            paths.remove(path)
            # asset.created_at.timestamp()
            mtime = asset.updated_at.timestamp()
            if not (path.exists() or path.stat().st_mtime == mtime):
                print(f"Write {asset.path}")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                os.utime(path, (mtime, mtime))

        # Clean old assets
        for _ in paths:
            _.unlink()

        # Now write history.json
        with open(self.HISTORY_JSON, 'w') as fh:
            # Fixme: reset ?
            json_versions = []
            for page_history in history:
                d = {
                    key: value
                    for key, value in page_history.__dict__.items()
                    if key not in ('api', 'page', '_page_version') and value is not None
                }
                page_version = page_history.page_version
                d['locale'] = page_version.locale
                d['path'] = page_version.path
                d['pageId'] = page_version.pageId
                json_versions.append(d)
            # last = history[-1]
            # data = {
            #     'versions': versions,
            #     'last_version_id': last.versionId,
            #     'laste_date': last.versionDate,
            # }
            json.dump(json_versions, fh, ensure_ascii=False, indent=4)

    ##############################################

    def check(self) -> None:
        pages = list(self._api.list_pages())
        page_paths = [_.path for _ in pages]
        for page in pages:
            # print(f"Checking {page.path}")
            page.complete()
            dead_links = []
            for line in page.content.splitlines():
                start = 0
                while True:
                    i = line.find('](', start)
                    if i != -1:
                        start = i+2
                        j = line.find(')', start)
                        if j != -1:
                            path = line[start:j].strip()
                            if path.startswith('/'):
                                path = path[1:]
                            _ = path.rfind('.')
                            if _ != -1:
                                extension = path[_:]
                            else:
                                extension = None
                            if (not re.match('^https?\\://', path)
                                and extension not in ('.png', '.jpg', '.webp', '.ods', '.pdf')
                                and path not in page_paths):
                                message = f"  <green>{path}</green>{LINESEP}    |{line}"
                                if path:
                                    parts = path.split('/')
                                    name = parts[-1]
                                    for _ in page_paths:
                                        name2 = _.split('/')[-1]
                                        if name in name2:
                                            message += f"{LINESEP}    <blue>found</blue> <green>{_}</green>"
                                    dead_links.append(message)
                    else:
                        break
            if dead_links:
                _ = f"<red>Page</red> <blue>{page.url}</blue> <red>as deak link</red>" + LINESEP
                _ += LINESEP.join(dead_links)
                self.print(_)

    ##############################################

    def tags(self) -> None:
        for _ in self._api.tags():
            self.print(f'<blue>{_.tag:30}</blue> <green>{_.title}</green>')

    ##############################################

    def search_tags(self, query: str) -> None:
        for _ in self._api.search_tags(query):
            self.print(f'<blue>{_}</blue>')

    ##############################################

    def links(self) -> None:
        pages = list(self._api.links())
        pages.sort(key=lambda _: _.path)
        for page in pages:
            self.print(f'<blue>{page.path:60}</blue>')
            # sorted()
            for _ in page.links:
                self.print(f'  <green>{_}</green>')
