from io import StringIO
import gzip, json, os, boto3, logging
from urllib.parse import urlencode
import urllib.request, urllib.error
from bs4 import BeautifulSoup

user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
headers = {'User-Agent': user_agent}
webhook_url = os.getenv('WEBHOOK_URL',"http://fake.org")
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

def discord_notify(data):
    payload = {
        'content': data
    }
    payload = json.dumps(payload).encode('utf-8')
    req_notificacion = urllib.request.Request(url=webhook_url,data=payload,headers={'User-Agent': user_agent, 'Content-Type':'application/json'})
    res_notification = urllib.request.urlopen(req_notificacion,data=payload)
    logger.info(res_notification.read())

def lambda_handler(event, context):
    data = urlencode({"selectedClub-clubpicker":6072}).encode()
    s3_client = boto3.client("s3")
    file_content = s3_client.get_object(Bucket=os.getenv('S3_BUCKET_ARN'), Key="items.json")["Body"].read()
    if file_content:
        items = json.loads(file_content)
    else:
        items = []

    print(items)

    for item in items:
        print(f"{item['url']} and item:{item['item']}")
        req = urllib.request.Request(url=item['url'],data=data,headers=headers)
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

        section = soup.select('li:-soup-contains("Los Héroes")')

        if not 'fa-times' in section[0].p.i['class']:
            logger.info(f"Item **{item['item']}**: Disponible")
            discord_notify(f"Item **{item['item']}**: Disponible")
        else:
            logger.info(f"Item **{item['item']}**: Agotado")
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Productos procesados exitosamente'})
    }