
import sys
if sys.version_info.minor < 8:
  print("Python3.8以上が必要です")
  exit()

import os
import datetime
import asyncio
import time
import discord
import re
from discord.ext import commands
import configparser
import urllib.request
import json
import shutil
import threading

from shovel_module import jtalk
from shovel_module import dict
from shovel_module import downloader
from shovel_module import sound_controller


try:
  if sys.argv[1] == "--mode":
    if sys.argv[2] == "hutao":
      mode = "hutao"
      prefix = "?"
    elif sys.argv[2] == "paimon":
      mode = "paimon"
      prefix = "!"
    else:
     print(f" {sys.argv[2]} というモードはありません")
     exit()
  else:
    print(f" {sys.argv[1]} という引数はありません")
    print(" コマンド一覧")
    print(" --mode  動作モード選択")
    print("  hutao  胡桃")
    print("  paimon パイモン")
    exit()
except:
  if len(sys.argv) == 1:
    print(" 引数が必要です")
  exit()

bot = commands.Bot(command_prefix=prefix,help_command=None)
config = configparser.ConfigParser()
config.read('./config.ini')
BOT_TOKEN = config.get(mode.upper(),'BOT_TOKEN')
config.clear
#messagequeue = {message.guild.id:[[message,path,volume],[message,path,volume]]}
#reading = {message.guild.id:読み上げチャンネルのID}
global messagequeue
global reading
messagequeue = {}
reading = {}


lang = {}
with open(f"./{mode}.json",mode="r") as f:
  lang = json.load(f)

def make_wav(id, word_wav, voice, datime):
  path_wav = f"./config/guild/{str(id)}/temp/{datime}"
  jtalk.jtalk(word_wav,voice,path_wav)
  shutil.copy(f"{path_wav}.wav",f"./config/guild/{str(id)}/wav/")



def truncate(string, length, ellipsis='、以下省略'):
    '''文字列を切り詰める

    string: 対象の文字列
    length: 切り詰め後の長さ
    ellipsis: 省略記号
    '''
    return string[:length] + (ellipsis if string[length:] else '')

def initdirs(guild_id):
  os.makedirs(f"./config/guild/{str(guild_id)}/wav",exist_ok=True)

def send_voice(message, path, volume, bass):
  while message.guild.voice_client.is_playing():
    time.sleep(0.1)
  while os.path.isfile(path) == False:
    time.sleep(0.1)
  wav_source = discord.FFmpegPCMAudio(path, before_options="-guess_layout_max 0",options=f"-af equalizer=f=200:t=h:w=200:g={bass}")
  wav_source_half = discord.PCMVolumeTransformer(wav_source, volume=volume)
  message.guild.voice_client.play(wav_source_half)

def voice_loop(ctx):
  messagequeue[ctx.guild.id] = []
  while reading[ctx.guild.id] is not None:
    try:
      if ctx.guild.voice_client.is_playing():
        time.sleep(0.1)
        continue
    except:
      continue
    queuelist = messagequeue[ctx.guild.id]
    try:
      queue = queuelist.pop(0)
    except:
      time.sleep(0.1)
      continue
    send_voice(queue[0],queue[1],queue[2],queue[3])

async def replace_message(message):
  if "<@" in message.content:
    mention = re.search("<@[!]?\d{18}>", message.content).group()
    mention = mention.replace("<@!","")
    mention = mention.replace("<@","")
    mention = mention.replace(">","")
    mention_user = await bot.fetch_user(int(mention))
    mention = mention_user.display_name
    message.content = re.sub("<@[!]?\d{18}>", "@" + mention, message.content)
  if "<#" in message.content:
    mention_channel = re.search("<#\d{18}>", message.content).group()
    mention_channel = mention_channel.replace("<#","")
    mention_channel = mention_channel.replace(">","")
    mention_channel = bot.get_channel(id=int(mention_channel))
    mention = mention_channel.name
    message.content = re.sub("<#\d{18}>", mention + "。", message.content)
  emoji = re.findall("<.?:[^<^>]*:\d{18}>", message.content)
  if emoji:
    for i in emoji:
      emoji = re.search(":[^:]*:", i).group()
      message.content = message.content.replace(i,emoji)
  #message.content = re.sub("(https?):\/\/[\w-]+(\.[\w-]+)+([\w.,@?^=%&amp;:\/~+#\-\(]*[\w@?^=%&amp;\/~+#\-\)])?","URL省略",message.content)
  message.content = re.sub("(https?):\/\/[^(\s　)]+","URL省略",message.content)
  message.content = message.content.replace("\n","。")
  message.content = message.content.replace("{","[")
  message.content = message.content.replace("}","]")
  if len(message.content) >= 60:
    message.content = truncate(message.content, 50)
  if message.author.nick is None:
    message_read = f"{message.author.name}。{message.content}"
  else:
    message_read = f"{message.author.nick}。{message.content}"
  if "%" in message_read:
    if "%time" in message_read:
      message_time = datetime.datetime.now().strftime('%H時%M分%S秒')
      message_time = re.sub("(?<!\d)0","",message_time)
      message_read = message_read.replace("%time", message_time)
    if "%date" in message_read:
      #message_date = datetime.datetime.now().strftime('%Y年%m月%d日')
      d = datetime.date.today()
      message_date = f"{d.year}年{d.month}月{d.day}日"
      message_read = message_read.replace("%date", message_date)
    if "%me" in message_read:
      message_me = message.author.name
      message_read = message_read.replace("%me", message_me)
    else:
      message_read = message_read.replace("%","ぱーせんと")
  message_read = re.sub("ww+","わらわら",message_read,0)
  message_read = dict.dict(message.guild.id,message_read)
  return message_read


