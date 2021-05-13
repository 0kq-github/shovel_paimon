import os
import datetime
import asyncio
import time
import discord
import re
import sys
from discord.ext import commands
import configparser
import urllib.request
import json

from shovel_module import jtalk
from shovel_module import dict
from shovel_module import downloader
from shovel_module import sound_controller
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor

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

bot = commands.Bot(command_prefix=prefix)
config = configparser.ConfigParser()
config.read('./config.ini')
BOT_TOKEN = config.get(mode.upper(),'BOT_TOKEN')
config.clear
tpe = ThreadPoolExecutor


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
  os.makedirs("./config/guild/" + str(guild_id) + "/wav",exist_ok=True)
  with open("./config/guild/" + str(guild_id) + "/" + "dict.csv","w") as f:
    f.write("")
  config_path = './config/guild/' + str(guild_id) + "/" + 'config.ini'
  shutil.copy("./config/guild/default/config.ini",config_path)

def send_voice(message, path, volume):
  while message.guild.voice_client.is_playing():
    time.sleep(0.1)
  while os.path.isfile(path) == False:
    time.sleep(0.1)
  wav_source = discord.FFmpegPCMAudio(path, before_options="-guess_layout_max 0")
  wav_source_half = discord.PCMVolumeTransformer(wav_source, volume=volume)
  message.guild.voice_client.play(wav_source_half)


@bot.event
async def on_ready():
    print('------')
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print(lang["hello"])
    print('------')
    await bot.change_presence(activity=discord.Game(name=f"{prefix}sh0 help | {len(bot.guilds)}サーバーで稼働中"))

@bot.event
async def on_guild_join(guild):
    print("joined " + str(guild.id))
    await bot.change_presence(activity=discord.Game(name=f"{prefix}sh0 help | {len(bot.guilds)}サーバーで稼働中"))
    initdirs(guild.id)

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
    if before.channel == None:
      return
    try:
      #VC退出ログ
      voicech = bot.get_channel(id=before.channel.id)
      voicemember = voicech.members
      print(f"[{datime_now}][{voicech.guild.name}] {str(member)} が {before.channel.name} から退出しました")
      #VC退出処理
      if len(voicemember) == 1:
        for user in voicemember:
          if user.id == bot.user.id:
            await voicech.guild.voice_client.disconnect()
            shutil.rmtree("./config/guild/" + str(voicech.guild.id) + "/wav/")
            langs = lang["auto.disconnect"]
            fields = langs["field"]
            embed = discord.Embed(title=langs["title"],color=discord.Colour.blue(),description=langs["description"])
            embed.add_field(name=fields["0"]["name"],value=fields["0"]["value"],inline=fields["0"]["inline"])
            embed.add_field(name=fields["1"]["name"],value=fields["1"]["value"],inline=fields["1"]["inline"])
            config_path = './config/guild/' + str(voicech.guild.id) + "/" + 'config.ini'
            config.read(config_path)
            read_channel = config[mode.upper()]['CHANNEL']
            readch = bot.get_channel(id=int(read_channel))
            await readch.send(embed=embed)
            config[mode.upper()]['ENABLE'] = 'FALSE'
            with open(config_path, 'w') as f:
              config.write(f)
              config.clear
              f.close()
            config.clear
    except Exception as e:
      print(e)
      return


