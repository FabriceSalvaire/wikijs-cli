```
[{
"operationName":null,
"variables":{
  "id":219,
  "checkoutDate":"2024-11-16T21:23:59.106Z"
  },
"extensions":{},
"query":"
query ($id: Int!, $checkoutDate: Date!) {
  pages {
    checkConflicts(id: $id, checkoutDate: $checkoutDate)
    __typename
  }
}
"}]

[{
"operationName":null,
"variables":{
  "parentFolderId":16
  },
"extensions":{},
"query":"
query ($parentFolderId: Int!) {
  assets {
    folders(parentFolderId: $parentFolderId) {
      id
      name
      slug
      __typename
    }
    __typename
  }
}
"},
{
"operationName":null,
"variables":{
  "folderId":16,
  "kind":"ALL"
  },
"extensions":{},
"query":"
query ($folderId: Int!, $kind: AssetKind!) {
  assets {
    list(folderId: $folderId, kind: $kind) {
      id
      filename
      ext
      kind
      mime
      fileSize
      createdAt
      updatedAt
      __typename
    }
    __typename
  }
}
"}]
```

```
[{
"operationName":null,
"variables":{
  "folderId":16,"
  kind":"ALL"},
"extensions":{},
"query":
"query ($folderId: Int!, $kind: AssetKind!) {
  assets {
    list(folderId: $folderId, kind: $kind) {
      id
      filename
      ext
      kind
      mime
      fileSize
      createdAt
      updatedAt
      __typename
    }
    __typename
  }
}
"}]
```

```
curl 'https://wiki.fabrice-salvaire.fr/u' -X POST -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0' -H 'Accept: */*' -H 'Accept-Language: fr,fr-FR;q=0.8,en;q=0.5,en-US;q=0.3' -H 'Accept-Encoding: gzip, deflate, br, zstd' -H 'Referer: https://wiki.fabrice-salvaire.fr/e/fr/home/Maison/garage-houilles/serrure-porte-garage' -H 'Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MywiZW1haWwiOiJ2cHMtdXNlckBmYWJyaWNlLXNhbHZhaXJlLmZyIiwibmFtZSI6IkZhYnJpY2UiLCJhdiI6bnVsbCwidHoiOiJFdXJvcGUvUGFyaXMiLCJsYyI6ImVuIiwiZGYiOiIiLCJhcCI6IiIsInBlcm1pc3Npb25zIjpbInJlYWQ6cGFnZXMiLCJyZWFkOmFzc2V0cyIsInJlYWQ6Y29tbWVudHMiLCJ3cml0ZTpjb21tZW50cyIsIm1hbmFnZTpzeXN0ZW0iXSwiZ3JvdXBzIjpbMywxXSwiaWF0IjoxNzMxODUxMjI2LCJleHAiOjE3MzE4NTMwMjYsImF1ZCI6InVybjp3aWtpLmpzIiwiaXNzIjoidXJuOndpa2kuanMifQ.lq38nBMITep0Xq2cPtCKCBwrBXwCHiRG9-pAFV2vsKr13VvpxPciL3Nw9kzFa_wgK9B9g8rvpX_cLFzKFluldVddDHWVEBH1Pqt76v-ueUgEtdUFQsNaZvPeSA4dWBHkYmFQW9BHeNdja5YQJVL2Kf99hleE9ayDJj1T4Kxk2AeqE1Vf51spFT_loqkHaugKt52GR7vzOOtZ9EUKL-tdr2DxWrAvnmITB5fDCxlMFyHsOZ3f3v9DzAkyYIxyRRc0-bCv4IbxCocrqBmps6I-mxMx2vYl4--oC6JzWLgLxTbQTpPFd03ThP2OxlxE98B84GjmR0MwVLp960Tlp3M4Ww' -H 'Content-Type: multipart/form-data; boundary=---------------------------129231049024720573734240874905' -H 'Origin: https://wiki.fabrice-salvaire.fr' -H 'Connection: keep-alive' -H 'Cookie: jwt=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MywiZW1haWwiOiJ2cHMtdXNlckBmYWJyaWNlLXNhbHZhaXJlLmZyIiwibmFtZSI6IkZhYnJpY2UiLCJhdiI6bnVsbCwidHoiOiJFdXJvcGUvUGFyaXMiLCJsYyI6ImVuIiwiZGYiOiIiLCJhcCI6IiIsInBlcm1pc3Npb25zIjpbInJlYWQ6cGFnZXMiLCJyZWFkOmFzc2V0cyIsInJlYWQ6Y29tbWVudHMiLCJ3cml0ZTpjb21tZW50cyIsIm1hbmFnZTpzeXN0ZW0iXSwiZ3JvdXBzIjpbMywxXSwiaWF0IjoxNzMxODUxMjI2LCJleHAiOjE3MzE4NTMwMjYsImF1ZCI6InVybjp3aWtpLmpzIiwiaXNzIjoidXJuOndpa2kuanMifQ.lq38nBMITep0Xq2cPtCKCBwrBXwCHiRG9-pAFV2vsKr13VvpxPciL3Nw9kzFa_wgK9B9g8rvpX_cLFzKFluldVddDHWVEBH1Pqt76v-ueUgEtdUFQsNaZvPeSA4dWBHkYmFQW9BHeNdja5YQJVL2Kf99hleE9ayDJj1T4Kxk2AeqE1Vf51spFT_loqkHaugKt52GR7vzOOtZ9EUKL-tdr2DxWrAvnmITB5fDCxlMFyHsOZ3f3v9DzAkyYIxyRRc0-bCv4IbxCocrqBmps6I-mxMx2vYl4--oC6JzWLgLxTbQTpPFd03ThP2OxlxE98B84GjmR0MwVLp960Tlp3M4Ww' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: same-origin' -H 'Pragma: no-cache' -H 'Cache-Control: no-cache' --data-binary $'-----------------------------129231049024720573734240874905\r\nContent-Disposition: form-data; name="mediaUpload"\r\n\r\n{"folderId":16}\r\n-----------------------------129231049024720573734240874905\r\nContent-Disposition: form-data; name="mediaUpload"; filename="thirard-rideau-sans-cylindre-cotation.jpg"\r\nContent-Type: image/jpeg\r\n\r\n-----------------------------129231049024720573734240874905--\r\n'
```

```
-----------------------------420613337318117538631003107387
Content-Disposition: form-data; name="mediaUpload"

{"folderId":16}
-----------------------------420613337318117538631003107387
Content-Disposition: form-data; name="mediaUpload"; filename="thirard-rideau-sans-cylindre.jpg"
Content-Type: image/jpeg

ÿØÿà\u0\u10JFIF...\u11
-----------------------------420613337318117538631003107387--
```

```
[{'operationName':null,'variables':{'parent':3,'locale':'fr'},'extensions':{},'query':'query ($parent: Int, $locale: String!) {
  pages {
    tree(parent: $parent, mode: ALL, locale: $locale) {
      id
      path
      title
      isFolder
      pageId
      parent
      locale
      __typename
    }
    __typename
  }
}
'}]
```
