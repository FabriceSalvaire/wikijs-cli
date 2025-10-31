####################################################################################################
#
# wikijs-cli - A CLI for Wiki.js
# Copyright (C) 2025 Fabrice SALVAIRE
# SPDX-License-Identifier: GPL-3.0-or-later
#
####################################################################################################

__all__ = ['sync', 'git_sync']

####################################################################################################

from datetime import datetime
from pathlib import Path
from pprint import pprint
import json
import os
import subprocess

from .printer import printc, CommandError
from .WikiJsApi import WikiJsApi

####################################################################################################

GIT = '/usr/bin/git'

HISTORY_JSON = 'wikijs-history.json'

####################################################################################################

def sync_asset(api: WikiJsApi, path: Path, exist_ok: bool = False) -> None:

    # DANGER : remove all the files that are not listed as assets !!!

    asset_path = Path(path).expanduser().resolve()
    # Protection
    if asset_path.exists() and not exist_ok:
        raise CommandError(f"<red>Asset path <green>{asset_path}</green> exists</red>")
    asset_path.mkdir(parents=True, exist_ok=exist_ok)

    # Collect current asset list on disk
    paths = []
    for dirpath, dirnames, filenames in asset_path.walk():
        dirpath = Path(dirpath)
        for filename in filenames:
            _ = dirpath.joinpath(filename)
            paths.append(_)

    def process_folder(folder_id: int = 0, stack: list = []):
        for asset in api.list_asset(folder_id):
            # url = '/'.join([api.api_url] + stack + [asset.filename])
            asset.path = '/'.join(stack + [asset.filename])
            yield asset
        for _ in api.list_asset_subfolder(folder_id):
            yield from process_folder(_.id, stack + [_.name])

    # To Git add, we must sort by date
    for asset in process_folder():
        data = api.get(asset.path)
        path = asset_path.joinpath(asset.path)   # .split('/')
        if path in paths:
            paths.remove(path)
        # asset.created_at.timestamp()
        mtime = asset.updated_at.timestamp()
        if not (path.exists() and path.stat().st_mtime == mtime):
            printc(f"Write {asset.path}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            os.utime(path, (mtime, mtime))

    # Clean old assets
    for _ in paths:
        _.unlink()

####################################################################################################

def sync(api: WikiJsApi, path: Path) -> None:
    """Sync on disk"""

   # DANGER : write many files and delete old assets !!!

    sync_path = Path(path).expanduser().resolve()
    if sync_path.exists():
        raise CommandError(f"<red>Sync path <green>{sync_path}</green> exists</red>")
    printc(f"Sync path <green>{sync_path}</green>")
    # Protection
    sync_path.mkdir(exist_ok=False)

    for page in api.list_pages():
        page.complete()
        file_path = page.sync(sync_path)
        if file_path is not None:
            _ = file_path.relative_to(sync_path)
            printc(f"Wrote {_}")
        # else is up to date

    asset_path = sync_path.joinpath('_assets')
    sync_asset(api, asset_path)

####################################################################################################

def git_sync(api: WikiJsApi, path: Path) -> None:
    """Sync Git repo"""

    # DANGER : don't run in another Git repo !!!

    # Fixme: remove ???
    # Protection
    # if Path.cwd().joinpath('.git').exists():
    #     printc(f"Current path is a git repo. Exit")
    #     return

    repo_path = Path(path).expanduser().resolve()
    printc(f"Git repository path <green>{repo_path}</green>")

    created = False
    if repo_path.exists():
        # Protection
        if not repo_path.joinpath('.git').exists():
            raise CommandError(f"<red> Directory <green>{repo_path}</green> is not a git repository</red>")
        if not repo_path.joinpath(HISTORY_JSON).exists():
            raise CommandError(f"<red> Directory <green>{repo_path}</green> doesn't have a JSON history</red>")
        printc("Git already initialised")
    else:
        repo_path.mkdir()
        created = True

    history_json_path = repo_path.joinpath(HISTORY_JSON)
    asset_path = repo_path.joinpath('_assets')

    def git(command: str, *args) -> None:
        subprocess.run(
            (
                GIT,
                command,
                *args,
            ),
            check=True,
            cwd=repo_path,
        )

    def commit(date, message: str) -> None:
        git(
            'commit',
            '-m', message,
            f'--date={date}',
        )

    json_versions = []
    last_version_date = None
    if created:
        git('init')
    else:
        with open(history_json_path, 'r') as fh:
            json_versions = json.load(fh)
            last_version = json_versions[-1]
            # How versionID are generated ???
            # last_version_id = last_version['versionId']
            last_version_date = datetime.fromisoformat(last_version['versionDate'])
        printc(f"Last version date {last_version_date}")

    # Fixme: progress callback
    #  how to get number of versions ?
    def progress_callback(p: int) -> None:
        printc(f"{p} % done")

    # Fixme: skip ?
    printc("Get page histories...")
    history = api.history(progress_callback)
    printc("Done")

    # Commit page history
    for ph in history:
        if last_version_date is not None:
            _ = datetime.fromisoformat(ph.versionDate)
            if _ <= last_version_date:
                continue

        page = ph.page
        pv = ph.page_version   # is None for current

        # Fixme: ???
        # if 'content' in pv.path:
        #     pprint(ph)
        #     pprint(pv)

        # /!\ In some case ph.actionType = initial and pv.action = moved
        match ph.actionType:
            case 'initial' | 'edit':
                if pv is not None:
                    wrapper = pv
                    action = pv.action
                    date = pv.versionDate
                else:
                    # current version
                    wrapper = page
                    action = 'current'
                    date = page.updatedAt
                    page.complete()
                printc(f'<blue>{action}</blue> @{page.locale} <green>{page.path}</green>')
                file_path = wrapper.sync(repo_path, check_exists=False)
                git('add', file_path)
                message = f'update @{page.locale} {page.path}'
                commit(date, message)
            case 'move':
                # Fixme: ???
                if ph.changed:
                    printc(f'<blue>{pv.action}</blue> @{page.locale} <green>{ph.old_path}</green> -> <green>{ph.new_path}</green>')
                    old_path = page.file_path(repo_path, ph.old_path)
                    if not old_path.exists():
                        raise CommandError(f"<red>Error <green>{old_path}</green> is missing</red>")
                    else:
                        new_path = page.file_path(repo_path, ph.new_path)
                        new_path.parent.mkdir(parents=True, exist_ok=True)
                        # Fixme: remove old directory
                        git('mv', old_path, new_path)
                        # update file content metadata
                        file_path = pv.sync(repo_path, check_exists=False)
                        git('add', file_path)
                        # Fixme: is move and update possible ???
                        message = f'move @{page.locale} {ph.old_path} -> {ph.new_path}'
                        commit(pv.versionDate, message)
                else:
                    printc(f'<red>@{page.locale} {pv.page.path} {pv.action} unchanged</red>')
            case _:
                raise NotImplementedError(f"Action {pv.action}")

    # Save Assets
    #  Wiki.js doesn't implement an history for assets
    sync_asset(api, asset_path, exist_ok=True)

    # Now write history.json
    with open(history_json_path, 'w') as fh:
        # Fixme: reset ?
        json_versions = []
        for ph in history:
            pv = ph.page_version
            if pv is None:
                continue
            d = {
                key: value
                # Fixme: better ?
                for key, value in ph.__dict__.items()
                if key not in ('api', 'page', '_page_version') and value is not None
            }
            d['locale'] = pv.locale
            d['path'] = pv.path
            d['pageId'] = pv.pageId
            json_versions.append(d)
        # last = history[-1]
        # data = {
        #     'versions': versions,
        #     'last_version_id': last.versionId,
        #     'laste_date': last.versionDate,
        # }
        json.dump(json_versions, fh, ensure_ascii=False, indent=4)
