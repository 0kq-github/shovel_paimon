import os

def stk2dic(stk:str):
  '''
  '''
  dictlist = []
  with open(stk,mode="r",encoding="utf-16") as f:
    for i in f.readlines():
      i = i.replace(",","")
      _in = i.split(" ")
      _in = [_in[0],_in[1]]
      dictlist.append(_in)
  return dictlist

def dic2csv(dic:list,path:str):
  '''  
  '''
  if os.path.exists(path):
    mode="a"
  else:
    mode="w"
  with open(path,mode=mode,encoding="utf-16") as f:
    for d in dic:
      f.write(",".join(d).rstrip("\n")+"\n")
