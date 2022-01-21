import hmac
import requests
import hashlib
import json
from datetime import datetime, timezone

def generate(accesskey,access_secret,coefont,text,path):
  date: str = str(int(datetime.utcnow().replace(tzinfo=timezone.utc).timestamp()))
  data: str = json.dumps({
    'coefont': coefont,
    'text': text
  })
  signature = hmac.new(bytes(access_secret, 'utf-8'), (date+data).encode('utf-8'), hashlib.sha256).hexdigest()

  response = requests.post('https://api.coefont.cloud/v1/text2speech', data=data, headers={
    'Content-Type': 'application/json',
    'Authorization': accesskey,
    'X-Coefont-Date': date,
    'X-Coefont-Content': signature
  })

  if response.status_code == 200:
    with open(f'{path}.wav', 'wb') as f:
      f.write(response.content)
  else:
    print(response.json())
