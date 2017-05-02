#!/usr/bin/python

import sys, os, time, urllib2, socket
from xml.sax.saxutils import unescape
from cookielib import CookieJar

if len(sys.argv) < 2:
  print "Usage 1.py user"
  quit(1)

blocksize = 65536

socket.setdefaulttimeout(30)

cj = CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

def pageiter(buf, start, end, pos = 0):
    while True:
        pos = buf.find(start, pos)
        if pos == -1: break
        pos += len(start)
        pos2 = buf.find(end, pos)
        yield buf[pos:pos2]
        pos = pos2+len(end)

def login(username, password):
    f = opener.open("https://www.deviantart.com/users/login?username=")
    page = f.read()
    f.close()

    f = opener.open("https://www.deviantart.com/users/login",
        "ref=https://www.deviantart.com/users/loggedin&username=%s&action=Login&remember_me=1&password=%s&validate_token=%s&validate_key=%s" % (
        username, password,
        pageiter(page,'name="validate_token" value="','"').next(),
        pageiter(page,'name="validate_key" value="','"').next()))

    page = f.read()
    f.close()

try:
    with open("credentials","r") as f:
        dauser = f.next()
        passwd = f.next()
        login(dauser, passwd)
except:
    pass

user = sys.argv[1]

if not os.path.exists(user):
    os.mkdir(user)

pagenum=0
flag = True
retry = True
while flag:
    sys.stderr.write("Page %i\n" % pagenum)
    f = opener.open("http://%s.deviantart.com/gallery/?catpath=%%2F&offset=%i" % (user, pagenum * 24))
    page = f.read()
    f.close()
    flag = False
    for div in pageiter(page, 'data-sigil="torpedo-thumb deviation-thumb','</span>', page.index('<td id="gruze-main"')):
        try:
            url = pageiter(div, 'data-super-full-img="','"').next()
        except StopIteration:
            try:
                url = pageiter(div, 'data-super-img="','"').next()
            except StopIteration:
              try:
                  url = pageiter(div, '<img data-sigil="torpedo-img" src="','"').next()
              except StopIteration:
                if 'freeform-thumb-text' in div: continue
                if 'state-msg mature-state-msg' in div: retry = True
                print("Unknown content type:\n" + div)
                if retry:
                    print("Retrying")
                    login(dauser, passwd)
                    pagenum -= 1
                    retry = False
                    flag = True
                    break
                retry = True
                continue
        filename = user + url[url.rindex("/"):]
        sys.stderr.write(filename)
        if os.path.exists(filename):
            print(" - Exists!")
            flag = True #False
            continue
        fin = opener.open(url)
        fout = open(filename, "wb")
        while True:
            buf = fin.read(blocksize)
            if not buf: break
            fout.write(buf)
            sys.stderr.write(".")
        fout.close()
        t = time.mktime(fin.info().getdate("date"))
        fin.close()
        os.utime(filename, (t,t))
        sys.stderr.write("\n")
        flag = True
        retry = True

    pagenum += 1

f = opener.open("https://www.deviantart.com/users/logout", "")
f.close()
