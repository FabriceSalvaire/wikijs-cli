###################################################################################################

__all__ = ['Cli']

####################################################################################################

# import logging
import os
import traceback

# See also [cmd — Support for line-oriented command interpreters — Python documentation](https://docs.python.org/3/library/cmd.html)
# Python Prompt Toolkit](https://python-prompt-toolkit.readthedocs.io/en/master/)
from prompt_toolkit import PromptSession, HTML
from prompt_toolkit import print_formatted_text, shortcuts
from prompt_toolkit.completion import WordCompleter
# from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style

from WikiJsApi import Page, WikiJsApi

####################################################################################################

# _module_logger = logging.getLogger('')

LINESEP = os.linesep

####################################################################################################

class Cli:

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
    ])

    ##############################################

    def __init__(self, api: WikiJsApi) -> None:
        self._api = api
        self.COMMANDS = [
            _
            for _ in dir(self)
            if not (_.startswith('_') or _[0].isupper() or _ in ('cli',))
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
            "<red>enter</red>: <blue>command argument</blue>",
            "<red>commands are</red>: " + ', '.join([f"<blue>{_}</blue>" for _ in self.COMMANDS]),
            "exit using command <blue>quit</blue> or <blue>Ctrl+d</blue>"
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
        _ = f"  <green>{old_path}</green> <red>-></red> <blue>{new_path}</blue>"
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
                _ = f"  <green>{page.path}</green> <red>-></red> <blue>{dest}</blue>"
                print_formatted_text(
                    HTML(_),
                    style=self.STYLE,
                )
                if not dryrun:
                    pass
                    # page.move(dest)
