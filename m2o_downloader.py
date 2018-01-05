#!/usr/bin/python

import os
import sys
import re
import ssl
import urllib2
import sqlite3
from cookielib import CookieJar
from hashlib import sha256

conn = sqlite3.connect('m2o.sqlite3',check_same_thread=False)
c=conn.cursor()


URL="https://www.m2o.it/programmi/real-trust/puntate/"

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

def numPages(URL):
    getDetails=urllib2.urlopen(URL).read()
    pageNumber=re.findall("<a class='page-numbers' href='https://www.m2o.it/programmi/real-trust/puntate/page/\d+/'>(\d+)</a>",getDetails)
    return max(pageNumber)

def storePlaylist(number,elem,page,size,Hash):

     c.execute("INSERT INTO m2o VALUES("+"'"+str(number)+"'"+",'"+elem+"','"+str(page)+"','"+str(size)+"','"+str(Hash)+"')")
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

def downloader(Links,page):

    counter = 0
    for elem in Links:
         counter=counter+1

         try:
             fileLoc=urllib2.urlopen(elem[0]).read()
             mp3Loc=re.findall("<iframe src=.*&file=(.*)&duration",fileLoc)
             fileDown=urllib2.urlopen(mp3Loc[0])

             if "real" in mp3Loc[0].split("/")[-1].replace("_"," ").lower() :
                 localFileDown = elem[1].split("-")[-1].lstrip().replace(" ","_").lower()+".mp3"
             elif "real" in elem[1].lower() :
                 if not mp3Loc[0].split("/")[-1].split("_")[2:] == "" :
                    localFileDown ="_".join(mp3Loc[0].split("/")[-1].split("_")[2:]).lower()
                 else :
                     localFileDown = "_".join(mp3Loc[0].split("/")[-1].split("_")).lower()
             else:
                 print localFileDown,"empty",mp3Loc

             if not checkDups(localFileDown):
                 saveFile=open(localFileDown,"wb")
                 print "Downloading Link: ",mp3Loc[0], "\tEpisode Name: ", elem[1], "\tElements In Download so Far:", counter

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

                 storePlaylist(counter,localFileDown,page,os.path.getsize(localFileDown),currentSHA2sum(localFileDown))
             else:
                 print "** File: "+localFileDown," already in DB"
        except Exception, e:
            print "Not handled error: ",e 


def getMp3(pageNumber):

    maxPages=pageNumber
    print "Total pages:", pageNumber
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
    getMp3(numPages(URL))
