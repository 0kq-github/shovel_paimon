import os
import datetime
import asyncio
import time
import discord
import re
from discord.ext import commands
import configparser
import urllib.request
from pydub import AudioSegment
from pydub.utils import ratio_to_db
import csv
from shovel_module import jtalk
from shovel_module import dict
from shovel_module import downloader
from shovel_module import sound_controller
import shutil

bot = commands.Bot(command_prefix='?')
config = configparser.ConfigParser()
config.read('./config.ini')
BOT_TOKEN = config.get('BOT','BOT_TOKEN')
config.clear

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
    print('------')
    await bot.change_presence(activity=discord.Game(name=f"?sh0 help | {len(bot.guilds)}サーバーで稼働中"))

@bot.event
async def on_guild_join(guild):
    print("joined " + str(guild.id))
    await bot.change_presence(activity=discord.Game(name=f"?sh0 help | {len(bot.guilds)}サーバーで稼働中"))
    initdirs(guild.id)

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
  if ctx.invoked_subcommand is None:
    embed = discord.Embed(title="コマンド",color=discord.Colour.red(),description="そんなコマンドは無いよ！")
    await ctx.send(embed=embed)

@sh0.command()
async def help(ctx,*args):
  embed = discord.Embed(title="コマンド",color=discord.Colour.blue(),description="こんなコマンドがあるよ！")
  embed.add_field(name="?sh0 s",value="おしゃべり開始！",inline=False)
  embed.add_field(name="?sh0 e",value="さいなら～",inline=False)
  embed.add_field(name="?sh0 link <音量倍率>",value="新しい音声を追加できるってよ！\nmp3ファイルを添付してね！",inline=False)
  embed.add_field(name="?sh0 show",value="どんな音声があるか教えてあげる！")
  await ctx.send(embed=embed)

@sh0.command()
async def s(ctx,*args):
  if ctx.author.voice is None:
    embed = discord.Embed(title="読み上げ",color=discord.Colour.orange(),description="あっれれ～？誰か呼んだ～？")
    embed.add_field(name="Tips",value="ボイスチャンネルに接続せずに読み上げを開始する機能はありません。",inline=False)
    await ctx.channel.send(embed=embed)
    return
  config_path = './config/guild/' + str(ctx.guild.id) + "/" + 'config.ini'
  config.read(config_path)
  if config['READ']['ENABLE'] == 'TRUE':
    embed = discord.Embed(title="読み上げ",color=discord.Colour.red(),description="おしゃべり中だよ！")
    await ctx.channel.send(embed=embed)
    config.clear
    return
  await ctx.author.voice.channel.connect()
  embed = discord.Embed(title="ボイスチャット接続",color=discord.Colour.blue(),description="ヤッホー！往生堂77代目、胡桃だよ！")
  embed.add_field(name="読み上げ対象",value=ctx.channel.mention)
  embed.add_field(name="読み上げボイスチャンネル",value=ctx.author.voice.channel.name)
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
  config_path = './config/guild/' + str(ctx.guild.id) + "/" + 'config.ini'
  config.read(config_path, encoding='utf-8')
  if ctx.channel.id == int(config['ID']['CHANNEL']):
    if ctx.guild.voice_client is None:
      await ctx.channel.send("ん～？誰か呼んだ～？")
      return
    await ctx.guild.voice_client.disconnect()
    embed = discord.Embed(title="ボイスチャット終了",color=discord.Colour.blue(),description="お疲れ様～ まったね～！")
    embed.add_field(name="ヒント",value="喋ってくれない時や、読み上げ終了後胡桃が帰らない場合は、?sh0 eで追い払ってください",inline=False)
    embed.add_field(name="各種リンク",value="[作者Twitter](https://twitter.com/_0kq_/)",inline=False)
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
    embed = discord.Embed(title="ユーザー辞書",color=discord.Colour.red(),description="それってどういう意味？")
    await ctx.send(embed=embed)
    return
  u_dict = {}
  u_dict = dict.reader(ctx.guild.id)
  u_dict[args[0]] = args[1]
  dict.writer(ctx.guild.id,u_dict)
  embed = discord.Embed(title="ユーザー辞書",color=discord.Colour.blue(),description="教えてくれてありがとう！旅人さん！")
  embed = embed.add_field(name="単語",value=args[0])
  embed = embed.add_field(name="読み",value=args[1])
  await ctx.send(embed=embed)

