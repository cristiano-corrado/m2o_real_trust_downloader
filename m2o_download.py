#!/usr/bin/python
import datetime
import os
import re
import sqlite3
import ssl
import sys
import urllib
from hashlib import sha256
from http import cookiejar
import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC

counter=0
URL="https://www.m2o.it/programmi/real-trust/puntate/"
DBName="m2o"


# Sqlite connector
conn = sqlite3.connect(DBName+'.sqlite3',check_same_thread=False)
c=conn.cursor()

# urllib2 configuration


ctx = ssl._create_unverified_context() #ssl.create_default_context(cafile="myca.pem")#,capath="/Users/cristiano/PycharmProjects/m2o_downloader/")
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

cj = cookiejar.CookieJar()

proxy_handler=urllib.request.ProxyHandler({
    'http':'proxy:3128',
    'https':'proxy:3128'
})
opener = urllib.request.build_opener(urllib.request.BaseHandler(), urllib.request.HTTPCookieProcessor(cj),proxy_handler,urllib.request.HTTPSHandler(context=ctx))

opener.addheaders = [('User-agent',
                                  'Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.133 Mobile Safari/535.19')]

urllib.request.install_opener(opener)

def checkdb(DB):
    ex=c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=\'"+DB+"\'");
    if ex.fetchone() == None :
        c.execute("CREATE TABLE m2o(datedown,songnum,filename,page,filesize,url,hash)")
        print("Creating DB structure, table name: "+DB)
    else:
        print("DB exists and in path. Downloading songs...")
    return True

def gatherFilename(urlname,titlename):

    URLNAME=urlname.split("/")[-1]

    if not re.findall(r"real|realmovie|realbook|realtrust|trust",URLNAME):

        numBlack=re.compile("^[0-9]")

        if "_" in URLNAME :
            URLNAME=URLNAME.split("_")
        else:
            URLNAME=URLNAME.split(".mp3")

        monBlack=re.compile(r"^gen$|^feb$|^mar$|^apr$|^mag$|^giu$|^lug$|^ago$|^set$|^ott$|^nov$|^dic$")

        NewName=filter(lambda number: not monBlack.search(number) and not numBlack.search(number), URLNAME)
        finalName="_".join(NewName)

        if not "mp3" in finalName:
            return finalName+".mp3"
        else:
            return finalName

    elif "selecta" in titlename.lower():
        return titlename.lower().rstrip().replace(" ","_").replace('&#039;','_')+".mp3"

    elif "puntata" in titlename.lower():
        return titlename.lower().replace("/","_").replace(" ","_")+".mp3"

    else:

        numBlack=re.compile("^[0-9]{1,4}")
        monBlack=re.compile(r"gen$|feb$|mar$|apr$|mag$|giu$|lug$|ago$|set$|dic$|gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre|real|movie|trust|book|realmovie|realbook|realtrust")
        removeDash=re.compile("-")
        removeUnder=re.compile("_")
        TitleName=filter(lambda number: not ( monBlack.search(number) or numBlack.search(number) or removeDash.search(number) or removeUnder.search(number)),titlename.lower().split())
        return "_".join(TitleName).replace('&#039;','_')+".mp3"

def numPages(URL):
    getDetails=opener.open(URL).read().decode()
    pageNumber=re.findall("<a class='page-numbers' href='https://www.m2o.it/programmi/real-trust/puntate/page/\d+/'>(\d+)</a>",getDetails)
    return max(pageNumber)

def storePlaylist(number,elem,page,size,url,hash):
     now=format(datetime.datetime.now()).split()[0]
     c.execute("INSERT INTO m2o VALUES("+"'"+now+"',"+"'"+str(number)+"'"+",'"+elem+"','"+str(page)+"','"+str(size)+"','"+url+"','"+str(hash)+"')")
     conn.commit()

def checkDups(filename):
    res=c.execute("SELECT filename FROM m2o WHERE filename LIKE \'"+filename+"\'")
    if res.fetchone():
        return True
    else:
        return False

