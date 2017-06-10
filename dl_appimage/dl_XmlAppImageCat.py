#!/usr/bin/env python3
#Download and generate a yml catalog from appimage repository at https://dl.bintray.com/probono/AppImages/
import sys
import urllib.request
import threading
from bs4 import BeautifulSoup
import random
def fetch_repo(repo):
    with urllib.request.urlopen('https://dl.bintray.com/probono/AppImages') as f:
        content=(f.read().decode('utf-8'))
    return(content)

def generate_applist(content):
    garbageList=[]
    garbageList=content.split(' ')
    for garbageLine in garbageList:
        if garbageLine.endswith('AppImage"'):
            app=garbageLine.replace('href=":','')
            applist.append(app.replace('"',''))
    return(applist)

def get_description(appName):
    desc=''
    print("Getting description from 'https://bintray.com/probono/AppImages/'"+appName)
    try:
        with urllib.request.urlopen('https://bintray.com/probono/AppImages/'+appName) as f:
            content=(f.read().decode('utf-8'))
        soup=BeautifulSoup(content,"html.parser")
        descDiv=soup.findAll('div', attrs={ "class" : "description-text"})
        if len(descDiv)>0:
            desc=descDiv[0].text
            desc=desc.replace(':','.')
            desc=desc.replace('&','&amp;')
    except:
        pass
    return(desc)

def th_generate_xml_catalog(applist,outdir):
    oldName=''
    oldDesc=''
    descDict={}
    maxconnections = 10
    semaphore = threading.BoundedSemaphore(value=maxconnections)
    randomList = list(applist)
    random.shuffle(randomList)
    for app in randomList:
        print("Launching thread")
        th=threading.Thread(target=_th_write_xml, args = (app,outdir,semaphore))
        th.start()

def _th_write_xml(app,outdir,semaphore):
    semaphore.acquire()
    global descDict
    lock=threading.Lock()
    print("Generating "+app+" xml")
    nameSplitted=app.split('-')
    name=nameSplitted[0]
    version=nameSplitted[1]
    arch=nameSplitted[2]
    f=open(outdir+'/'+name+"_"+version+".appdata.xml",'w')
    f.write('<?xml version="1.0" encoding="UTF-8"?>'+"\n")
    f.write("<components version=\"0.10\">\n")
    f.write("<component  type=\"desktop-application\">\n")
    f.write("  <id>"+app.lower()+"</id>\n")
    f.write("  <pkgname>"+app+"</pkgname>\n")
    f.write("  <name>"+name+"</name>\n")
    f.write("  <summary>"+name+" AppImage Bundle</summary>\n")
    f.write("  <metadata_license>CC0-1.0</metadata_license>\n")
    f.write("  <provides><binary>"+app+"</binary></provides>\n")
    f.write("  <releases>\n")
    f.write("  <release version=\""+version+"\" timestamp=\"1408573857\"></release>\n")
    f.write("  </releases>\n")
    f.write("  <launchable type=\"desktop-id\">"+name+".desktop</launchable>\n")
    with lock:
        if name in descDict.keys():
            description=descDict[name]
        else:
            description=get_description(name)
            descDict.update({name:description})
    f.write("  <description><p>This is an AppImage bundle of app "+name+". It hasn't been tested by our developers and comes from a 3rd party dev team. Please use it carefully.</p><p>"+description+"</p></description>\n")
    f.write("  <bundle type=\"appimage\">"+app+"</bundle>\n")
    f.write("  <keywords>\n")
    f.write("    <keyword>"+name+"</keyword>\n")
    f.write("    <keyword>appimage</keyword>\n")
    f.write("  </keywords>\n")
    f.write("  <categories>\n")
    f.write("    <category>AppImage</category>\n")
    f.write("    <category>GTK</category>\n")
    f.write("  </categories>\n")
    f.write("<icon type=\"cached\">"+name+"_"+name+".png</icon>\n")
    f.write("</component>\n")
    f.write("</components>\n")
    f.close()
    semaphore.release()

def write_yml(applist,outfile):
    oldName=''
    oldDesc=''
    f=open(outfile,'w')
    f.write("---\nFile: DEP-11\nVersion: '0.8'\nOrigin: xenial-main\n")
    for app in applist:
        nameSplitted=app.split('-')
        name=nameSplitted[0]
        version=nameSplitted[1]
        arch=nameSplitted[2]
        f.write("---\n")
        f.write("Categories:\n  - GTK\n  - AppImage\n")
        f.write("ID: "+app.lower()+"\n")
        f.write("Icon:\n  stock: "+name+"_"+name+".png\n")
        f.write("Name:\n C: "+name+"\n")
        f.write("Package: "+app+"\n")
        f.write("Summary:\n  C: "+name+" AppImage Bundle\n")
        f.write("Description:\n")
        f.write("  C:<p>This is an AppImage bundle of app "+name+". It hasn't been tested by our developers and comes from a 3rd party dev team. Please use it carefully\n")
        f.write("  Este es el paquete AppImage de la aplicación "+name+". No ha sido testado por nuestros desarrolladores y proviene de equipo de desarrollo externo. Por favor, utilizalo con cuidado\n")
        f.write("  This is an AppImage bundle of app "+name+". It hasn't been tested by our developers and comes from a 3rd party dev team. Please use it carefully<p>\n")
        description=oldDesc
        if oldName!=name:
            description=get_description(name)
            oldName=name
            oldDesc=description
        f.write("  "+description+"</p>\n")
        f.write("Type: desktop-app\n")
        f.write("Keywords:\n")
        f.write("  C:\n")
        f.write("    - "+name+"\n")
        f.write("    - "+app+"\n")
        f.write("Bundle:\n- type: appimage\n  id: "+app+"\n")
        f.write("Releases:\n")
        f.write("  - version: "+version+"\n")
    f.close()

args=sys.argv[1:]
if '-y' in args:
    sw_generate='yml'
    print("Generating dep11 catalogue...")
else:
    sw_generate='xml'
    print("Generating xml catalogue...")
outfile='appimage.yml'
outdir="/usr/share/metainfo"
outdir="/tmp"
content=''
applist=[]
repolist=['https://dl.bintray.com/probono/AppImages']
descDict={}
for repo in repolist:
    print(("Fetching repo %s")%(repo))
    applist=generate_applist(fetch_repo(repo))
    print("Processing info...")
    if sw_generate=='yml':
        write_yml(applist,outfile)
    else:
        th_generate_xml_catalog(applist,outdir)
    print("Work done!")


