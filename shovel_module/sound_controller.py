'''音声操作モジュール


'''

from pydub import AudioSegment
from pydub.utils import ratio_to_db

def convert_volume(path:str,volume:int):
  '''音量調整
  
  path: ファイルのパス
  volume: 音量の倍率
  '''
  base_sound = AudioSegment.from_file(path,format="wav")
  new_sound = base_sound + ratio_to_db(float(volume))
  new_sound.export(path,format="wav")

def mp3_to_wav(path:str):
  '''mp3 → wav変換
  
  path: ファイルのパス
  '''
  sound = AudioSegment.from_mp3(f"{path}.mp3")
  sound.export(f"{path}.wav",format="wav")