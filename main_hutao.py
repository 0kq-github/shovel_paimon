import os
import datetime
import asyncio
import time
import discord
import re
from discord import voice_client
from discord.channel import VoiceChannel
from discord.ext import commands
import configparser
import urllib.request
from pydub import AudioSegment
from pydub.utils import ratio_to_db
import json
from shovel_module import jtalk
from shovel_module import dict
from shovel_module import downloader
from shovel_module import sound_controller
import shutil


bot = commands.Bot(command_prefix='?')
config = configparser.ConfigParser()
config.read('./config.ini')
BOT_TOKEN = config.get('HUTAO','BOT_TOKEN')
config.clear

lang = {}
with open("./hutao.json",mode="r") as f:
  lang = json.load(f)

def make_wav(id, word_wav, voice):
  datime_now = datetime.datetime.now().strftime('%Y-%m-%d_%H_%M_%S')
  path_wav = "./config/guild/" + str(id) + "/wav/" + datime_now
  jtalk.jtalk(word_wav,voice,path_wav)
  while os.path.isfile(path_wav + '.wav') == False:
    time.sleep(0.1)
  path_wav = path_wav + '.wav'
  return path_wav


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

@bot.event
async def on_ready():
    print('------')
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print(lang["hello"])
    print('------')
    await bot.change_presence(activity=discord.Game(name=f"?sh0 help | {len(bot.guilds)}サーバーで稼働中"))

@bot.event
async def on_guild_join(guild):
    print("joined " + str(guild.id))
    await bot.change_presence(activity=discord.Game(name=f"?sh0 help | {len(bot.guilds)}サーバーで稼働中"))
    initdirs(guild.id)

@bot.event
async def on_voice_state_update(member,before,after):
  voicemember = VoiceChannel.voice_states
  print(voicemember)
  print(member)
  print(before)


