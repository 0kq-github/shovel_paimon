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
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(t, "./jtalk_dic/")

def jtalk(t,voice,speed,pitch,path):
    open_jtalk=['open_jtalk']
    #mech=['-x','./jtalk_dic/open_jtalk_dic_utf_8-1.07']
    mech=['-x','./dict/naist-jdic']
    htsvoice=['-m','./voice/mei_'+voice+'.htsvoice']
    speed=['-r',str(speed)]
    pitch=["-fm",str(pitch)]
    jm=['-jm','1.0']
    outwav=['-ow',path+'.wav']
    cmd=open_jtalk+mech+htsvoice+speed+pitch+jm+outwav
    c = subprocess.Popen(cmd,stdin=subprocess.PIPE)
    c.stdin.write(t.encode())
    c.stdin.close()
    c.wait()
