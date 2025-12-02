####################################################################################################
#
# wikijs-cli - A CLI for Wiki.js
# Copyright (C) 2025 Fabrice SALVAIRE
# SPDX-License-Identifier: GPL-3.0-or-later
#
####################################################################################################

# Emacs : (setq create-lockfiles nil)

# Somebody scans the whole file hierarchy
# Dolphin calls getxattr
# Editors attempt to write and read a lot of backup files... 

####################################################################################################

__all__ = ['mount']

####################################################################################################

# import logging

from collections import defaultdict
from errno import ENOENT, ENODATA
from pathlib import Path, PurePosixPath
from stat import S_IFDIR, S_IFLNK, S_IFREG
from time import time

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

from .WikiJsApi import WikiJsApi, ApiError, Page

####################################################################################################

def mount(api: WikiJsApi, path: str) -> None:
    fuse = FUSE(WikiJsFuse(api), path, foreground=True, allow_other=True)

####################################################################################################

class WikiJsFuse(LoggingMixIn, Operations):

    # https://libfuse.github.io/doxygen/structfuse__operations.html

    ##############################################

    def __init__(self, api: WikiJsApi) -> None:
        self._api = api
        self._mount_time = time()
        self.files = {}
        self.data = defaultdict(bytes)
        self.fd = 0
        # now = time()
        # self.files['/'] = dict(
        #     st_mode=(S_IFDIR | 0o755),
        #     st_ctime=now,
        #     st_mtime=now,
        #     st_atime=now,
        #     st_nlink=2,
        # )

    ##############################################

    # def _list_folder(self, path: str) -> None:
    #     items = list(self._itree(0))
    #     for item in items:
    #         print(item.id, item.path, item.isFolder)

    def _query_folder(self, path: PurePosixPath):
        cache = []
        for i, part in enumerate(path.parts):
            if i == 0:
                folder_id = 0
            else:
                folder = cache[i-1][part]
                folder_id = folder.id
            items = {_.path.name: _ for _ in self._api.itree(folder_id)}
            cache.append(items)
        return cache

    ##############################################

    def chmod(self, path: str, mode: int):
        # self.files[path]['st_mode'] &= 0o770000
        # self.files[path]['st_mode'] |= mode
        return 0

    ##############################################

    def chown(self, path: str, uid, gid):
        # self.files[path]['st_uid'] = uid
        # self.files[path]['st_gid'] = gid
        pass

    ##############################################

    def create(self, path: str, mode: int):
        self.files[path] = dict(
            st_mode=(S_IFREG | mode),
            st_nlink=1,
            st_size=0,
            st_ctime=time(),
            st_mtime=time(),
            st_atime=time(),
        )
        self.fd += 1
        return self.fd

    ##############################################

    def getattr(self, path: str, fh=None):
        """Get file attributes. Similar to stat()"""
        # if path not in self.files:
        #     raise FuseOSError(ENOENT)
        # return self.files[path]
        mount_time = self._mount_time
        if path == '/':
            return dict(
                st_mode=(S_IFDIR | 0o755),
                st_ctime=mount_time,
                st_mtime=mount_time,
                st_atime=mount_time,
                st_nlink=2,
            )
        else:
            path = PurePosixPath(path)
            cache = self._query_folder(path.parent)
            # print(f"Lookup {path}")
            # print(f"Cache {cache[-1]}")
            try:
                item = cache[-1][path.name]
            except KeyError:
                raise FuseOSError(ENOENT)
            if item.isFolder:
                return dict(
                    st_mode=(S_IFDIR | 0o755),
                    st_ctime=mount_time,
                    st_mtime=mount_time,
                    st_atime=mount_time,
                    st_nlink=2,
                )
            else:
                page = self._api.page(path)
                data = page.bytes_data
                return dict(
                    st_mode=(S_IFREG | 0o644),
                    st_ctime=page.created_at.timestamp(),
                    st_mtime=page.updated_at.timestamp(),
                    st_atime=mount_time,
                    st_nlink=1,
                    st_size=len(data),
                )

    ##############################################

    def getxattr(self, path: str, name: str, position: int = 0) -> str:
        # attrs = self.files[path].get('attrs', {})
        # try:
        #     return attrs[name]
        # except KeyError:
        #     return ''   # Should return ENOATTR
        # match name:
        #     case 'system.posix_acl_access':
        #     case 'security.capability'
        #         # return 'unconfined_u:object_r:user_home_t:s0'
        #         return FuseOSError(ENODATA)
        # return FuseOSError(ENODATA)
        return b''

    ##############################################

    def listxattr(self, path: str):
        # attrs = self.files[path].get('attrs', {})
        # return attrs.keys()
        return ()

    ##############################################

    def mkdir(self, path: str, mode: int):
        # self.files[path] = dict(
        #     st_mode=(S_IFDIR | mode),
        #     st_nlink=2,
        #     st_size=0,
        #     st_ctime=time(),
        #     st_mtime=time(),
        #     st_atime=time(),
        # )
        # self.files['/']['st_nlink'] += 1
        pass

    ##############################################

    def open(self, path: str, flags) -> int:
        self.fd += 1
        return self.fd

    ##############################################

    def read(self, path: str, size, offset, fh) -> bytes:
        print('read', path, size, offset, fh)
        page = self._api.page(path)
        data = page.bytes_data
        return data[offset:offset + size]

    ##############################################

    def readdir(self, path: str, fh: int) -> list[str]:
        path = PurePosixPath(path)
        cache = self._query_folder(path)
        return ['.', '..'] + list(cache[-1].keys())

    ##############################################

    def readlink(self, path: str):
        return self.data[path]

    ##############################################

    def removexattr(self, path: str, name):
        # attrs = self.files[path].get('attrs', {})
        # try:
        #     del attrs[name]
        # except KeyError:
        #     pass   # Should return ENOATTR
        pass

    ##############################################

    def rename(self, old, new):
        # self.data[new] = self.data.pop(old)
        # self.files[new] = self.files.pop(old)
        pass

    ##############################################

    def rmdir(self, path: str):
        # with multiple level support, need to raise ENOTEMPTY if contains any files
        # self.files.pop(path)
        # self.files['/']['st_nlink'] -= 1
        pass

    ##############################################

    def setxattr(self, path: str, name: str, value: str, options, position: int = 0):
        # Ignore options
        # attrs = self.files[path].setdefault('attrs', {})
        # attrs[name] = value
        pass

    ##############################################

    def statfs(self, path: str):
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)

    ##############################################

    def symlink(self, target: str, source: str):
        self.files[target] = dict(
            st_mode=(S_IFLNK | 0o777),
            st_nlink=1,
            st_size=len(source),
        )
        self.data[target] = source

    ##############################################

    def truncate(self, path: str, length: int, fh: int = None) -> None:
        # make sure extending the file fills in zero bytes
        # self.data[path] = self.data[path][:length].ljust(length, '\x00'.encode('ascii'))
        # self.files[path]['st_size'] = length
        pass

    ##############################################

    def unlink(self, path: str) -> None:
        self.data.pop(path)
        self.files.pop(path)

    ##############################################

    def utimens(self, path: str, times=None):
        # now = time()
        # atime, mtime = times if times else (now, now)
        # self.files[path]['st_atime'] = atime
        # self.files[path]['st_mtime'] = mtime
        pass

    ##############################################

    def write(self, path: str, data: bytes, offset: int, fh: int) -> int:
        # Write can be incomplete !!!
        print('write', path, offset, fh, data)
        if path.startswith('.'):
            self.data[path] = (
                # make sure the data gets inserted at the right offset
                self.data[path][:offset].ljust(
                    offset,
                    '\x00'.encode('ascii'))
                    + data
                    # and only overwrites the bytes that data is replacing
                    + self.data[path][offset + len(data):]
            )
            self.files[path]['st_size'] = len(self.data[path])
            return len(data)
        # else:
        elif 'test' in path.lower():
            print('write on wiki', path)
            if offset == 0:
                data = data.decode('utf8')
                page = Page.import_(data, self._api)
                page.update()
            return len(data)
