import requests

class vroid():
  def __init__(self):
    ...
  
  def generate(self,text,speed,pitch,vrange,path):
    with requests.Session() as session:
      s = session.get(f"http://192.168.100.41:4090/api/v1/audiofile?text={text}&speed={speed}&pitch={pitch}&range={vrange}")
      with open(path+".wav",mode="wb") as f:
        f.write(s.content)