@bot.event
async def on_ready():
    print('------')
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print(lang["hello"])
    print('------')
    await bot.change_presence(activity=discord.Game(name=f"{prefix}sh0 help | {len(bot.guilds)}サーバーで稼働中"))
    if not os.path.exists("./config/config.json"):
      with open("./config/config.json","w") as f:
        cf = {0:False}
        f.write(json.dumps(cf))
    with open("./config/config.json","r") as f:
      global voice_config
      voice_config = json.load(f)
      print(voice_config)
    for i in bot.guilds:
      reading[i.id] = None
      try:
        if voice_config[i.id]["voice"] == True:
          continue
      except KeyError:
        voice_config[i.id] = {"voice":False}




@bot.event
async def on_guild_join(guild):
    print("joined " + str(guild.id))
    await bot.change_presence(activity=discord.Game(name=f"{prefix}sh0 help | {len(bot.guilds)}サーバーで稼働中"))
    initdirs(guild.id)
    with open(f"./config/guild/{str(guild.id)}/dict.csv","w") as f:
      f.write("")

@bot.event
async def on_voice_state_update(member,before,after):
  try:
    if before.channel.id == after.channel.id:
      return
  except Exception:
    None
  datime_now = datetime.datetime.now().strftime('%Y/%m/%d-%H:%M:%S')
  #自動切断
  try:
    #VC入室ログ
    voicech = bot.get_channel(id=after.channel.id)
    print(f"[{datime_now}][{voicech.guild.name}] {str(member)} が {after.channel.name} に参加しました")
  except Exception:
    None
  finally:
    if before.channel is None:
      return
    try:
      #VC退出ログ
      voicech = await bot.fetch_channel(before.channel.id)
      voicemember = voicech.members
      print(f"[{datime_now}][{voicech.guild.name}] {str(member)} が {before.channel.name} から退出しました")
      #VC退出処理
      if len(voicemember) == 1:
        for user in voicemember:
          if user.id == bot.user.id:
            await voicech.guild.voice_client.disconnect()
            shutil.rmtree(f"./config/guild/{str(voicech.guild.id)}/wav/")
            shutil.rmtree(f"./config/guild/{str(voicech.guild.id)}/temp/")
            langs = lang["auto.disconnect"]
            fields = langs["field"]
            embed = discord.Embed(title=langs["title"],color=discord.Colour.blue(),description=langs["description"])
            embed.add_field(name=fields["0"]["name"],value=fields["0"]["value"],inline=fields["0"]["inline"])
            embed.add_field(name=fields["1"]["name"],value=fields["1"]["value"],inline=fields["1"]["inline"])
            read_channel = reading[voicech.guild.id]
            readch = bot.get_channel(id=int(read_channel))
            await readch.send(embed=embed)
            reading[voicech.guild.id] = None
    except Exception as e:
      print(e)
      return


