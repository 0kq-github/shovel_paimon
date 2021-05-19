import urllib
import time

def download(url:str,path:str):
  '''ファイルのダウンロード

  url: ファイルのurl
  path: 保存先
  '''
  print("音声登録")
  print("url:" + url)
  print("path:" + path)
  header = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0"}
  request = urllib.request.Request(url=url,headers=header)
  with urllib.request.urlopen(request) as web_file, open(path,'wb') as local_file:
      local_file.write(web_file.read())
  time.sleep(1)