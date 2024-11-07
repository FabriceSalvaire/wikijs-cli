####################################################################################################

from WikiJsApi import Page, WikiJsApi

####################################################################################################

API_URL = 'https://wiki.fabrice-salvaire.fr/graphql'
# API_KEY = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MywiZW1haWwiOiJ2cHMtdXNlckBmYWJyaWNlLXNhbHZhaXJlLmZyIiwibmFtZSI6IkZhYnJpY2UiLCJhdiI6bnVsbCwidHoiOiJFdXJvcGUvUGFyaXMiLCJsYyI6ImVuIiwiZGYiOiIiLCJhcCI6IiIsInBlcm1pc3Npb25zIjpbInJlYWQ6cGFnZXMiLCJyZWFkOmFzc2V0cyIsInJlYWQ6Y29tbWVudHMiLCJ3cml0ZTpjb21tZW50cyIsIm1hbmFnZTpzeXN0ZW0iXSwiZ3JvdXBzIjpbMywxXSwiaWF0IjoxNzMwOTAwMjA1LCJleHAiOjE3MzA5MDIwMDUsImF1ZCI6InVybjp3aWtpLmpzIiwiaXNzIjoidXJuOndpa2kuanMifQ.nCdpEO544G5SLa1vk3ZBj9qYeiq-GgkxG54parXBVVLR0h-HzSeboghFVJxpmXnpK1EjIIp1kJ9jHRw0BHrUlpHMUN1QfVO2gGpiM0hN4FnjfB-MDJr29B6ozL_5xvQ2g4yB4Z0c-Z2lGX60WBLNYbBESIHpHHAk9g3aMK836TjxCyAuzLRTx7uOieAOIkmift9DHmAk9xFjdJsVNNaqdCJMZ9b558W1hPCEljy5_oSiT_OFoY6b4A1lvi6uJ6HwKZGtCZqUHt-YVyCKZaMQaUs2dHAXMh24fEbDOBbpjVIo_Mzicpt4uqT4EwX8I8TKp9_xe6lVu0zEckG1a9YpPg'
API_KEY = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcGkiOjMsImdycCI6MSwiaWF0IjoxNzMwOTMxNjE0LCJleHAiOjE4MjU2MDQ0MTQsImF1ZCI6InVybjp3aWtpLmpzIiwiaXNzIjoidXJuOndpa2kuanMifQ.lcyuLPURdqGdIq5bg0cC0aVg6zvqJaxo8g9aIRYcm3hhA284Y6m7Kp-OJrBqo-Sav_oFfw4ZlmLG9Ml-rkUNTyIJfCf84X-ICbml35KdYLTkeItCMOouwLR4cGnGyf_2buuVVqduv4oCeysmx0zML9q5P6Qr9dF4f8eZ2rWHJiZdRor1U2E2FzsuMpuClXAxogsXYD4sP4LAF3Ist4wvHRScok1qzw7qdIt-1Pzmz1sZyiB9EdQVagkZu7u09uAdRrk81At-C58zHiFKCcL67pmwMA_L2lVYF0pcvrmFLZgIE6f_q8BHLJ-uoM_60J4nFghhUrSZqsruW08wHng0LQ'

api = WikiJsApi(api_url=API_URL, api_key=API_KEY)

if True:
    for page in api.yield_pages():
        page.complete()
        print(f"{page.path:60} {page.title:40} {len(page.content):5} @{page.locale} {page.id:3} ")

        # if page.path.startswith('home/bricolage/'):
        # print()
        # print(f"{page.path} @{page.locale}")
        # print(f"  {page.title}")

        # print(f"  {page.id}")

        # print(page.content)

if False:
    page = api.page('home/bricolage/serrure-porte-garage')
    print()
    print(f"  {page.path} @{page.locale}")
    print(f"  {page.title}")
    print(f"  {page.id}")
    page.move('home/maison/serrure-porte-garage')

if False:
    for page in api.yield_pages():
        # for _ in ('portail',):
        # if page.path.lower().startswith('.../' + _):
        old_path = 'home/bricolage/documentation/'
        if page.path.startswith(old_path):
            dest = page.path.replace(old_path, 'home/Documentation/Bricolage/')
            print()
            print(f"  {page.path} -> {dest}")
            page.move(dest)