@bot.event
async def on_message(message):
  if message.author.bot:
    return
  message.content = str(message.content)
  try:
    read_channel = reading[message.guild.id]
    basslevel = 1
  except Exception:
    initdirs(message.guild.id)
    return
  if not message.content.startswith(f'{prefix}sh0'):
    if not message.content.startswith("!!"):
      if (
        read_channel is not None and
        message.channel.id == read_channel and
        message.guild.voice_client is not None
        ):
        datime_now = datetime.datetime.now().strftime('%Y/%m/%d-%H:%M:%S')
        if voice_config[message.guild.id]["voice"]:
          if os.path.exists(f"./global_wav/{message.content}.mp3"):
            print(f"[{datime_now}][{message.guild.name}] {message.author.name}: {message.content}")
            queuelist = messagequeue[message.guild.id]
            queuelist.append([message,f"./global_wav/{message.content}.mp3",0.1,basslevel])
            messagequeue[message.guild.id] = queuelist
            return
          if os.path.exists(f"./global_wav/{message.content}.wav"):
            print(f"[{datime_now}][{message.guild.name}] {message.author.name}: {message.content}")
            queuelist = messagequeue[message.guild.id]
            queuelist.append([message,f"./global_wav/{message.content}.wav",0.1,basslevel])
            messagequeue[message.guild.id] = queuelist
            return
        message_read = await replace_message(message)
        print(f"[{datime_now}][{message.guild.name}] {message.author.name}: {message.content} -> {message_read}")
        datime = datetime.datetime.now().strftime('%Y-%m-%d_%H_%M_%S_%f')
        make = threading.Thread(target=make_wav,args=(message.guild.id, message_read, "normal", datime,))
        make.start()
        path_wav = f"./config/guild/{str(message.guild.id)}/wav/{datime}.wav"
        queuelist = messagequeue[message.guild.id]
        queuelist.append([message,path_wav,0.7,0])
        messagequeue[message.guild.id] = queuelist
  await bot.process_commands(message)


@bot.group()
async def sh0(ctx):
  '''
  メイン
  '''
  if ctx.invoked_subcommand is None:
    langs = lang["unknown"]
    embed = discord.Embed(title=langs["title"],color=discord.Colour.red(),description=langs["description"])
    await ctx.send(embed=embed)

@sh0.command()
async def help(ctx,*args):
  '''
  helpコマンド
  '''
  langs = lang["help"]
  fields = langs["field"]
  embed = discord.Embed(title=langs["title"],color=discord.Colour.blue(),description=langs["description"])
  i = 0
  while i <= 8:
    embed.add_field(name=fields[i]["name"],value=fields[i]["value"],inline=fields[i]["inline"])
    i += 1
  await ctx.send(embed=embed)

@sh0.command()
async def s(ctx,*args):
  '''
  読み上げ開始コマンド
  '''
  if ctx.author.voice is None:
    langs = lang["s.notfound"]
    fields = langs["field"]
    embed = discord.Embed(title=langs["title"],color=discord.Colour.orange(),description=langs["description"])
    embed.add_field(name=fields["0"]["name"],value=fields["0"]["value"],inline=fields["0"]["inline"])
    await ctx.channel.send(embed=embed)
    return
  if reading[ctx.guild.id] is not None:
    langs = lang["s.already"]
    embed = discord.Embed(title=langs["title"],color=discord.Colour.red(),description=langs["description"])
    await ctx.channel.send(embed=embed)
    return
  await ctx.author.voice.channel.connect()
  os.makedirs(f"./config/guild/{str(ctx.guild.id)}/wav",exist_ok=True)
  os.makedirs(f"./config/guild/{str(ctx.guild.id)}/temp",exist_ok=True)
  msgloop = threading.Thread(target=voice_loop,args=(ctx,))
  langs = lang["s.connect"]
  fields = langs["field"]
  embed = discord.Embed(title=langs["title"],color=discord.Colour.blue(),description=langs["description"])
  embed.add_field(name=fields["0"]["name"],value=fields["0"]["value"] + ctx.channel.mention,inline=fields["0"]["inline"])
  embed.add_field(name=fields["1"]["name"],value=fields["1"]["value"] + ctx.author.voice.channel.name,inline=fields["1"]["inline"])
  await ctx.channel.send(embed=embed)
  reading[ctx.guild.id] = ctx.channel.id
  msgloop.start()

