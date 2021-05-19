'''
辞書モジュール
'''

import csv

def dict(id, read_text):
  '''
  辞書変換
  '''
  u_dict = {}
  dict_path = "./config/guild/" + str(id) + "/" + "dict.csv"
  with open(dict_path,mode="r",encoding="utf-16") as f:
    u_dict = csv.reader(f)
    u_dict = {row[0]:row[1] for row in u_dict}
  read_list = [] # あとでまとめて変換するときの読み仮名リスト
  for i, one_dic in enumerate(u_dict.items()): # one_dicは単語と読みのタプル。添字はそれぞれ0と1。
      read_text = read_text.replace(one_dic[0], '{'+str(i)+'}')
      read_list.append(one_dic[1]) # 変換が発生した順に読みがなリストに追加

  read_text = read_text.format(*read_list) #読み仮名リストを引数にとる
  return read_text

def reader(id):
  '''
  読み込み用関数

  csv -> 辞書
  '''
  dict_path = "./config/guild/" + str(id) + "/" + "dict.csv"
  with open(dict_path,mode="r",encoding="utf-16") as f:
    u_dict = csv.reader(f)
    u_dict = {row[0]:row[1] for row in u_dict}
    return u_dict

def writer(id, u_dict):
  '''
  書き込み用関数

  辞書 -> csv
  '''
  dict_path = "./config/guild/" + str(id) + "/" + "dict.csv"
  with open(dict_path,mode="w",encoding="utf-16") as f:
    writer = csv.writer(f)
    for k, v in u_dict.items():
      writer.writerow([k,v])