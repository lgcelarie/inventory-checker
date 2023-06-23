from io import StringIO
import gzip, json, os, boto3, logging
from urllib.parse import urlencode
import urllib.request, urllib.error
from bs4 import BeautifulSoup

user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
headers = {'User-Agent': user_agent}
club_webhook_url = os.getenv('WEBHOOK_URL',"http://fake.org")
market_webhook_url = os.getenv('WEBHOOK_URL',"http://fake.org")
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

'''
Funcion encargada de notificar al canal de discord correspondiente, dependiendo del tipo de item.
'''
def discord_notify(data,webhook_url):
    payload = {
        'content': data
    }
    payload = json.dumps(payload).encode('utf-8')
    if os.getenv('TEST_ENV', False):
        req_notificacion = urllib.request.Request(url=webhook_url,data=payload,headers={'User-Agent': user_agent, 'Content-Type':'application/json'})
        res_notification = urllib.request.urlopen(req_notificacion,data=payload)
        logger.info(res_notification.read())
    else:
        logger.info(payload)

'''
Funcion que prepara los headers correspondientes para los 2 tipos de items, club y market
Devuelve el diccionario a ser usado con el request.
'''
def get_headers(item):
    req_headers = headers
    if item['type'] == 'market':
        req_headers.update({'Cookie':f"sucursalSelectos={item['sucursal']}"})
    return req_headers

'''
Funcion que verifica el item en caso de ser perteneciente a un supermercado.
Recibe el item y la "sopa" para procesamiento. Por el momento solamente ejecuta comparacion de precios.
TODO: implementar tipos de analisis adicionales, como verificacion de promocion 2x1
'''
def check_market(item, soup):
    section = soup.select('div.descripcion')
    # logger.info(section)
    precio = soup.select("div.descripcion > div.numeros > p.precio span")
    logger.info(f"Precio: {precio[0].string.replace('$','')}")
    if float(precio[0].string.replace('$','')) < item['price']:
        logger.info("exito en comparacion")
        discord_notify(f"Item **{item['item']}**: Disponible", market_webhook_url)
    else:
        logger.info()

'''
Funcion que verifica la existencia de un producto en un club de compras especifico
'''
def check_club(item, soup):
    section = soup.select('li:-soup-contains("Los Héroes")')

    if not 'fa-times' in section[0].p.i['class']:
        logger.info(f"Item **{item['item']}**: Disponible")
        if os.getenv("TEST_ENV", False):
            discord_notify(f"Item **{item['item']}**: Disponible",club_webhook_url)
    else:
        logger.info(f"Item **{item['item']}**: Agotado")

'''
Funcion que obtiene los items a procesar, dependiendo del entorno:
    S3 para produccion
    local para desarrollo
Devuelve los items en un diccionario
'''
def get_items():
    file_content = None
    if os.getenv("TEST_ENV", False):
        with open('items.json', 'r') as f:
            file_content = f.read()
    else:
        s3_client = boto3.client("s3")
        file_content = s3_client.get_object(Bucket=os.getenv('S3_BUCKET_ARN'), Key="items.json")["Body"].read()

    if file_content:
        items = json.loads(file_content)
    else:
        items = []

    return items

def lambda_handler(event, context):
    data = urlencode({"selectedClub-clubpicker":6072}).encode()
    items = get_items()

    for item in items:
        if item['enabled'] is False:
            logger.info(f"Item {item['item']} esta deshabilitado. Omitiendo validacion...")
            continue
        logger.info(f"{item['url']} and item:{item['item']}")
        req = urllib.request.Request(url=item['url'],data=data,headers=get_headers(item))
        try:
            page = urllib.request.urlopen(req,data=data)
        except urllib.error.URLError as e:
            logger.warning(f"Item **{item['item']}**: Error en URL")
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

        if item['type'] == 'market':
            check_market(item,soup)
        else:
            check_club(item,soup)
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Productos procesados exitosamente'})
    }