#!/usr/bin/env python3
#Download and generate a yml catalog from appimage repository at https://dl.bintray.com/probono/AppImages/

import urllib.request
from bs4 import BeautifulSoup

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
            desc.replace(':','.')
    except:
        pass
    return(desc)

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

outfile='appimage.yml'
content=''
applist=[]
repolist=['https://dl.bintray.com/probono/AppImages']
for repo in repolist:
    print(("Fetching repo %s")%(repo))
    applist=generate_applist(fetch_repo(repo))
    print("Generating dep11 catalogue...")
    write_yml(applist,outfile)
    print("Work done!")


