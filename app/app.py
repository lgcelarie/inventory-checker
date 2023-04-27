from io import StringIO
import gzip, json, os
from urllib.parse import urlencode
import urllib.request, urllib.error
from bs4 import BeautifulSoup

user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
headers = {'User-Agent': user_agent}
webhook_url = os.environ['WEBHOOK_URL']

def discord_notify(data):
    payload = {
        'content': data
    }
    payload = json.dumps(payload).encode('utf-8')
    req_notificacion = urllib.request.Request(url=webhook_url,data=payload,headers={'User-Agent': user_agent, 'Content-Type':'application/json'})
    res_notification = urllib.request.urlopen(req_notificacion,data=payload)
    print(res_notification.read())


data = {
    'selectedClub-clubpicker' : 6702
}

items = [
    {
        'item': 'Arena para gatos',
        'url':'https://www.pricesmart.com/site/sv/es/pagina-producto/4057?_hn:type=action&_hn:ref=r193_r9'
    }
]
def lambda_handler(event, context):
    for item in items:
        req = urllib.request.Request(url=item['url'],headers=headers)
        try:
            page = urllib.request.urlopen(req,data=urlencode(data).encode())
        except urllib.error.URLError as e:
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

        if 'fa-times' in section[0].p.i['class']:
            discord_notify(f"Item **{item['item']}**: Disponible")
