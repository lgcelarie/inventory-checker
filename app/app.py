from io import StringIO
import gzip, json, os
from urllib.parse import urlencode
import urllib.request, urllib.error
from bs4 import BeautifulSoup

user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
headers = {'User-Agent': user_agent}
webhook_url = os.getenv('WEBHOOK_URL') or "http://fake.org"

def discord_notify(data):
    payload = {
        'content': data
    }
    payload = json.dumps(payload).encode('utf-8')
    req_notificacion = urllib.request.Request(url=webhook_url,data=payload,headers={'User-Agent': user_agent, 'Content-Type':'application/json'})
    res_notification = urllib.request.urlopen(req_notificacion,data=payload)
    print(res_notification.read())

def lambda_handler(event, context):
    data = urlencode({"selectedClub-clubpicker":6072}).encode()
    items = []
    with open('items.json') as items_file:
        items = json.loads(items_file.read())
    print(items)
    # items = [
    #     {
    #         'item': 'Arena para gatos',
    #         'url':'https://www.pricesmart.com/site/sv/es/pagina-producto/4057?_hn:type=action&_hn:ref=r193_r9'
    #     }
    # ]
    for item in items:
        print(f"{item['url']} and item:{item['item']}")
        req = urllib.request.Request(url=item['url'],data=data,headers=headers)
        try:
            page = urllib.request.urlopen(req,data=data)
        except urllib.error.URLError as e:
            print(f"Item **{item['item']}**: Error en URL")
            discord_notify(f"Item **{item['item']}**: Error en URL")
            continue
        gzipped = page.info().get('Content-Encoding') == 'gzip'

        if gzipped:
            buf  = StringIO(page.read())
            f = gzip.GzipFile(fileobj = buf)
            data = f.read()
        else:
            data = page

        soup = BeautifulSoup(data,features="html.parser")

        section = soup.select('li:-soup-contains("Los Héroes")')

        if not 'fa-times' in section[0].p.i['class']:
            print(f"Item **{item['item']}**: Disponible")
            discord_notify(f"Item **{item['item']}**: Disponible")
        else:
            f"Item **{item['item']}**: Agotado"
