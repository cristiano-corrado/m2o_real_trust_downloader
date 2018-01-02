#!/usr/bin/python

import os
import sys
import re
import ssl
import urllib2
from cookielib import CookieJar


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

def getMp3(pageNumber):
    maxPages=pageNumber
    print "Total pages:", pageNumber
    for i in range(int(maxPages)):
        getPages=urllib2.urlopen(URL+"page/"+str(i)).read()
        getLinks=re.findall("<figure><a href=\"(.*?)\" title=\"(.*?)\"",getPages)
        print "Page: "+str(i)
        for elem in getLinks:
             fileLoc=urllib2.urlopen(elem[0]).read()
             mp3Loc=re.findall("<iframe src=.*&file=(.*)&duration",fileLoc)
             fileDown=urllib2.urlopen(mp3Loc[0])
             print "Download Link: ",mp3Loc[0], "Episode Name: ", elem[1]
             localFileDown = open(elem[0].split("/")[len(elem[0].split("/"))-1].replace(".mp3","").title()+".mp3","wb")
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
                 localFileDown.write(data)
                 if not header:
                     total_size = progress
                 percent = float(progress) / total_size
                 percent = round(percent*100,2)
                 sys.stdout.write("Downloaded %d of %d bytes (%0.2f%%)\r" % (progress, total_size, percent))



if __name__ == '__main__':
    getMp3(numPages(URL))
