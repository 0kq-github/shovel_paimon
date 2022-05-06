import requests
from . import sound_controller

class vroid:
  def __init__(self,actor):
    self.actor = actor
  
  def generate(self,text,speed,pitch,vrange,path):
    with requests.Session() as session:
      s = session.get(f"http://192.168.100.41:4090/api/v1/audiofile?text={text}&speed={speed}&pitch={pitch}&range={vrange}")
      with open(path+".wav",mode="wb") as f:
        f.write(s.content)
    sound_controller.convert_volume(path+".wav",0.5)
    sound_controller.mp3_to_wav(path)