@sh0.command()
async def e(ctx,*args):
  '''
  読み上げ終了コマンド
  '''
  if ctx.channel.id == reading[ctx.guild.id]:
    if ctx.guild.voice_client is None:
      langs = lang["e.notfound"]
      fields = langs["field"]
      embed = discord.Embed(title=langs["title"],color=discord.Colour.orange(),description=langs["description"])
      embed.add_field(name=fields["0"]["name"],value=fields["0"]["value"],inline=fields["0"]["inline"])
      await ctx.channel.send(embed=embed)
      return
    await ctx.guild.voice_client.disconnect()
    shutil.rmtree(f"./config/guild/{str(ctx.guild.id)}/wav/")
    shutil.rmtree(f"./config/guild/{str(ctx.guild.id)}/temp/")
    try:
      del messagequeue[ctx.guild.id]
    except:
      pass
    langs = lang["e.disconnect"]
    fields = langs["field"]
    embed = discord.Embed(title=langs["title"],color=discord.Colour.blue(),description=langs["description"])
    embed.add_field(name=fields["0"]["name"],value=fields["0"]["value"],inline=fields["0"]["inline"])
    embed.add_field(name=fields["1"]["name"],value=fields["1"]["value"],inline=fields["1"]["inline"])
    await ctx.channel.send(embed=embed)
    reading[ctx.guild.id] = None


@sh0.command()
async def fe(ctx,*args):
  '''
  強制終了コマンド
  '''
  try:
    await ctx.guild.voice_client.disconnect()
    shutil.rmtree(f"./config/guild/{str(ctx.guild.id)}/wav/",ignore_errors=True)
    del messagequeue[ctx.guild.id]
  except:
    None
  finally:
    reading[ctx.guild.id] = None
    initdirs(ctx.guild.id)
    langs = lang["fe.disconnect"]
    fields = langs["field"]
    embed = discord.Embed(title=langs["title"],color=discord.Colour.orange(),description=langs["description"])
    embed.add_field(name=fields["0"]["name"],value=fields["0"]["value"],inline=fields["0"]["inline"])
    embed.add_field(name=fields["1"]["name"],value=fields["1"]["value"],inline=fields["1"]["inline"])
    await ctx.channel.send(embed=embed)



@sh0.command()
async def aw(ctx,*args):
  '''
  辞書追加コマンド
  '''
  if len(args) != 2:
    langs = lang["aw.unknown"]
    embed = discord.Embed(title=langs["title"],color=discord.Colour.red(),description=langs["description"])
    await ctx.send(embed=embed)
    return
  u_dict = {}
  u_dict = dict.reader(ctx.guild.id)
  u_dict[args[0]] = args[1]
  dict.writer(ctx.guild.id,u_dict)
  langs = lang["aw.success"]
  fields = langs["field"]
  embed = discord.Embed(title=langs["title"],color=discord.Colour.blue(),description=langs["description"])
  embed = embed.add_field(name=fields["0"]["name"],value=fields["0"]["value"] + args[0],inline=fields["0"]["inline"])
  embed = embed.add_field(name=fields["1"]["name"],value=fields["1"]["value"] + args[1],inline=fields["1"]["inline"])
  await ctx.send(embed=embed)

@sh0.command()
async def dw(ctx,*args):
  '''
  辞書削除コマンド
  '''
  if len(args) != 1:
    langs = lang["dw.wrong"]
    embed = discord.Embed(title=langs["title"],color=discord.Colour.red(),description=langs["description"])
    await ctx.send(embed=embed)
    return
  u_dict = {}
  u_dict = dict.reader(ctx.guild.id)
  try:
    u_dict.pop(args[0])
  except:
    langs = lang["dw.unknown"]
    embed = discord.Embed(title=langs["title"],color=discord.Colour.red(),description=langs["description"])
    await ctx.send(embed=embed)
    return
  dict.writer(ctx.guild.id, u_dict)
  langs = lang["dw.success"]
  fields = langs["field"]
  embed = discord.Embed(title=langs["title"],color=discord.Colour.blue(),description=langs["description"])
  embed = embed.add_field(name=fields["0"]["name"],value=fields["0"]["value"] + args[0],inline=fields["0"]["inline"])
  await ctx.send(embed=embed)


@sh0.command()
async def link(ctx,*args):
  '''
  音声登録コマンド
  '''
  volume = args[0] or 1.0
  if not ctx.message.attachments:
    langs = lang["link.notfound"]
    embed = discord.Embed(title=langs["title"],color=discord.Colour.red(),description=langs["description"])
    await ctx.send(embed=embed)
    return
  url = ctx.message.attachments[0].url
  filename = ctx.message.attachments[0].filename
  path = "./global_wav/" + filename
  if os.path.exists(path):
    downloader.download(url,path)
    sound_controller.convert_volume(path,volume)
    langs = lang["link.update"]
    embed = discord.Embed(title=langs["title"],color=discord.Colour.blue(),description=langs["description"])
    await ctx.send(embed=embed)
    return
  await asyncio.sleep(0.1)
  downloader.download(url,path)
  sound_controller.convert_volume(path,volume)
  langs = lang["link.success"]
  embed = discord.Embed(title=langs["title"],color=discord.Colour.blue(),description=langs["description"])
  await ctx.send(embed=embed)

