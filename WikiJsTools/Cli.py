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
from prompt_toolkit.styles import Style

from .WikiJsApi import Page, WikiJsApi

####################################################################################################

# _module_logger = logging.getLogger('')

LINESEP = os.linesep

####################################################################################################

class Cli:

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

    COMPLETER = WordCompleter([
        'clear',
        'dump',
        'list',
        'move',
        'quit',
        'update',
        'usage',
    ])

    ##############################################

    def __init__(self, api: WikiJsApi) -> None:
        self._api = api
        self.COMMANDS = [
            _
            for _ in dir(self)
            if not (_.startswith('_') or _[0].isupper() or _ in ('cli', 'run'))
        ]

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
            _ = f"<red>Invalid command</red> <blue>{query}</blue>"
            print_formatted_text(
                HTML(_),
                style=self.STYLE,
            )
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

        session = PromptSession(
            completer=self.COMPLETER,
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
            "<red>Exit</red> using command <blue>quit</blue> or <blue>Ctrl+d</blue>"
        ):
            print_formatted_text(
                HTML(_),
                style=self.STYLE,
            )

    ##############################################

    def list(self) -> None:
        for page in self._api.yield_pages():
            page.complete()
            _ = f"<green>{page.path:60}</green> <blue>{page.title:40}</blue> {len(page.content):5} @{page.locale} {page.id:3}"
            print_formatted_text(
                HTML(_),
                style=self.STYLE,
            )

        # if page.path.startswith('home/bricolage/'):
        # print()
        # print(f"{page.path} @{page.locale}")
        # print(f"  {page.title}")

        # print(f"  {page.id}")

        # print(page.content)

    ##############################################

    def tree(self, path: str) -> None:
        for page in self._api.yield_tree(path):
            pass
            # page.complete()
            # _ = f"<green>{page.path:60}</green> <blue>{page.title:40}</blue> {len(page.content):5} @{page.locale} {page.id:3}"
            # print_formatted_text(
            #     HTML(_),
            #     style=self.STYLE,
            # )

    ##############################################

    def dump(self, path: str, output: str = None) -> None:
        page = self._api.page(path)
        page.complete()
        _ = f"<green>{page.path}</green> @{page.locale}{LINESEP}"
        _ += f"  <blue>{page.title}</blue>{LINESEP}"
        _ += f"  {page.id}{LINESEP}"
        print_formatted_text(
            HTML(_),
            style=self.STYLE,
        )
        if output:
            output = Path(output)
            if not output.parent.exists():
                raise NameError(f"path doesn't exists {output.parent}")
            with open(output, mode='w', encoding='utf8') as fh:
                fh.write(page.content)
        else:
            rule = '\u2500' * 100
            print(rule)
            print(page.content)
            print(rule)

   ##############################################

    def update(self, path: str, input: str = None) -> None:
        page = self._api.page(path)
        page.complete()
        _ = f"<green>{page.path}</green> @{page.locale}{LINESEP}"
        _ += f"  <blue>{page.title}</blue>{LINESEP}"
        _ += f"  {page.id}{LINESEP}"
        print_formatted_text(
            HTML(_),
            style=self.STYLE,
        )
        with open(input, mode='r', encoding='utf8') as fh:
            content = fh.read()
        rule = '\u2500' * 100
        print(rule)
        print(page.content)
        print(rule)
        page.update(content)

    ##############################################

    def move(self, old_path: str, new_path: str, dryrun: bool = False) -> None:
        _ = f"  Move: <green>{old_path}</green> <red>-></red> <blue>{new_path}</blue>"
        print_formatted_text(
            HTML(_),
            style=self.STYLE,
        )
        for page in self._api.yield_pages():
            # for _ in ('portail',):
            # if page.path.lower().startswith('.../' + _):
            # print(page.path)
            if page.path.startswith(old_path):
                dest = page.path.replace(old_path, new_path)
                _ = f"  Move page: <green>{page.path}</green> <red>-></red> <blue>{dest}</blue>"
                print_formatted_text(
                    HTML(_),
                    style=self.STYLE,
                )
                if not dryrun:
                    page.move(dest)

    ##############################################

    def sync(self, path: Path = None) -> None:
        if path is None:
            path = Path('.', 'sync')
        path.mkdir(exist_ok=True)

        # i = 0
        for page in self._api.yield_pages():
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
            path = Path('.', self.GIT_SYNC).resolve()
        print(f"Git path {path}")

        created = False
        if path.exists():
            print("Git already initialised")
        else:
            path.mkdir()
            created = True
        os.chdir(path)
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
        pages = list(self._api.yield_pages())
        page_paths = [_.path for _ in pages]
        for page in pages:
            # print(f"Checking {page.path}")
            page.complete()
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
                                and extension not in ('.png', '.jpg', '.pdf')
                                and path not in page_paths):
                                _ = f"<red>Page</red> <blue>{page.url}</blue> <red>as deak link</red> <green>{path}</green>{LINESEP}{line}"
                                print_formatted_text(
                                    HTML(_),
                                    style=self.STYLE,
                                )
                    else:
                        break
