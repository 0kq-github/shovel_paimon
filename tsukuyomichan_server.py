from tsukuyomichan_talksoft import TsukuyomichanTalksoft
#from tsukuyomichan_talksoft.tsukuyomichan_talksoft import TsukuyomichanTalksoft
import soundfile
from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
import io
from pitchshifter import pitchshifter

class tsukuyomi:
  def __init__(self):
    self.tsukuyomichan_talksoft = TsukuyomichanTalksoft(model_version='v.1.2.0')
    pass

  def generate(self,text):
    gacha = 0
    wav = self.tsukuyomichan_talksoft.generate_voice(text,gacha)
    return wav

class args:
  def __init__(self,speed,pitch,source):
    self.speed = speed
    self.pitch = pitch
    self.source = source
    self.out = source
    self.chunk_size = 4096
    self.overlap = .9
    self.blend = 1
    self.no_resample = False
    self.debug = False

app = FastAPI()

@app.get("/generate", response_class=FileResponse)
def generate(text:str,speed:float,pitch:float):
  wav = tsukuyomi().generate(text)
  with io.BytesIO() as bs:
    soundfile.write(bs,wav,24000,"PCM_16",format="wav")
    return Response(content=bs.getvalue(),media_type="audio/wav")