@sh0.command()
async def show(ctx):
  '''
  音声一覧表示コマンド
  '''
  path = "./global_wav/"
  filelist = os.listdir(path=path)
  filecount = len(filelist)
  files = ""
  count = 1
  for i in filelist:
    if count <= 30:
      i = i[:-4]
      files += i + ","
    if count >= 31:
      langs = lang["show"]
      fields = langs["field"]
      embed = discord.Embed(title=langs["title"],color=discord.Colour.blue())
      embed.add_field(name=fields["name"] + str(filecount),value=fields["value"] + files)
      await ctx.send(embed=embed)
      embed.clear_fields
      files = ""
      count = 0
    count += 1
  if count <= 31:
    langs = lang["show"]
    fields = langs["field"]
    embed = discord.Embed(title=langs["title"],color=discord.Colour.blue())
    embed.add_field(name=fields["name"] + str(filecount),value=fields["value"] + files)
    await ctx.send(embed=embed)

@sh0.command()
async def import_word(ctx,*args):
  '''
  辞書インポートコマンド
  '''
  if not ctx.message.attachments:
    langs = lang["import_word.notfound"]
    embed = discord.Embed(title=langs["title"],color=discord.Colour.red(),description=langs["description"])
    await ctx.send(embed=embed)
    return
  url = ctx.message.attachments[0].url
  filename = ctx.message.attachments[0].filename
  path = "./config/guild/" + str(ctx.guild.id) + "/" + filename
  header = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0"}
  request = urllib.request.Request(url=url,headers=header)
  with urllib.request.urlopen(request) as web_file, open(path,'wb') as local_file:
    local_file.write(web_file.read())
  os.rename(path, "./config/guild/" + str(ctx.guild.id) + "/dict.csv")
  langs = lang["import_word.success"]
  embed = discord.Embed(title=langs["title"],color=discord.Color.blue(),description=langs["description"])
  await ctx.send(embed=embed)

@sh0.command()
async def export_word(ctx,*args):
  '''
  辞書エクスポートコマンド
  '''
  langs = lang["export_word"]
  embed = discord.Embed(title=langs["title"],color=discord.Colour.blue(),description=langs["description"])
  await ctx.send(embed=embed)
  dictpath = "./config/guild/" + str(ctx.guild.id) + "/" + "dict.csv"
  await ctx.send(file=discord.File(dictpath))

@sh0.command()
async def bass(ctx,*args):
  '''
  低音強化コマンド
  '''
  langs = lang["bass"]
  fields = langs["field"]
  if args[0]:
    basslevel = args[0]
  else:
    basslevel = 0
  basslevel = 0
  embed = discord.Embed(title=langs["title"],color=discord.Colour.blue(),description=langs["description"])
  embed = embed.add_field(name=fields["0"]["name"],value=f"{basslevel}dB",inline=fields["0"]["inline"])
  #await ctx.send(embed=embed)
  await ctx.send("現在低音強化機能は無効化されています")

@sh0.command()
async def init(ctx):
  '''
  初期化コマンド(使用不可)
  '''
  if ctx.author.id == 262132823895441409:
    initdirs(ctx.guild.id)
    await ctx.send(lang["init"]["title"])

@sh0.command()
async def v(ctx, *args):
  if not args:
    await ctx.send("引数が足りなリよ！")
  if args[0] == "on":
    voice_config[ctx.guild.id] = {"voice":True}
    langs = lang["voice.on"]
    embed = discord.Embed(title=langs["title"],description=langs["description"],color=discord.Colour.blue())
    await ctx.send(embed=embed)
  else:
    voice_config[ctx.guild.id] = {"voice":False}
    langs = lang["voice.off"]
    embed = discord.Embed(title=langs["title"],description=langs["description"],color=discord.Colour.blue())
    await ctx.send(embed=embed)


try:  
    bot.loop.run_until_complete(bot.start(BOT_TOKEN)) 
except KeyboardInterrupt: 
    print('\nClosing %s...' % bot.user.name)
    for i in reading:
      shutil.rmtree(f"./config/guild/{i}/wav/",ignore_errors=True)
      reading[i] = None
      initdirs(i)
    with open("./config/config.json","w") as f:
      config_json = json.dumps(voice_config)
      f.write(config_json)
      f.close()
    bot.loop.run_until_complete(bot.close())