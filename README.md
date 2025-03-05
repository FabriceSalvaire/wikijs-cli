# A CLI for Wiki.js

This repo contains a CLI written in Python (1) for [Wiki.js](https://js.wiki).
(1) because I master Python

For some reason free software Wiki implementations are a bit complicated...
In the past, I used the MoinMoin Wiki but MoinMoin2 was never stable.
Then I used Redmine Wiki but it is not well suited for smartphone and this component is not the most maintained.
Then I discovered Wiki.js and its modern look-and-feel.
But later I realised that in fact it was not ready for production and shows several issues.
Wiki.js was developed by only one person, that implemented successively three versions, but none was ever completed.  Some users call it a vaporware.  Maybe too much people expect free support for such a tool.
Despite this situation, Wiki.js features a GraphQL API which permits to interact with the server.

This CLI is just a tool to leverage the current implementation (Wiki.js 2).
It features:
- commands to list pages, assets, ...
- a disk export (with network transparency)
- a Git export and sync
  I was unable to use this feature of Wiki.js.
- a check tool
  for example, to check for dangling links
- to dump a page to disk
- to update a page from disk
  for example, to edit the page using a true editor (Emacs) and perform spell checking
  I have issues with Firefox WithExEditor and LanguageTool extensions and ckeditor
- to create a page from disk
- to move pages

Actual Wiki.js limitations:
- A deleted page is really deleted and disappear of the history.
  This is weird behaviour and this feature should not be used.
  Instead to delete, move the page in a dedicated trash folder.
- Some asset management functions are not implemented.