@bot.event
async def on_message(message):
  if message.author.bot:
    return
  config_path = './config/guild/' + str(message.guild.id) + "/" + 'config.ini'
  if not os.path.exists(config_path):
    initdirs(message.guild.id)
  config.read(config_path, encoding='utf-8')
  read_channel = config[mode.upper()]['CHANNEL']
  if not message.content.startswith(f'{prefix}sh0'):
    if (
      config[mode.upper()]['ENABLE'] == 'TRUE' and
      message.channel.id == int(read_channel) and
      message.guild.voice_client is not None
      ):
      play = tpe(max_workers=1)
      if os.path.exists(f"./global_wav/{message.content}.mp3"):
        play.submit(send_voice, message, f"./global_wav/{message.content}.mp3", 0.1)
        return
      if os.path.exists(f"./global_wav/{message.content}.wav"):
        play.submit(send_voice, message, f"./global_wav/{message.content}.wav", 0.1)
        return
      if "http" in message.content:
        message.content = re.sub("(?<=http).*$","",message.content)
        message.content = message.content.replace("http","。URL省略")
      if "<@" in message.content:
        mention = re.search("<@!..................>", message.content).group()
        mention = mention.replace("<@!","")
        mention = mention.replace(">","")
        mention_user = bot.fetch_user(int(mention))
        mention = mention_user.display_name
        message.content = re.sub("<@!..................>", "@" + mention, message.content)
      if "<#" in message.content:
        mention_channel = re.search("<#..................>", message.content).group()
        mention_channel = mention_channel.replace("<#","")
        mention_channel = mention_channel.replace(">","")
        mention_channel = await bot.get_channel(id=int(mention_channel)).name
        message.content = re.sub("<#..................>", mention_channel + "。", message.content)
      message.content = message.content.replace("\n","。")
      if len(message.content) > 50:
        message.content = truncate(message.content, 50)
      if message.author.nick is None:
        message_read = message.author.name + "。" + message.content
      else:
        message_read = message.author.nick + "。" + message.content
      message_read = re.sub("www+","わらわら",message_read,0)
      message_read = dict.dict(message.guild.id,message_read)
      datime_now = datetime.datetime.now().strftime('%Y/%m/%d-%H:%M:%S')
      print(f"[{datime_now}][{message.guild.name}] {message.author.name}: {message.content} -> {message_read}")
      datime = datetime.datetime.now().strftime('%Y-%m-%d_%H_%M_%S_%f')
      make = threading.Thread(target=make_wav,args=(message.guild.id, message_read, "normal", datime,))
      make.start()
      path_wav = f"./config/guild/{str(message.guild.id)}/wav/{datime}.wav"
      play.submit(send_voice, message, path_wav, 0.7)
  config.clear()
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
  embed.add_field(name=fields["0"]["name"],value=fields["0"]["value"],inline=fields["0"]["inline"])
  embed.add_field(name=fields["1"]["name"],value=fields["1"]["value"],inline=fields["1"]["inline"])
  embed.add_field(name=fields["2"]["name"],value=fields["2"]["value"],inline=fields["2"]["inline"])
  embed.add_field(name=fields["3"]["name"],value=fields["3"]["value"],inline=fields["3"]["inline"])
  embed.add_field(name=fields["4"]["name"],value=fields["4"]["value"],inline=fields["4"]["inline"])
  embed.add_field(name=fields["5"]["name"],value=fields["5"]["value"],inline=fields["5"]["inline"])
  embed.add_field(name=fields["6"]["name"],value=fields["6"]["value"],inline=fields["6"]["inline"])
  embed.add_field(name=fields["7"]["name"],value=fields["7"]["value"],inline=fields["7"]["inline"])
  embed.add_field(name=fields["8"]["name"],value=fields["8"]["value"],inline=fields["8"]["inline"])
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
  config_path = './config/guild/' + str(ctx.guild.id) + "/" + 'config.ini'
  config.read(config_path)
  if config[mode.upper()]['ENABLE'] == 'TRUE':
    langs = lang["s.already"]
    embed = discord.Embed(title=langs["title"],color=discord.Colour.red(),description=langs["description"])
    await ctx.channel.send(embed=embed)
    config.clear
    return
  await ctx.author.voice.channel.connect()
  os.makedirs(f"./config/guild/{str(ctx.guild.id)}/wav",exist_ok=True)
  os.makedirs(f"./config/guild/{str(ctx.guild.id)}/temp",exist_ok=True)
  langs = lang["s.connect"]
  fields = langs["field"]
  embed = discord.Embed(title=langs["title"],color=discord.Colour.blue(),description=langs["description"])
  embed.add_field(name=fields["0"]["name"],value=fields["0"]["value"] + ctx.channel.mention,inline=fields["0"]["inline"])
  embed.add_field(name=fields["1"]["name"],value=fields["1"]["value"] + ctx.author.voice.channel.name,inline=fields["1"]["inline"])
  await ctx.channel.send(embed=embed)
  config_path = './config/guild/' + str(ctx.guild.id) + "/" + 'config.ini'
  config.read(config_path)
  config[mode.upper()]['CHANNEL'] = str(ctx.channel.id)
  config[mode.upper()]['ENABLE'] = 'TRUE'
  with open(config_path, 'w') as f:
    config.write(f)
    config.clear
    f.close()

@sh0.command()
async def e(ctx,*args):
  '''
  読み上げ終了コマンド
  '''
  config_path = './config/guild/' + str(ctx.guild.id) + "/" + 'config.ini'
  config.read(config_path, encoding='utf-8')
  if ctx.channel.id == int(config[mode.upper()]['CHANNEL']):
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
    langs = lang["e.disconnect"]
    fields = langs["field"]
    embed = discord.Embed(title=langs["title"],color=discord.Colour.blue(),description=langs["description"])
    embed.add_field(name=fields["0"]["name"],value=fields["0"]["value"],inline=fields["0"]["inline"])
    embed.add_field(name=fields["1"]["name"],value=fields["1"]["value"],inline=fields["1"]["inline"])
    await ctx.channel.send(embed=embed)
    config.read(config_path)
    config[mode.upper()]['ENABLE'] = 'FALSE'
    with open(config_path, 'w') as f:
      config.write(f)
      config.clear
      f.close()
  config.clear


@sh0.command()
async def fe(ctx,*args):
  '''
  強制終了コマンド
  '''
  config_path = './config/guild/' + str(ctx.guild.id) + "/" + 'config.ini'
  config.read(config_path, encoding='utf-8')
  if ctx.channel.id == int(config[mode.upper()]['CHANNEL']):
    try:
      await ctx.guild.voice_client.disconnect()
      shutil.rmtree("./config/guild/" + str(ctx.guild.id) + "/wav/")
    except:
      None
    finally:
      langs = lang["fe.disconnect"]
      fields = langs["field"]
      embed = discord.Embed(title=langs["title"],color=discord.Colour.orange(),description=langs["description"])
      embed.add_field(name=fields["0"]["name"],value=fields["0"]["value"],inline=fields["0"]["inline"])
      embed.add_field(name=fields["1"]["name"],value=fields["1"]["value"],inline=fields["1"]["inline"])
      await ctx.channel.send(embed=embed)
      config.read(config_path)
      config[mode.upper()]['ENABLE'] = 'FALSE'
      with open(config_path, 'w') as f:
        config.write(f)
        config.clear
        f.close()
    config.clear



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
  if not ctx.author.id == 262132823895441409 and ctx.author.guild_permissions.administrator:
    return
  '''
  音声登録コマンド
  '''
  try:
    volume = args[0]
  except:
    volume = 1.0
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
async def init(ctx):
  '''
  初期化コマンド
  '''
  if ctx.author.id == 262132823895441409:
    initdirs(ctx.guild.id)
    await ctx.send(lang["init"]["title"])



try:  
    bot.loop.run_until_complete(bot.start(BOT_TOKEN)) 
except KeyboardInterrupt: 
    print('\nClosing %s...' % bot.user.name)
    bot.loop.run_until_complete(bot.close())