@bot.event
async def on_message(message):
  if message.author.bot:
    return
  config_path = './config/guild/' + str(message.guild.id) + "/" + 'config.ini'
  if not os.path.exists(config_path):
    initdirs(message.guild.id)
  config.read(config_path, encoding='utf-8')
  read_channel = config['ID']['CHANNEL']
  if not message.content.startswith('?sh0'):
    if (
      config['READ']['ENABLE'] == 'TRUE' and
      message.channel.id == int(read_channel) and
      message.guild.voice_client is not None
      ):
      while message.guild.voice_client.is_playing():
        await asyncio.sleep(0.1)
      if os.path.exists("./global_wav/" + message.content + '.mp3'):
        sozai_wav = "./global_wav/" + message.content + '.mp3'
        sozai_source = discord.FFmpegPCMAudio(sozai_wav)
        sozai_source_half = discord.PCMVolumeTransformer(sozai_source, volume=0.1)
        message.guild.voice_client.play(sozai_source_half)
        return
      if os.path.exists("./global_wav/" + message.content + '.wav'):
        sozai_wav = "./global_wav/" + message.content + '.wav'
        sozai_source = discord.FFmpegPCMAudio(sozai_wav)
        sozai_source_half = discord.PCMVolumeTransformer(sozai_source, volume=0.1)
        message.guild.voice_client.play(sozai_source_half)
        return
      if "http" in message.content:
        message.content = re.sub("(?<=http).*$","",message.content)
        message.content = message.content.replace("http","。URL省略")
      #if "<:" in message.content:
      #  message.content = re.sub(":..................>", "", message.content)
      #  message.content = message.content.replace("<:","")
      if "<@" in message.content:
        mention = re.search("<@!..................>", message.content).group()
        mention = mention.replace("<@!","")
        mention = mention.replace(">","")
        mention = discord.Client.get_user(id=int(mention)).display_name
        message.content = re.sub("<@!..................>", "@" + mention, message.content)
      if "<#" in message.content:
        mention_channel = re.search("<#..................>", message.content).group()
        mention_channel = mention_channel.replace("<#","")
        mention_channel = mention_channel.replace(">","")
        mention_channel = discord.Client.get_channel(self=bot,id=int(mention_channel)).name
        message.content = re.sub("<#..................>", mention_channel + "。", message.content)
      message.content = message.content.replace("\n","。")
      if len(message.content) > 100:
        message.content = truncate(message.content, 100)
      if message.author.nick is None:
        message_read = message.author.name + "。" + message.content
      else:
        message_read = message.author.nick + "。" + message.content
      message_read = dict.dict(message.guild.id,message_read)
      print(str(message.guild.id) + ' ' + message_read)
      path_wav = make_wav(message.guild.id , message_read, voice="normal")
      source = discord.FFmpegPCMAudio(path_wav)
      source_half = discord.PCMVolumeTransformer(source, volume=0.7)
      message.guild.voice_client.play(source_half)
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
  if config['READ']['ENABLE'] == 'TRUE':
    langs = lang["s.already"]
    embed = discord.Embed(title=langs["title"],color=discord.Colour.red(),description=langs["description"])
    await ctx.channel.send(embed=embed)
    config.clear
    return
  await ctx.author.voice.channel.connect()
  os.makedirs("./config/guild/" + str(ctx.guild.id) + "/wav",exist_ok=True)
  langs = lang["s.connect"]
  fields = langs["field"]
  embed = discord.Embed(title=langs["title"],color=discord.Colour.blue(),description=langs["description"])
  embed.add_field(name=fields["0"]["name"],value=fields["0"]["value"] + ctx.channel.mention,inline=fields["0"]["inline"])
  embed.add_field(name=fields["1"]["name"],value=fields["1"]["value"] + ctx.author.voice.channel.name,inline=fields["1"]["inline"])
  await ctx.channel.send(embed=embed)
  config_path = './config/guild/' + str(ctx.guild.id) + "/" + 'config.ini'
  config.read(config_path)
  config['ID']['CHANNEL'] = str(ctx.channel.id)
  config['READ']['ENABLE'] = 'TRUE'
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
  if ctx.channel.id == int(config['ID']['CHANNEL']):
    if ctx.guild.voice_client is None:
      langs = lang["e.notfound"]
      fields = langs["field"]
      embed = discord.Embed(title=langs["title"],color=discord.Colour.orange(),description=langs["description"])
      embed.add_field(name=fields["0"]["name"],value=fields["0"]["value"],inline=fields["0"]["inline"])
      await ctx.channel.send(embed=embed)
      return
    await ctx.guild.voice_client.disconnect()
    shutil.rmtree("./config/guild/" + str(ctx.guild.id) + "/wav/")
    langs = lang["e.disconnect"]
    fields = langs["field"]
    embed = discord.Embed(title=langs["title"],color=discord.Colour.blue(),description=langs["description"])
    embed.add_field(name=fields["0"]["name"],value=fields["0"]["value"],inline=fields["0"]["inline"])
    embed.add_field(name=fields["1"]["name"],value=fields["1"]["value"],inline=fields["1"]["inline"])
    await ctx.channel.send(embed=embed)
    config.read(config_path)
    config['READ']['ENABLE'] = 'FALSE'
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
  if ctx.channel.id == int(config['ID']['CHANNEL']):
    try:
      await ctx.guild.voice_client.disconnect()
      shutil.rmtree("./config/guild/" + str(ctx.guild.id) + "/wav/")
    finally:
      langs = lang["fe.disconnect"]
      fields = langs["field"]
      embed = discord.Embed(title=langs["title"],color=discord.Colour.orange(),description=langs["description"])
      embed.add_field(name=fields["0"]["name"],value=fields["0"]["value"],inline=fields["0"]["inline"])
      embed.add_field(name=fields["1"]["name"],value=fields["1"]["value"],inline=fields["1"]["inline"])
      await ctx.channel.send(embed=embed)
      config.read(config_path)
      config['READ']['ENABLE'] = 'FALSE'
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
      files += i + "\n"
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