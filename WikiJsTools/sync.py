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

from .WikiJsApi import WikiJsApi

####################################################################################################

GIT = '/usr/bin/git'
GIT_SYNC = 'git_sync'
HISTORY_JSON = 'history.json'

####################################################################################################

def sync(api: WikiJsApi, path: Path = None) -> None:
    """Sync on disk"""
    if path is None:
        path = Path('.', 'sync')
    path.mkdir(exist_ok=True)

    # i = 0
    for page in api.list_pages():
        page.complete()
        file_path = page.sync(path)
        if file_path is not None:
            print(f"Wrote {file_path}")
        # else is up to date
        # i += 1
        # if i > 3:
        #    break

####################################################################################################

def git_sync(api: WikiJsApi, path: Path = None) -> None:
    """Sync Git repo"""
    # Protection
    if Path.cwd().joinpath('.git').exists():
        print(f"Current path is a git repo. Exit")
        return

    if path is None:
        sync_dir = Path('.', GIT_SYNC).resolve()
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
        # Fixme: to func
        subprocess.run((GIT, 'init'), check=True)
    else:
        with open(HISTORY_JSON, 'r') as fh:
            json_versions = json.load(fh)
            last_version = json_versions[-1]
            # How versionID are generated ???
            # last_version_id = last_version['versionId']
            last_version_date = datetime.fromisoformat(last_version['versionDate'])
        print(f"Last version date {last_version_date}")

    def commit(version, message: str) -> None:
        subprocess.run(
            (
                GIT,
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
    print("Get page histories...")
    history = api.history(progress_callback)
    print("Done")

    # Commit page history
    for page_history in history:
        if last_version_date is not None:
            _ = datetime.fromisoformat(page_history.versionDate)
            if _ <= last_version_date:
                continue

        version = page_history.page_version
        # Fixme: ???
        if 'content' in version.path:
            pprint(page_history)
            pprint(version)
        # /!\ In some case page_history.actionType = initial and version.action = moved
        match page_history.actionType:
            case 'initial' | 'edit':
                print(f'{version.action} {version.path}')
                file_path = version.sync('.', check_exists=False)
                subprocess.run((GIT, 'add', file_path), check=True)
                commit(version, f'update {file_path}')
            case 'move':
                # Fixme: ???
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
                        subprocess.run((GIT, 'mv', old_path, new_path), check=True)
                        # update file content metadata
                        file_path = version.sync('.', check_exists=False)
                        subprocess.run((GIT, 'add', file_path), check=True)
                        # Fixme: is move and update possible ???
                        commit(version, f'move {old_path} -> {new_path}')
                else:
                    print(f'{version.action} unchanged')
            case _:
                raise NotImplementedError(f"Action {version.action}")

    # Save Assets
    #  Wiki.js doesn't implement an history for assets
    # asset_path = sync_dir.joinpath('_assets')
    asset_path = Path('_assets')
    asset_path.mkdir(parents=True, exist_ok=True)
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
            print(f"Write {asset.path}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            os.utime(path, (mtime, mtime))

    # Clean old assets
    for _ in paths:
        _.unlink()

    # Now write history.json
    with open(HISTORY_JSON, 'w') as fh:
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
