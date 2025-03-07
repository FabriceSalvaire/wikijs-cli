# A CLI for Wiki.js

This repo contains a CLI written in Python (1) for [Wiki.js](https://js.wiki).
(1) because I master Python

For some reason free software Wiki implementations are a bit complicated... </br>
In the past, I used the [MoinMoin](http://moinmo.in) Wiki but MoinMoin2 was never released as stable. </br>
Then I used [Redmine](https://www.redmine.org/projects/redmine/wiki/RedmineWikis) Wiki but it is not well suited for smartphone and this component is not the most maintained and it require an extension for dangling pages. </br>
Then I discovered Wiki.js and its modern look-and-feel. </br>
But later I realised that in fact it was not ready for production and shows several issues. </br>
Wiki.js was developed by only one person, that implemented successively three versions, but none was ever completed.  Some users call it a vaporware.  Maybe too much people expect free support for such a tool. </br>
Despite this situation, Wiki.js features a GraphQL API which permits to interact with the server.
Wiki.js client uses the Vue framework.


This CLI is just a tool to leverage the current implementation (Wiki.js 2).
It features these commands:
- commands to list pages, assets, ...
- a disk export (with network transparency)
- a Git export and sync

  I was unable to use this feature of Wiki.js.
- a check tool

  for example, to check for dangling links
- dump a page to disk
- update a page from disk

  for example, to edit the page using a true editor (Emacs) and perform spell checking
  I have issues with Firefox WithExEditor and LanguageTool extensions and ckeditor
- create a page from disk
- move pages


**Actual Wiki.js limitations:**
- A deleted page is really deleted and disappear of the history !

  This is weird behaviour and this feature should not be used.
  Instead to delete, move the page in a dedicated trash folder.
- Some asset management functions are not implemented !

  We can only upload, rename, delete and asset, and create folders.
  We cannot move an asset.
  Workaround is to download, delete, and upload.
- Page creation

  There are multiple ways to create a new pages:
  From the New Page button.
  By clicking a link pointing to a non-existing page.
  Manually type the path in the browser address bar.

  It means the path must be absolute.
  We cannot simply create a page relative to a parent page !
  Thus, contrary to every wiki, we cannot just add a link `[[MyNewWikiPage]]` to the page you want to create.
  However, the drawback of this common approach, is to have to deal with dangling pages.
  Redmine requires an extension to show those pages else...

  Usually, it is cumbersome to create a page and organize things in Wiki.js !
  We have to perform a lot of clicks and to type a path and a title etc.
  We have to define a slug for the page path.
- Folder Hierarchy

  A page does not have a parent but an absolute path from witch the folder hierarchy is inferred.
  We have to create a folder page, to customize the folder title.
  If we want to move a node of the folder hierarchy, then we have to move each page manually one by one (i.e. rename the path).
  This is ridiculously inefficient !

**Curated documentation links:**
- [Pages | Wiki.js](https://docs.requarks.io/guide/pages)
- [Build Process | Wiki.js](https://docs.requarks.io/dev/build-process)


**Curated Javascript Library links:**
- [Knex.js — SQL Query Builder for Javascript](https://knexjs.org)
- [Objection.js — ORM for Node.js](https://vincit.github.io/objection.js/)
- [Apollo GraphQL](https://www.apollographql.com/)
- [Cheerio — Javascript library for parsing and manipulating HTML and XML](https://cheerio.js.org)


**Curated source code links:**
- `dev/build/DockerFile` Yarn commands to build

   It could be the developer is working on Windows VsCode.
   Thus there is any process to build from the Linux command line.
   see also `dev/webpack`
- `server/models`
- `server/db/migrations` hand written DB migrations

  `2.0.0.js` is root DB creation
  I suspect all migrations are executed for a new wiki instance.
  See [sql - create table from model in objection.js - Stack Overflow](https://stackoverflow.com/questions/59627328/create-table-from-model-in-objection-js)
  > Objection does not support any ways to create migrations from models. You need to write migration files to create schema and then write Models that matches DB schema...
- `server/graph/resolvers` GraphQL API

  see also `server/graph/schemas
-`server/jobs`

  task to render page
-`server/modules/storage` storage plugins
