'''
jtalk 音声生成
'''

import subprocess
import os

def jtalk(t,voice,n):
    open_jtalk=['open_jtalk']
    mech=['-x','/var/lib/mecab/dic/open-jtalk/naist-jdic']
    htsvoice=['-m','/usr/share/hts-voice/mei/mei_'+voice+'.htsvoice']
    speed=['-r','1.5']
    jm=['-jm','1.0']
    outwav=['-ow',n+'.wav']
    cmd=open_jtalk+mech+htsvoice+speed+jm+outwav
    c = subprocess.Popen(cmd,stdin=subprocess.PIPE)
    c.stdin.write(t.encode())
    c.stdin.close()
    c.wait()
