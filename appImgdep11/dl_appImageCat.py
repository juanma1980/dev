#!/usr/bin/env python3
#Download and generate a yml catalog from appimage repository at https://dl.bintray.com/probono/AppImages/

import urllib.request

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

def write_yml(applist,outfile):
    f=open(outfile,'w')
    for app in applist:
        f.write("---\n")
        f.write("Categories:\n  - GTK\n  - AppImage\n")
        f.write("ID: "+app+"\n")
        f.write("Icon:\n  stock: appImage.png\n")
        name=app.split('.')[0]
        f.write("Name:\n C: "+name+"\n")
        f.write("Package: "+name+".AppImage\n")
        f.write("Summary:\n  C: "+name+" AppImage Bundle\n")
        f.write("Description:\n")
        f.write("  C: This is an AppImage bundle of app "+name+". It hasn't been tested by our developers and comes from a 3rd party dev team. Please use it carefully\n")
        f.write("  es: Este es el paquete AppImage de la aplicación "+name+". No ha sido testado por nuestros desarrolladores y proviene de equipo de desarrollo externo. Por favor, utilizalo con cuidado\n")
        f.write("  ca_ES@valencia: This is an AppImage bundle of app "+name+". It hasn't been tested by our developers and comes from a 3rd party dev team. Please use it carefully\n")
        f.write("Type: desktop-app\n")
        f.write("Bundle:\n  appimage: "+app+"\n")
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


