####################################################################################################
#
# wikijs-cli - A CLI for Wiki.js
# Copyright (C) 2025 Fabrice SALVAIRE
# SPDX-License-Identifier: GPL-3.0-or-later
#
####################################################################################################

###################################################################################################

__all__ = ['Cli']

####################################################################################################

from datetime import datetime
from pathlib import PurePosixPath
from pprint import pprint
from typing import Iterable
import difflib
import html
import inspect
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
from prompt_toolkit.completion import WordCompleter, Completer, Completion, CompleteEvent
from prompt_toolkit.document import Document
# from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import ProgressBar
from prompt_toolkit.styles import Style

from .WikiJsApi import Page, WikiJsApi, Node

####################################################################################################

# _module_logger = logging.getLogger('')

LINESEP = os.linesep

# Fixme: ?
#  from typing import NewType
type CommandName = str
type PagePath = str   # aka PurePosixPath
type PageFolder = str   # aka PurePosixPath
type AssetFolder = str   # aka PurePosixPath
type FilePath = str   # aka Path
type Tag = str   # aka Path

####################################################################################################

class CustomCompleter(Completer):

    """
    Simple autocompletion on a list of words.

    :param words: List of words or callable that returns a list of words.
    :param ignore_case: If True, case-insensitive completion.
    :param meta_dict: Optional dict mapping words to their meta-text. (This
        should map strings to strings or formatted text.)
    :param WORD: When True, use WORD characters.
    :param sentence: When True, don't complete by comparing the word before the
        cursor, but by comparing all the text before the cursor. In this case,
        the list of words is just a list of strings, where each string can
        contain spaces. (Can not be used together with the WORD option.)
    :param match_middle: When True, match not only the start, but also in the
                         middle of the word.
    :param pattern: Optional compiled regex for finding the word before
        the cursor to complete. When given, use this regex pattern instead of
        default one (see document._FIND_WORD_RE)
    """

    ##############################################

    def __init__(self, cli, commands: list[str]) -> Node:
        self._cli = cli
        self._commands = commands

        self.ignore_case = True
        # self.display_dict = display_dict or {}
        # self.meta_dict = meta_dict or {}
        self.WORD = False
        self.sentence = False
        self.match_middle = False
        self.pattern = None

    ##############################################

    # cf. prompt_toolkit/completion/word_completer.py
    def _get_completions(
            self,
            document: Document,
            complete_event: CompleteEvent,
            words: list[str],
            separator: str,
    ) -> Iterable[Completion]:
        # Get list of words.
        # if callable(words):
        #     words = words()

        # Get word/text before cursor.
        # if self.sentence:
        #     word_before_cursor = document.text_before_cursor
        # else:
        # word_before_cursor = document.get_word_before_cursor(
        #     WORD=self.WORD, pattern=self.pattern
        # )
        line = document.current_line
        index = line.rfind(separator)
        word_before_cursor = line[index+1:]

        if self.ignore_case:
            word_before_cursor = word_before_cursor.lower()

        def word_matches(word: str) -> bool:
            """True when the word before the cursor matches."""
            if self.ignore_case:
                word = word.lower()

            if self.match_middle:
                return word_before_cursor in word
            else:
                return word.startswith(word_before_cursor)

        for _ in words:
            if word_matches(_):
                # display = self.display_dict.get(_, _)
                # display_meta = self.meta_dict.get(_, "")
                yield Completion(
                    text=_,
                    start_position=-len(word_before_cursor),
                    # display=display,
                    # display_meta=display_meta,
                )

    ##############################################

    def get_completions(
            self,
            document: Document,
            complete_event: CompleteEvent,
    ) -> Iterable[Completion]:
        line = document.current_line.lstrip()
        line = re.sub(' +', ' ', line)
        number_of_parameters = line.count(' ')
        command = None
        right_word = None
        parameter_type = None
        if number_of_parameters:
            # words = [_ for _ in line.split(' ') if _]
            # command = words[0]
            index = line.rfind(' ')
            right_word = line[index+1:]
            index = line.find(' ')
            command = line[:index]
            try:
                func = getattr(Cli, command)
                signature = inspect.signature(func)
                parameters = list(signature.parameters.values())
                if len(parameters) > 1:
                    parameter = parameters[number_of_parameters]   # 0 is self
                    parameter_type = parameter.annotation.__name__   # Fixme: case type alias ???
            except AttributeError:
                pass
        # print(f'Debug: "{command}" | "{right_word}" | {number_of_parameters} | {parameter_type}')

        separator = ' '

        def handle_cd(current_path, path, folder: bool):
            cwd = current_path.find(path)
            if '/' in path:
                nonlocal separator
                separator = '/'
            if folder:
                return cwd.folder_names
            else:
                return cwd.leaf_names

        if command is None:
            words = self._commands
        else:
            words = ()
            match parameter_type:
                case 'bool':
                    words = ('true', 'false')
                case 'CommandName':
                    words = self._commands
                case 'FilePath':
                    # match command:
                    #     case 'create' | 'update':
                    cwd = Path().cwd()
                    filenames = sorted(cwd.glob('*.md'))
                    words = [_.name for _ in filenames]
                case 'PagePath':
                    words = handle_cd(self._cli._current_path, right_word, folder=False)
                case 'PageFolder':
                    words = handle_cd(self._cli._current_path, right_word, folder=True)
                case 'AssetFolder':
                    words = handle_cd(self._cli._current_asset_folder, right_word, folder=True)
                case 'Tag':
                    # Fixme: tag can have space !
                    words = [_.tag for _ in self._cli._api.tags()]
        yield from self._get_completions(document, complete_event, words, separator)

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
            if not (_.startswith('_') or _[0].isupper() or _ in ('cli', 'run', 'print'))
        ]
        self.COMMANDS.sort()
        # self._completer = WordCompleter(self.COMMANDS)
        self._completer = CustomCompleter(self, self.COMMANDS)
        self._page_tree = None
        self._current_path = None
        self._asset_tree = None
        self._current_asset_folder = None

    ##############################################

    @staticmethod
    def _to_bool(value: str) -> bool:
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
        self.print("<red>Build tree...</red>")
        self._init()
        self.print("<red>Done</red>")

        if query:
            if not self.run(query):
                return

        history = FileHistory(self.CLI_HISTORY)
        session = PromptSession(
            completer=self._completer,
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

    def print(self, message: str = '') -> None:
        if message:
            message = HTML(message)
        print_formatted_text(
            message,
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
            "use <blue>help</blue> <green>command</green> to get help",
            "use <green>tab</green> key to complete",
            "use <green>up/down</green> key to navigate history",
            "<red>Exit</red> using command <blue>quit</blue> or <blue>Ctrl+d</blue>"
        ):
            self.print(_)

            # "  <blue>dump</blue> <green>@page_url@ [output]</green>: dump the page",
            # "  <blue>list</blue>: list all the pages",
            # "  <blue>move</blue> <green>@page_url@ @new_page_url@</green>: move a page",
            # "  <blue>update</blue> <green>@page_url@ input</green>: update the page",
            # "  <blue>create</blue> <green>input</green>: create a page",
            # "  <blue>template</blue> <green>output</green>: create a page template",
            # "  <blue>check</blue>: check pages",
            # "  <blue>asset</blue>: list all the assets",
            # "  <blue>sync</blue>: sync wiki on disk",
            # "  <blue>git_sync</blue>: sync wiki on a Git repo",

    ##############################################

    def _absolut_path(self, path: str) -> PurePosixPath:
        if not path.startswith('/') and self._current_path:
            path = self._current_path.join(path)
        return PurePosixPath(path)

    ##############################################

    def help(self, command: CommandName) -> None:
        func = getattr(self, command)
        # help(func)
        self.print(f'<blue>{func.__doc__}</blue>')
        signature = inspect.signature(func)
        for _ in signature.parameters.values():
            if _.default != inspect._empty:
                default = f' = <orange>{_.default}</orange>'
            else:
                default = ''
            self.print(f'  <blue>{_.name}</blue>: <green>{_.annotation.__name__}</green>{default}')

    ##############################################

    def list(self, complete: bool = False) -> None:
        """List the pages"""
        complete = self._to_bool(complete)
        for page in self._api.list_pages():
            if complete:
                page.complete()
                self.print(f"<green>{page.path:60}</green> <blue>{page.title:40}</blue> {len(page.content):5} @{page.locale} {page.id:3}")
            else:
                self.print(f"<green>{page.path:60}</green> <blue>{page.title:40}</blue> @{page.locale} {page.id:3}")

    ##############################################

    def listp(self, path: PagePath) -> None:
        for page in self._api.list_pages():
            if path in page.path.lower():
                self.print(f"<green>{page.path:60}</green> <blue>{page.title:40}</blue> @{page.locale} {page.id:3}")

    ##############################################

    def last(self) -> None:
        """List the last updated pages"""
        for page in self._api.list_pages(order_by='UPDATED', reverse=True, limit=10):
            self.print(f"<green>{page.path:60}</green> <blue>{page.title:40}</blue>{LINESEP}  {page.updated_at}   @{page.locale}   {page.id:3}")

    ##############################################

    def tree(self, path: PagePath) -> None:
        """Show page tree"""
        pages = list(self._api.tree(path))
        pages.sort(key=lambda _: _.path)
        for page in pages:
            is_folder = '/' if page.isFolder else ''
            path = f"{page.path}{is_folder}"
            self.print(f"<green>{path:60}</green> <blue>{page.title:40}</blue>")

    ##############################################

    def dump(self, path: PagePath, output: str = None) -> None:
        """dump a page"""
        path = self._absolut_path(path)
        page = self._api.page(path)   # locale=
        page.complete()
        # Fixme: write dump on stdout
        _ = f"<green>{page.path}</green> @{page.locale}{LINESEP}"
        _ += f"  <blue>{page.title}</blue>{LINESEP}"
        _ += f"  {page.id}{LINESEP}"
        self.print(_)
        if output:
            output = page.add_extension(output)
            if output.exists():
                self.print(f"<red>File exists</red> {output}")
            else:
                self.print(f"<blue>Write</blue> {output}")
                page.write(output)
        else:
            rule = '\u2500' * 100
            print(rule)
            print(page.content)
            print(rule)

    ##############################################

    def reset(self) -> None:
        """Reset page and folder tree"""
        self._page_tree = self._api.build_page_tree(ProgressBar)
        self._asset_tree = self._api.build_asset_tree()
        self._current_path = self._page_tree
        self._current_asset_folder = self._asset_tree
        # reset current_path ?

    def _init(self) -> None:
        if self._page_tree is None:
            self.reset()

    ##############################################

    def ls(self) -> None:
        """List the current path"""
        self._init()
        self.print(f"<red>CWD</red> <blue>{self._current_path.path}</blue>")
        # for _ in self._current_path.folder_childs:
        #     self.print(f"  {_.name}")
        for _ in self._current_path.childs:
            if _.is_folder:
                self.print(f"  <green>{_.name} /</green>")
            else:
                self.print(f"  <blue>{_.name}</blue> : <orange>{_.page.title}</orange>")

    ##############################################

    def cd(self, path: PageFolder) -> None:
        """Change the current path"""
        self._init()
        if path == '..':
            if not self._current_path.is_root:
                self._current_path = self._current_path.parent
        else:
            _ = self._current_path.find(path)
            if _.is_leaf:
                self.print(f"<red>Error: </red> <blue>{path}</blue> <red>is not a folder</red>")
            self._current_path = _
        self.print(f"<red>moved to</red> <blue>{self._current_path.path}</blue>")

    ##############################################

    def lsa(self) -> None:
        """List the current asset folder"""
        self._init()
        self.print(f"<red>CWD</red> <blue>{self._current_asset_folder.path}</blue>")
        # for _ in self._current_path.folder_childs:
        #     self.print(f"  {_.name}")
        for _ in self._current_asset_folder.childs:
            if _.is_folder:
                self.print(f"  <green>{_.name} /</green>")
            else:
                self.print(f"  <blue>{_.name}</blue>")

    ##############################################

    def cda(self, path: AssetFolder) -> None:
        """Change the current asset folder"""
        self._init()
        if path == '..':
            if not self._current_asset_folder.is_root:
                self._current_asset_folder = self._current_asset_folder.parent
        else:
            _ = self._current_asset_folder.find(path)
            if _.is_leaf:
                self.print(f"<red>Error: </red> <blue>{path}</blue> <red>is not a folder</red>")
            self._current_asset_folder = _
        self.print(f"<red>moved to</red> <blue>{self._current_asset_folder.path}</blue>")

        # try:
        #     self._current_asset_folder = self._asset_folders[path]
        #     self.print(f"<red>moved to</red> <blue>{path}</blue>")
        # except KeyError:
        #     self.print(f"<red>Error:</red> <blue>{path}</blue> <red>not found</red>")

    ##############################################

    def cwd(self) -> None:
        """Show current working directry"""
        self.print(f"<blue>Current path</blue> <green>{self._current_path.path}</green>")
        self.print(f"<blue>Current asset path</blue> <green>{self._current_asset_folder}</green>")

    ##############################################

    @classmethod
    def _fix_extension(self, filename: str, content_type: str = 'markdown') -> Path:
        extension = Page.extension_for(content_type)
        if not filename.endswith(extension):
            filename += extension
        return Path(filename)

    ##############################################

    def template(self, dst: FilePath, path: PagePath = None, locale: str = 'fr', content_type: str = 'markdown') -> None:
        """Write a page template"""
        dst = self._fix_extension(dst)
        if self._current_path:
            if path is None:
                path = dst.stem
            path = self._current_path.join(path)
            self.print(f"<red>Path is</red> <blue>{path}</blue>")
        elif path is None:
            self.print("<red>path is required</red>")

        if Page.template(dst, locale, path, content_type) is None:
            self.print(f"<red>Error: file exists</red>")
        else:
            self.print(f"<red>Wrote</red>  <blue>{dst}</blue>")

    ##############################################

    def emc(self, dst: FilePath) -> None:
        dst = self._fix_extension(dst)
        subprocess.Popen(('/usr/bin/emacsclient', dst), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    ##############################################

    def open(self, path: PagePath, locale: str = 'fr') -> None:
        path = self._absolut_path(path)
        url = f'{self._api.api_url}/{locale}/{path}'
        self.print(f"<red>Open</red>  <blue>{url}</blue>")
        subprocess.Popen(('/usr/bin/xdg-open', url), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    ##############################################

    def create(self, input: FilePath) -> None:
        """Create a new page"""
        input = self._fix_extension(input)
        page = Page.read(input, self._api)
        if page.title is None:
            self.print(f"<red>Error: missing title</red>")
            return
        _ = f"<green>{page.path}</green> @{page.locale}{LINESEP}"
        _ += f"  <blue>{page.title}</blue>{LINESEP}"
        self.print(_)
        response = self._api.create_page(page)
        self.print(f"<red>{response.message}</red>")

    ##############################################

    def diff(self, input: FilePath = None) -> None:
        """Diff a page"""
        file_page = Page.read(input, self._api)
        wiki_page = file_page.reload()
        wiki_page.complete()
        self.print(f"<red>Wiki:</red> <blue>{wiki_page.updated_at}</blue>")
        self.print(f"<red>File:</red> <blue>{file_page.updated_at}</blue>")
        for _ in difflib.unified_diff(
                wiki_page.content.splitlines(),
                file_page.content.splitlines(),
                fromfile='wiki',
                tofile='disk',
                n=3,
                lineterm='',
        ):
            _ = html.escape(_)
            if _.startswith('---') or _.startswith('+++'):
                _ = f'<green>{_}</green>'
            elif _.startswith('@@'):
                _ = f'<blue>{_}</blue>'
            elif _.startswith('-'):
                _ = f'<red>-</red>{_[1:]}'
            elif _.startswith('+'):
                _ = f'<green>+</green>{_[1:]}'
            self.print(_)

    ##############################################

    def update(self, input: FilePath = None) -> None:
        """Update a page"""
        page = Page.read(input, self._api)
        _ = f"<green>{page.path}</green> @{page.locale}{LINESEP}"
        _ += f"  <blue>{page.title}</blue>{LINESEP}"
        _ += f"  {page.id}{LINESEP}"
        self.print(_)
        response = page.update()
        self.print(f"<red>{response.message}</red>")

    ##############################################

    def movep(self, old_path: PagePath, new_path: PagePath, dryrun: bool = False) -> None:
        """Move the pages that match the path pattern"""
        # <pattern>/... -> <new_pattern>/...
        # relative page -> folder
        dryrun = self._to_bool(dryrun)
        # self.print(f"  Move: <green>{old_path}</green> <red>-></red> <blue>{new_path}</blue>")
        for page in self._api.list_pages():
            path = page.path
            if path.startswith(old_path):
                dest = path.replace(old_path, new_path)
                self.print(f"  Move page: <green>{path}</green> <red>-></red> <blue>{dest}</blue>")
                if not dryrun:
                    response = page.move(dest)
                    self.print(f"<red>{response.message}</red>")

    ##############################################

    def _move_impl(self, path: str, new_path: str, rename: bool = False, dryrun: bool = False) -> None:
        """Move a page"""
        path = self._absolut_path(path)
        page = self._api.page(path)   # locale=
        new_path = self._absolut_path(new_path)
        if not rename:
            dest = new_path.joinpath(page.path.name)
        self.print(f"  Move page: <green>{path}</green> <red>-></red> <blue>{dest}</blue>")
        dryrun = self._to_bool(dryrun)
        if not dryrun:
            response = page.move(dest)
            self.print(f"<red>{response.message}</red>")


    def move(self, path: PagePath, new_path: PageFolder, dryrun: bool = False) -> None:
        """Move a page"""
        self._move_impl(path, new_path, dryrun)


    def rename(self, path: PagePath, new_path: PagePath, dryrun: bool = False) -> None:
        """Rename a page"""
        self._move_impl(path, new_path, rename=True, dryrun=dryrun)

    ##############################################

    def asset(self, show_files: bool = True, show_folder_path: bool = False) -> None:
        """List the assets"""
        show_files = self._to_bool(show_files)
        def show_folder(folder_id: int = 0, indent: int = 0, stack: list = []):
            indent_str = '  '*indent
            if show_files:
                for asset in self._api.list_asset(folder_id):
                    self.print(f"{indent_str}- <blue>{asset.filename}</blue>   {asset.updated_at}   <green>{asset.id}</green>")
                    url = '/'.join([self._api.api_url] + stack + [asset.filename])
                    self.print(f"{indent_str}  {url}")
            for _ in self._api.list_asset_subfolder(folder_id):
                path = '/'.join(stack + [_.name])
                # print(f"{indent_str}- {_.name} {_.slug} {_.id}")
                if show_folder_path:
                    self.print(f"<red>{path}</red>    <green>{_.id}</green>")
                else:
                    self.print(f"{indent_str}+ <red>{_.name}</red>    <green>{_.id}</green>")
                show_folder(_.id, indent + 1, stack + [_.name])
        self.print('<blue>/</blue>')
        show_folder()

    ##############################################

    def upload(self, path: FilePath, name: str = None) -> None:
        """Upload an asset"""
        if self._current_asset_folder is not None:
            self._current_asset_folder.upload(path, name)
            # lists asset folder
            assets = list(self._current_asset_folder.list())
            assets.sort(key=lambda _: _.updated_at, reverse=True)
            self.print(f'<blue>{self._current_asset_folder.path}</blue>')
            for asset in assets:
                self.print(f'- <blue>{asset.filename}</blue>   {asset.updated_at}')
        else:
            self.print(f"<red>Error: run cd_asset before</red>")

    ##############################################

    def search(self, query: str) -> None:
        """Search page"""
        response = self._api.search(query)
        if response.suggestions:
            _ = ', '.join(response.suggestions)
            self.print(f'Suggestions: <blue>{_}</blue>')
        for _ in response.results:
            self.print(f'<blue>{_.path:60}</blue> <green>{_.title}</green>')

    ##############################################

    def sync(self, path: Path = None) -> None:
        """Sync on disk"""
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
        """Sync Git repo"""
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
            subprocess.run((self.GIT, 'init'), check=True)
        else:
            with open(self.HISTORY_JSON, 'r') as fh:
                json_versions = json.load(fh)
                last_version = json_versions[-1]
                # How versionID are generated ???
                # last_version_id = last_version['versionId']
                last_version_date = datetime.fromisoformat(last_version['versionDate'])
            print(f"Last version date {last_version_date}")

        def commit(version, message: str) -> None:
            subprocess.run(
                (
                    self.GIT,
                    'commit',
                    '-m', message,
                    f'--date={version.versionDate}',
                ),
                check=True,
            )

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
                    file_path = version.sync('.', check_exists=False)
                    subprocess.run((self.GIT, 'add', file_path), check=True)
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
                            subprocess.run((self.GIT, 'mv', old_path, new_path), check=True)
                            # update file
                            file_path = version.sync('.', check_exists=False)
                            subprocess.run((self.GIT, 'add', file_path), check=True)
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
        """Check pages"""
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
        """List the tags"""
        for _ in self._api.tags():
            self.print(f'<blue>{_.tag:30}</blue> <green>{_.title}</green>')

    ##############################################

    def search_tags(self, query: str) -> None:
        """Search the tags"""
        for _ in self._api.search_tags(query):
            self.print(f'<blue>{_}</blue>')

    ##############################################

    def links(self) -> None:
        """List tha page links"""
        pages = list(self._api.links())
        pages.sort(key=lambda _: _.path)
        for page in pages:
            self.print(f'<blue>{page.path:60}</blue>')
            # sorted()
            for _ in page.links:
                self.print(f'  <green>{_}</green>')
