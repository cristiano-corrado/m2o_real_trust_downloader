#!/usr/bin/python

import os
import sys
import re
import ssl
import urllib2
import sqlite3
import datetime
import eyed3
from cookielib import CookieJar
from hashlib import sha256

URL="https://www.m2o.it/programmi/real-trust/puntate/"
DBName="m2o"

# Sqlite connector
conn = sqlite3.connect(DBName+'.sqlite3',check_same_thread=False)
c=conn.cursor()

# urllib2 configuration
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
cj=CookieJar()

opener=urllib2.build_opener(
        urllib2.HTTPSHandler(context=ctx),
        urllib2.HTTPCookieProcessor(cj)
    )

opener.addheaders = [('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0')]
urllib2.install_opener(opener)

def checkdb(DB):
    ex=c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=\'"+DB+"\'");
    if ex.fetchone() == None :
        c.execute("CREATE TABLE m2o(datedown,songnum,filename,page,filesize,url,hash)")
        print "Creating DB structure, table name: "+DB
    else:
        print "DB exists and in path. Downloading songs..."
    return True

def gatherFilename(urlname,titlename):

    URLNAME=urlname[0].split("/")[-1]

    if not re.findall(r"real|realmovie|realbook|realtrust|trust",URLNAME):
        numBlack=re.compile("^[0-9]")
        URLNAME=URLNAME.split("_")
        monBlack=re.compile(r"^gen$|^feb$|^mar$|^apr$|^mag$|^giu$|^lug$|^ago$|^set$|^ott$|^nov$|^dic$")
        NewName=filter(lambda number: not ( monBlack.search(number) or numBlack.search(number) ),URLNAME)

        if not "mp3" in "_".join(NewName):
            return "_".join(NewName)+".mp3"
        else:
            return "_".join(NewName)

    elif "selecta" in titlename.lower():
        return titlename.lower().rstrip().replace(" ","_")+".mp3"

    else:

        numBlack=re.compile("^[0-9]{1,4}")
        monBlack=re.compile(r"gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre|real|movie|trust|book|realmovie|realbook|realtrust")
        removeDash=re.compile("-")
        TitleName=filter(lambda number: not ( monBlack.search(number) or numBlack.search(number) or removeDash.search(number)),titlename.lower().split())
        return "_".join(TitleName)+".mp3"
    sys.exit()

def numPages(URL):
    getDetails=urllib2.urlopen(URL).read()
    pageNumber=re.findall("<a class='page-numbers' href='https://www.m2o.it/programmi/real-trust/puntate/page/\d+/'>(\d+)</a>",getDetails)
    return max(pageNumber)

def storePlaylist(number,elem,page,size,Hash,url):
     now=format(datetime.datetime.now()).split()[0]
     c.execute("INSERT INTO m2o VALUES("+"'"+now+"',"+"'"+str(number)+"'"+",'"+elem+"','"+str(page)+"','"+str(size)+"','"+url+"','"+str(Hash)+"')")
     conn.commit()

def checkDups(filename):
    res=c.execute("SELECT filename FROM m2o WHERE filename LIKE \'"+filename+"\'")
    if res.fetchone():
        return True
    else:
        return False

def currentSHA2sum(files):
        Hash=sha256(files).hexdigest()
        return Hash

def id3tag(filename,title,counter,page):
    audiofile=eyed3.load(filename)
    audiofile.tag.artist = u"Roberto Molinaro"
    audiofile.tag.album = u"m2o Real Trust"
    audiofile.tag.title = title
    audifile.tag.track_num = int(page),int(counter)
    audiofile.tag.save()
    sys.exit()

def downloader(Links,page):
    counter = 0
    for elem in Links:
         counter=counter+1
         try:
             fileLoc=urllib2.urlopen(elem[0]).read()
             mp3Loc=re.findall("<iframe src=.*&file=(.*)&duration",fileLoc)
             fileDown=urllib2.urlopen(mp3Loc[0])
             localFileDown=gatherFilename(mp3Loc,elem[1])
             print "%s)Name:%s Title:%s URL:%s" % (counter,localFileDown,elem[1],mp3Loc[0])

             if not checkDups(localFileDown) :

                 # Downloading temp rem
                 saveFile=open(localFileDown,"wb")

                 try:
                     total_size = fileDown.info().getheader('Content-Length').strip()
                     header = True
                 except AttributeError:
                     header = False
                 if header:
                     total_size = int(total_size)
                 progress = 0
                 while True:
                     data = fileDown.read(8192)
                     if not data:
                         sys.stdout.write('\n')
                         break
                     progress += len(data)
                     saveFile.write(data)
                     if not header:
                         total_size = progress
                     percent = float(progress) / total_size
                     percent = round(percent*100,2)
                     sys.stdout.write("Downloaded %d of %d bytes (%0.2f%%)\r" % (progress, total_size, percent))

                 storePlaylist(counter,localFileDown,page,os.path.getsize(localFileDown),mp3Loc[0],currentSHA2sum(localFileDown))
                 #id3tag(localFileDown,localFileDown.replace("_"," ").replace(".mp3","").title(),counter,page)
             else:
                 print "** File: "+localFileDown, elem[1] ," already in DB",checkDups(localFileDown), mp3Loc[0]

         except Exception, e:
            print "Not handled error: ",e

def getMp3(pageNumber):

    maxPages=pageNumber
    #print "Total pages:", pageNumber
    countfiles=[]
    for i in range(int(maxPages)):
        if i >= 1:
            getPages=urllib2.urlopen(URL+"page/"+str(i)).read()
            getLinks=re.findall("<figure><a href=\"(.*?)\" title=\"(.*?)\"",getPages)

            if len(countfiles) == 0:
                countfiles.append(int(len(getLinks)))
            else:
                cur=countfiles[0]
                countfiles.pop(0)
                countfiles.append(int(cur)+len(getLinks))

            print "Total Files on Page "+str(i)+": "+str(len(getLinks))
            print "Total Files In Download: "+str(countfiles[0])

            downloader(getLinks,i)

if __name__ == '__main__':
    if checkdb(DBName):
        getMp3(numPages(URL))