@sh0.command()
async def dw(ctx,*args):
  '''
  辞書削除コマンド
  '''
  if len(args) != 1:
    embed = discord.Embed(title="ユーザー辞書",color=discord.Colour.red(),description="なんか変じゃない？")
    await ctx.send(embed=embed)
    return
  u_dict = {}
  u_dict = dict.reader(ctx.guild.id)
  try:
    u_dict.pop(args[0])
  except:
    embed = discord.Embed(title="ユーザー辞書",color=discord.Colour.red(),description="そんな言葉知らないよ？")
    await ctx.send(embed=embed)
    return
  dict.writer(ctx.guild.id, u_dict)
  embed = discord.Embed(title="ユーザー辞書",color=discord.Colour.blue(),description="これってどんな意味だったっけ...")
  embed = embed.add_field(name="単語",value=args[0])
  await ctx.send(embed=embed)


@sh0.command()
async def link(ctx,*args):
  '''
  音声登録コマンド
  '''
  volume = 1.0
  if args:
    volume = args[0]
  if not ctx.message.attachments:
    embed = discord.Embed(title="音声登録",color=discord.Colour.red(),description="ファイルが無いよ！")
    await ctx.send(embed=embed)
    return
  url = ctx.message.attachments[0].url
  filename = ctx.message.attachments[0].filename
  path = "./global_wav/" + filename
  if os.path.exists(path):
    downloader.download(url,path)
    sound_controller.convert_volume(path,volume)
    embed = discord.Embed(title="音声登録",color=discord.Colour.blue(),description="やったー！更新できたー！")
    await ctx.send(embed=embed)
    return
  await asyncio.sleep(0.1)
  downloader.download(url,path)
  sound_controller.convert_volume(path,volume)
  embed = discord.Embed(title="音声登録",color=discord.Colour.blue(),description="ら～ら～ら～♪ 水煮魚にエビ蒸し餃子～")
  await ctx.send(embed=embed)

@sh0.command()
async def show(ctx):
  path = "./global_wav/"
  filelist = os.listdir(path=path)
  filecount = len(filelist)
  files = ""
  count = 1
  for i in filelist:
    if count <= 30:
      files += i + "\n"
    if count >= 31:
      embed = discord.Embed(title="音声一覧",color=discord.Colour.blue())
      embed.add_field(name="登録数 " + str(filecount),value=files)
      await ctx.send(embed=embed)
      embed.clear_fields
      files = ""
      count = 0
    count += 1
  if count <= 31:
    embed = discord.Embed(title="音声一覧",color=discord.Colour.blue())
    embed.add_field(name="登録数 " + str(filecount),value=files)
    await ctx.send(embed=embed)

@sh0.command()
async def import_word(ctx,*args):
  if not ctx.message.attachments:
    embed = discord.Embed(title="ユーザー辞書",color=discord.Colour.red(),description="ファイルが無いよ！")
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
  embed = discord.Embed(title="ユーザー辞書",color=discord.Color.blue(),description="インポート成功！初めて聞く言葉がたくさん！")
  await ctx.send(embed=embed)

@sh0.command()
async def init(ctx):
  initdirs(ctx.guild.id)
  await ctx.send("お掃除完了！")



try:  
    bot.loop.run_until_complete(bot.start(BOT_TOKEN)) 
except KeyboardInterrupt: 
    print('\nClosing %s...' % bot.user.name)
    bot.loop.run_until_complete(bot.close())