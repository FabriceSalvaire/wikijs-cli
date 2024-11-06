API_KEY='eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MywiZW1haWwiOiJ2cHMtdXNlckBmYWJyaWNlLXNhbHZhaXJlLmZyIiwibmFtZSI6IkZhYnJpY2UiLCJhdiI6bnVsbCwidHoiOiJFdXJvcGUvUGFyaXMiLCJsYyI6ImVuIiwiZGYiOiIiLCJhcCI6IiIsInBlcm1pc3Npb25zIjpbInJlYWQ6cGFnZXMiLCJyZWFkOmFzc2V0cyIsInJlYWQ6Y29tbWVudHMiLCJ3cml0ZTpjb21tZW50cyIsIm1hbmFnZTpzeXN0ZW0iXSwiZ3JvdXBzIjpbMywxXSwiaWF0IjoxNzMwOTAwMjA1LCJleHAiOjE3MzA5MDIwMDUsImF1ZCI6InVybjp3aWtpLmpzIiwiaXNzIjoidXJuOndpa2kuanMifQ.nCdpEO544G5SLa1vk3ZBj9qYeiq-GgkxG54parXBVVLR0h-HzSeboghFVJxpmXnpK1EjIIp1kJ9jHRw0BHrUlpHMUN1QfVO2gGpiM0hN4FnjfB-MDJr29B6ozL_5xvQ2g4yB4Z0c-Z2lGX60WBLNYbBESIHpHHAk9g3aMK836TjxCyAuzLRTx7uOieAOIkmift9DHmAk9xFjdJsVNNaqdCJMZ9b558W1hPCEljy5_oSiT_OFoY6b4A1lvi6uJ6HwKZGtCZqUHt-YVyCKZaMQaUs2dHAXMh24fEbDOBbpjVIo_Mzicpt4uqT4EwX8I8TKp9_xe6lVu0zEckG1a9YpPg'

curl \
  'https://wiki.fabrice-salvaire.fr/graphql' \
  -X POST \
  -H "Authorization: Bearer ${API_KEY}" \
  -H 'content-type: application/json' \
  --data-raw '{"operationName":null, "variables":{}, "query":"{pages {list(orderBy: TITLE) {id path title}}}"}'

# --compressed
# -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0' \
# -H 'Accept: */*' \
# -H 'Accept-Language: fr,fr-FR;q=0.8,en;q=0.5,en-US;q=0.3' \
# -H 'Accept-Encoding: gzip, deflate, br, zstd' \
# -H 'Referer: https://wiki.fabrice-salvaire.fr/graphql' \
# -H 'Origin: https://wiki.fabrice-salvaire.fr' \
# -H 'Connection: keep-alive' \
# -H 'Sec-Fetch-Dest: empty' \
# -H 'Sec-Fetch-Mode: cors' \
# -H 'Sec-Fetch-Site: same-origin' \
# -H 'Priority: u=0' \
# -H 'Pragma: no-cache' \
# -H 'Cache-Control: no-cache' \
