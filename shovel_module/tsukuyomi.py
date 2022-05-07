import requests
from . import sound_controller
from . import config

address = config.SERVER["tsukuyomi"]

class vroid:
  def __init__(self,actor):
    self.actor = actor
  
  def generate(self,text,speed,pitch,path):
    with requests.Session() as session:
      s = session.get(f"{address}generate?text={text}&speed={speed}&pitch={pitch}")
      with open(path+".wav",mode="wb") as f:
        f.write(s.content)
    #sound_controller.convert_volume(path+".wav",0.7)