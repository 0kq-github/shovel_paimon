'''
jtalk 音声生成
'''

import subprocess
import os
import urllib.request
import tarfile

if not os.path.exists("./jtalk_dic/open_jtalk_dic_utf_8-1.07"):
    os.makedirs("./jtalk_dic",exist_ok=True)
    request = urllib.request.Request(url="http://sourceforge.net/projects/open-jtalk/files/Dictionary/open_jtalk_dic-1.07/open_jtalk_dic_utf_8-1.07.tar.gz")
    with urllib.request.urlopen(request) as web_file, open("./jtalk_dic/open_jtalk_dic.tar.gz",'wb') as local_file:
        local_file.write(web_file.read())
    with tarfile.open("./jtalk_dic/open_jtalk_dic.tar.gz",mode="r") as t:
        t.extractall("./jtalk_dic/")

def jtalk(t,voice,n):
    open_jtalk=['open_jtalk']
    mech=['-x','./jtalk_dic/open_jtalk_dic_utf_8-1.07']
    htsvoice=['-m','/usr/share/hts-voice/mei/mei_'+voice+'.htsvoice']
    #htsvoice=['-m','./voice/miku.htsvoice']
    speed=['-r','1.5']
    jm=['-jm','1.0']
    outwav=['-ow',n+'.wav']
    cmd=open_jtalk+mech+htsvoice+speed+jm+outwav
    c = subprocess.Popen(cmd,stdin=subprocess.PIPE)
    c.stdin.write(t.encode())
    c.stdin.close()
    c.wait()