def currentSHA2sum(files):
        files=files.encode()
        Hash=sha256(files).hexdigest()
        return Hash

def id3tag(filename,title,track,image):
    try:
        meta = EasyID3(filename)
    except mutagen.id3.ID3NoHeaderError :
        meta = mutagen.File(filename, easy=True)
        meta.add_tags()

    meta.delete()
    meta['title'] = title
    meta['artist'] = u"Roberto Molinaro"
    meta['album'] = u"m2o Real Trust"
    meta['tracknumber'] = str(track)
    meta.save()
    albumart=opener.open(image).read()

    meta = ID3(filename)

    meta['APIC'] = APIC(
            encoding=3,
            mime='image/jpeg',
            type=3, desc=u'Cover',
            data=albumart
    )
    meta.save()

def downloader(Links,page):

    for elem in Links:
         global counter
         counter=counter+1
         try : 
            fileLoc=opener.open(elem[0]).read().decode()
            mp3Loc=re.findall("<iframe src=.*&file=(.*)&duration",fileLoc)
            fileDown=opener.open(mp3Loc[0].split('.mp3')[0]+".mp3")
            localFileDown=gatherFilename(mp3Loc[0].split('.mp3')[0]+".mp3",elem[1])
            print("%s)Name: %s Title: %s URL: %s" % (counter,localFileDown,elem[1],mp3Loc[0].split('.mp3')[0]+".mp3"))

         except urllib.error.HTTPError:
             with open('m2o_logs.txt',"a") as logger:
                 print("Not Found: {}) {} Page: {} {}".format(counter,localFileDown,elem[1],mp3Loc[0]))
                 logger.write("Not Found: {}) {} Page: {} {}".format(counter,localFileDown,elem[1],mp3Loc[0]))

         if not checkDups(localFileDown) :
             # Downloading temp rem
             saveFile=open(localFileDown,"wb")
             total_size = fileDown.info()['Content-Length'].strip()
             total_length = int(total_size) if total_size else 8192

         
             try:
                 total_size = fileDown.info()['Content-Length'].strip()
                 header = True
             except AttributeError:
                 header = False
                 
             if header:
                 total_size = int(total_size)
             progress = 0
             while True:
                 data = fileDown.read(8192)

                 if not data:
                     break
                 progress += len(data)
                 saveFile.write(data)
                 if not header:
                     total_size = progress
                 percent = float(progress) / total_size
                 percent = round(percent*100,2)

                 print("Downloading: %s - %d of %d bytes (%0.2f%%)" % (localFileDown, progress, total_size, percent), flush=True,file=sys.stdout, end='\r')

             if os.path.isfile(localFileDown):
                embedImage=elem[2]
                storePlaylist(counter,localFileDown,page,os.path.getsize(localFileDown),mp3Loc[0],currentSHA2sum(localFileDown))
                id3tag(localFileDown, localFileDown.replace("_", " ").replace(".mp3", "").title(), counter,embedImage)
         else:
             print("** File: "+localFileDown, elem[1] ," already in DB",checkDups(localFileDown), mp3Loc[0])

def getMp3(pageNumber):

    maxPages=pageNumber
    #print "Total pages:", pageNumber
    countfiles=[]
    for i in range(int(maxPages)):
        if i >= 1:
            getPages=opener.open(URL+"page/"+str(i)).read().decode()
            getLinks=re.findall("<figure><a href=\"(.*?)\" title=\"(.*?)\"><img src=\"(.*?)\"",getPages)

            if len(countfiles) == 0:
                countfiles.append(int(len(getLinks)))
            else:
                cur=countfiles[0]
                countfiles.pop(0)
                countfiles.append(int(cur)+len(getLinks))

            countf=countfiles[0]-len(getLinks)
            print("Total Files on Page "+str(i)+": "+str(len(getLinks)))
            downloader(getLinks,i)



if __name__ == '__main__':
    if checkdb(DBName):
        getMp3(numPages(URL))
