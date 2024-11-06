####################################################################################################

import json
import pprint
from dataclasses import dataclass

import requests

####################################################################################################

API_URL = f'https://wiki.fabrice-salvaire.fr/graphql'
API_KEY = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MywiZW1haWwiOiJ2cHMtdXNlckBmYWJyaWNlLXNhbHZhaXJlLmZyIiwibmFtZSI6IkZhYnJpY2UiLCJhdiI6bnVsbCwidHoiOiJFdXJvcGUvUGFyaXMiLCJsYyI6ImVuIiwiZGYiOiIiLCJhcCI6IiIsInBlcm1pc3Npb25zIjpbInJlYWQ6cGFnZXMiLCJyZWFkOmFzc2V0cyIsInJlYWQ6Y29tbWVudHMiLCJ3cml0ZTpjb21tZW50cyIsIm1hbmFnZTpzeXN0ZW0iXSwiZ3JvdXBzIjpbMywxXSwiaWF0IjoxNzMwOTAwMjA1LCJleHAiOjE3MzA5MDIwMDUsImF1ZCI6InVybjp3aWtpLmpzIiwiaXNzIjoidXJuOndpa2kuanMifQ.nCdpEO544G5SLa1vk3ZBj9qYeiq-GgkxG54parXBVVLR0h-HzSeboghFVJxpmXnpK1EjIIp1kJ9jHRw0BHrUlpHMUN1QfVO2gGpiM0hN4FnjfB-MDJr29B6ozL_5xvQ2g4yB4Z0c-Z2lGX60WBLNYbBESIHpHHAk9g3aMK836TjxCyAuzLRTx7uOieAOIkmift9DHmAk9xFjdJsVNNaqdCJMZ9b558W1hPCEljy5_oSiT_OFoY6b4A1lvi6uJ6HwKZGtCZqUHt-YVyCKZaMQaUs2dHAXMh24fEbDOBbpjVIo_Mzicpt4uqT4EwX8I8TKp9_xe6lVu0zEckG1a9YpPg'


HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    # 'content-type': 'application/json',
}

####################################################################################################

def xpath(data: dict, path: str) -> dict:
    d = data
    for _ in path.split('/'):
        d = d[_]
    return d

####################################################################################################

def query_wikijs(query: str) -> dict:
    response = requests.post(API_URL, json={'query': query}, headers=HEADERS)
    data = response.json()
    if 'errors' in data:
        pprint.pprint(data)
        raise NameError
    else:
        return data

####################################################################################################

@dataclass
class Page:
    id: int
    path: str
    # hash: str
    title: str
    # description: str
    # isPrivate: bool
    # isPublished: bool
    # privateNS: str
    # publishStartDate: Date
    # publishEndDate: Date
    # tags: [PageTag]
    content: str = None
    # render: str
    # toc: str
    # contentType: str
    # createdAt: Date
    # updatedAt: Date
    # editor: str
    # locale: str
    # scriptCss: str
    # scriptJs: str
    # authorId: int
    # authorName: str
    # authorEmail: str
    # creatorId: int
    # creatorName: str
    # creatorEmail: str

####################################################################################################

# json_query = '{"operationName":null, "variables":{}, "query":"{pages {list(orderBy: TITLE) {id path title}}}"}'

# r = requests.post(API_URL, data=json_query, headers=HEADERS)
# print(r.content)

# Query > PageQuery > PageListItem
query = """
{
  pages {
    list (orderBy: TITLE) {
      id
      path
      title
    }
  }
}
"""
data = query_wikijs(query)
# {'data': {'pages': {'list': [{'id': 51,
#                               'path': 'Vera/a-apporter',
#                               'title': 'À apporter'},
pages = [Page(**page) for page in xpath(data, 'data/pages/list')]
for page in sorted(pages, key=lambda p: p.path):
    if page.path.startswith('home/bricolage/'):
        print()
        print(page.path)
        print(f"  {page.title}")
    #print(f"  {page.id}")
    # query = '{pages {single (id: %s) {content}}}' % (page.id)
    # data = query_wikijs(query)
    # print(data)
