####################################################################################################
#
# wikijs-cli - A CLI for Wiki.js
# Copyright (C) 2025 Fabrice SALVAIRE
# SPDX-License-Identifier: GPL-3.0-or-later
#
####################################################################################################

INFO = '''
{
system {
  info {
    currentVersion
    latestVersion
    groupsTotal
    pagesTotal
    usersTotal
    tagsTotal
}}}
'''

PAGE = '''
query ($path: String!, $locale: String!) {
  pages {
    singleByPath(path: $path, locale: $locale) {
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
      authorId
      authorName
      creatorId
      creatorName
      tags {
        tag
      }
}}}
'''

# query ($limit: Int!, $orderBy: PageOrderBy!, $orderByDirection: PageOrderByDirection!) {
#     list(limit: $limit, orderBy: $orderBy, orderByDirection: $orderByDirection) {
def LIST_PAGE(order_by, order_by_direction):
    return f'''
query ($limit: Int!) {{
  pages {{
    list(
      limit: $limit,
      orderBy: {order_by},
      orderByDirection: {order_by_direction}
    ) {{
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
}}}}}}
'''

def LIST_PAGE_FOR_TAGS(order_by):
    return f'''
query ($tags: [String!], $limit: Int!) {{
  pages {{
    list(
      limit: $limit,
      orderBy: {order_by},
      tags: $tags
    ) {{
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
}}}}}}
'''

TREE = '''
query ($path: String!, $locale: String!) {
  pages {
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
'''

PAGE_HISTORY = '''
query ($id: Int!) {
  pages {
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
}}}
'''

LIST_ASSET_SUBFOLDER = '''
query ($parentFolderId: Int!) {
  assets {
    folders(parentFolderId: $parentFolderId) {
      id
      name
      slug
}}}
'''

LIST_ASSET = '''
query ($folderId: Int!, $kind: AssetKind!) {
  assets {
    list(folderId: $folderId, kind: $kind) {
      id
      filename
      ext
      kind
      mime
      fileSize
      metadata
      createdAt
      updatedAt
}}}
'''

PAGE_VERSION = '''
query ($id: Int!, $version_id: Int!) {
  pages {
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
}}}
'''

MOVE_PAGE = '''
mutation ($id: Int!, $destinationPath: String!, $destinationLocale: String!) {
  pages {
    move(id: $id, destinationPath: $destinationPath, destinationLocale: $destinationLocale) {
      responseResult {
        succeeded
        errorCode
        slug
        message
      }
}}}
'''

CREATE_PAGE = '''
mutation (
  $content: String!,
   $description: String!,
   $editor: String!,
   $isPrivate: Boolean!,
   $isPublished: Boolean!,
   $locale: String!,
   $path: String!,
   $publishEndDate: Date,
   $publishStartDate: Date,
   $scriptCss: String,
   $scriptJs: String,
   $tags: [String]!,
   $title: String!
) {
  pages {
    create(
      content: $content,
      description: $description,
      editor: $editor,
      isPrivate: $isPrivate,
      isPublished: $isPublished,
      locale: $locale,
      path: $path,
      publishEndDate: $publishEndDate,
      publishStartDate: $publishStartDate,
      scriptCss: $scriptCss,
      scriptJs: $scriptJs,
      tags: $tags,
      title: $title
    ) {
      responseResult {
        succeeded
        errorCode
        slug
        message
      }
      page {
        id
        updatedAt
      }
}}}
'''

UPDATED_PAGE = '''
mutation ($id: Int!,
   $content: String,
   $description: String,
   $editor: String,
   $isPrivate: Boolean,
   $isPublished: Boolean,
   $locale: String,
   $path: String,
   $publishEndDate: Date,
   $publishStartDate: Date,
   $scriptCss: String,
   $scriptJs: String,
   $tags: [String],
   $title: String) {
  pages {
    update(
      id: $id,
      content: $content,
      description: $description,
      editor: $editor,
      isPrivate: $isPrivate,
      isPublished: $isPublished,
      locale: $locale,
      path: $path,
      publishEndDate: $publishEndDate,
      publishStartDate: $publishStartDate,
      scriptCss: $scriptCss,
      scriptJs: $scriptJs,
      tags: $tags,
      title: $title
    ) {
      responseResult {
        succeeded
        errorCode
        slug
        message
      }
      page {
        updatedAt
      }
}}}
'''

PAGE_SEARCH = '''
query ($query: String!) {
  pages {
    search(query: $query) {
      results {
        id
        title
        description
        path
        locale
      }
      suggestions
      totalHits
}}}
'''

TAGS = '''
{
  pages {
    tags {
      id
      tag
      title
      createdAt
      updatedAt
}}}
'''

SEARCH_TAGS = '''
query ($query: String!) {
  pages {
    searchTags(query: $query)
}}
'''

LINKS = '''
query ($locale: String!) {
  pages {
    links(locale: $locale) {
      id
      path
      title
      links
}}}
'''
