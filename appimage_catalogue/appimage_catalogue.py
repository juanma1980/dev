#!/usr/bin/python3
import urllib
import re
from urllib.request import Request
from urllib.request import urlretrieve
import shutil
import json
import os
from subprocess import call
import sys
import threading
from bs4 import BeautifulSoup
import random
import time
import gi
from gi.repository import Gio
gi.require_version('AppStreamGlib', '1.0')
from gi.repository import AppStreamGlib as appstream
import queue
import time

class appimageToAppstream:

	def __init__(self):
		self.dbg=True
		#To get the description of an app we must go to a specific url defined in url_info.
		#$(appname) we'll be replaced with the appname so the url matches the right one.
		#If other site has other url naming convention it'll be mandatory to define it with the appropiate replacements
		self.repos={'appimagehub':{'type':'json','url':'https://appimage.github.io/feed.json','url_info':''}}
		#Appimges not stored in a repo must be listed in this file, providing the download url and the info url (if there's any)
		self.external_appimages="/usr/share/lliurex-store/files/external_appimages.json"
		self.conf_dir=os.getenv("HOME")+"/.cache/lliurex-store"
		self.bundles_dir=self.conf_dir+"/bundles"
		self.queue=queue.Queue()
	#def __init__

	def _debug(self,msg=''):
		if self.dbg:
			print ('DEBUG appimage: %s'%msg)
	#def debug

	def get_bundles_catalogue(self):
		applist=[]
		appdict={}
		all_apps=[]
		outdir=self.bundles_dir+'/appimg/'
		#Load repos
		for repo_name,repo_info in self.repos.items():
			if not os.path.isdir(self.bundles_dir):
				try:
					os.makedirs(self.bundles_dir)
				except:
					self._debug("appImage catalogue could not be fetched: Permission denied")
			self._debug("Fetching repo %s"%repo_info['url'])
			if repo_info['type']=='repo':
				applist=self._generate_applist(self._fetch_repo(repo_info['url']),repo_name)
				self._debug("Processing info...")
			elif repo_info['type']=='json':
				applist=self._process_appimage_json(self._fetch_repo(repo_info['url']),repo_name)
			self._debug("Fetched repo "+repo_info['url'])
			self._th_generate_xml_catalog(applist,outdir,repo_info['url_info'],repo_info['url'],repo_name)
			all_apps.extend(applist)
		#Load external apps
		for app_name,app_info in self._get_external_appimages().items():
			if os.path.isdir(self.bundles_dir):
				appinfo=self._init_appinfo()
				appinfo['name']=app_info['url'].split('/')[-1]
				appinfo['package']=app_info['url'].split('/')[-1]
				appinfo['homepage']='/'.join(app_info['url'].split('/')[0:-1])
				self._debug("Fetching external appimage %s"%app_info['url'])
				appinfo['bundle']='appimage'
				applist=[appinfo]
				self._th_generate_xml_catalog(applist,outdir,app_info['url_info'],app_info['url'],app_name)
				self._debug("Fetched appimage "+app_info['url'])
				all_apps.extend(applist)
			else:
				self._debug("External appImage could not be fetched: Permission denied")
		self._debug("Removing old entries...")
#		self._clean_bundle_catalogue(all_apps,outdir)
	#def _download_bundles_catalogue

	def _process_releases(self,applist):
		appdict={}
		for app in applist:
			version=''
			name_splitted=app.split('-')
			name=name_splitted[0]
			if len(name_splitted)>1:
				version='-'.join(name_splitted[1][-1])
			if name in appdict.keys():
				appdict[name].append(version)
			else:
				appdict[name]=[version]
		self._debug("APPS:\n%s"%appdict)
		return appdict
	#def _process_releases

	def _fetch_repo(self,repo):
		req=Request(repo, headers={'User-Agent':'Mozilla/5.0'})
		with urllib.request.urlopen(req) as f:
			content=(f.read().decode('utf-8'))
		
		return(content)
	#def _fetch_repo

	def _generate_applist(self,content,repo_name):
		garbage_list=[]
		applist=[]
		#webscrapping for probono repo
		if repo_name=='probono':
			garbage_list=content.split(' ')
			for garbage_line in garbage_list:
				if garbage_line.endswith('AppImage"'):
					app=garbage_line.replace('href=":','')
					applist.append(app.replace('"',''))
		#Example of a webscrapping from another site
#		if repo_name='other_repo_name':
#			for garbage_line in garbage_list:
#					if garbage_line.startswith('file="'):
#						if 'appimage' in garbage_line:
#							app=garbage_line.replace('file="','')
#							app=app.replace('\n','')
#							self._debug("Add %s"%app)
#							applist.append(app.replace('"',''))
			for garbage_line in garbage_list:
				if garbage_line.endswith('AppImage"'):
					app=garbage_line.replace('href=":','')
					applist.append(app.replace('"',''))
		return(applist)
	#def _generate_applist

	def _get_external_appimages(self):
		external_appimages={}
		if os.path.isfile(self.external_appimages):
			try:
				with open(self.external_appimages) as appimages:
					external_appimages=json.load(appimages)
			except:
				self._debug("Can't load %s"%self.external_appimages)
		self._debug(external_appimages)
		return external_appimages
	#_get_external_appimages

	def _process_appimage_json(self,data,repo_name):
		maxconnections = 10
		semaphore = threading.BoundedSemaphore(value=maxconnections)
		applist=[]
		json_data=json.loads(data)
		if 'items' in json_data.keys():
			for appimage in json_data['items']:
				th=threading.Thread(target=self._th_process_appimage, args = (appimage,semaphore))
				th.start()

		while threading.active_count()>1:
		    time.sleep(0.1)

		while not self.queue.empty():
		    applist.append(self.queue.get())
		self._debug("JSON: %s"%applist)
		return (applist)
	#_process_appimage_json

	def _th_process_appimage(self,appimage,semaphore):
		releases=[]
		if 'links' in appimage.keys():
			releases=self._get_releases_from_json(appimage)
		if releases:
			appinfo=self.load_json_appinfo(appimage)
			appinfo['releases']=releases
#			applist.append(appinfo)
			self.queue.put(appinfo)
#                  	for release in releases:
#				tmp_appinfo=appinfo.copy()
#				self._debug("Release: %s"%release)
#				tmp_appinfo['name']=release
#				tmp_appinfo['package']=release
#				applist.append(tmp_appinfo)
        #def _th_process_appimage

	def load_json_appinfo(self,appimage):
		appinfo=self._init_appinfo()
		appinfo['name']=appimage['name']
		appinfo['package']=appimage['name']
		if 'license' in appimage.keys():
			appinfo['license']=appimage['license']
		appinfo['summary']=''
		if 'description' in appimage.keys():
			appinfo['description']=appimage['description']
		if 'categories' in appimage.keys():
			appinfo['categories']=appimage['categories']
		if 'icon' in appimage.keys():
			appinfo['icon']=appimage['icon']
		if 'screenshots' in appimage.keys():
			appinfo['thumbnails']=appimage['screenshots']
		if 'authors' in appimage.keys():
			if appimage['authors']:
				for author in appimage['authors']:
					if 'url' in author.keys():
						appinfo['homepage']=author['url']
		appinfo['bundle']='appimage'
		return appinfo
	#def load_json_appinfo

	def _get_releases_from_json(self,appimage):
		releases=[]
		if appimage['links']:
			for link in appimage['links']:
				if 'type' in link.keys():
					if link['type']=='Download':
						self._debug("Info url: %s"%link['url'])
						try:
							with urllib.request.urlopen(link['url']) as f:
								content=(f.read().decode('utf-8'))
								soup=BeautifulSoup(content,"html.parser")
								package_a=soup.findAll('a', attrs={ "href" : re.compile(r'.*[aA]pp[iI]mage$')})
								for package_data in package_a:
									package_soup=BeautifulSoup(str(package_data),"html.parser")
									package_name=package_soup.findAll('strong', attrs={ "class" : "pl-1"})
#									self._debug("Release name: %s"%package_name)
									for name in package_name:
										releases.append(name.get_text())
						except Exception as e:
							print(e)
		return releases
	#def _get_releases_from_json

	def _th_generate_xml_catalog(self,applist,outdir,info_url,repo,repo_name):
		maxconnections = 10
		semaphore = threading.BoundedSemaphore(value=maxconnections)
		random_applist = list(applist)
		random.shuffle(random_applist)
		for app in applist:
			th=threading.Thread(target=self._th_write_xml, args = (app,outdir,info_url,repo,repo_name,semaphore))
			th.start()
	#def _th_generate_xml_catalog

	def _th_write_xml(self,appinfo,outdir,info_url,repo,repo_name,semaphore):
		semaphore.acquire()
		lock=threading.Lock()
		self._debug("Populating %s"%appinfo)
		filename=outdir+appinfo['package'].lower().replace('appimage',"appdata")+".xml"
		self._debug("checking if we need to download "+filename)
		if not os.path.isfile(filename):
			repo_info={'info_url':info_url,'repo':repo,repo_name:'repo_name'}
			self._write_xml_file(filename,appinfo,repo_info,lock)
		semaphore.release()
	#def _th_write_xml

	def _write_xml_file(self,filename,appinfo,repo_info,lock):
			name=appinfo['name'].lower().replace(".appimage","")
			self._debug("Generating %s xml"%appinfo['package'])
			f=open(filename,'w')
			f.write('<?xml version="1.0" encoding="UTF-8"?>'+"\n")
			f.write("<components version=\"0.10\">\n")
			f.write("<component  type=\"desktop-application\">\n")
			f.write("  <id>%s</id>\n"%appinfo['package'].lower())
			f.write("  <pkgname>%s</pkgname>\n"%appinfo['package'])
			f.write("  <name>%s</name>\n"%name)
			f.write("  <metadata_license>CC0-1.0</metadata_license>\n")
			f.write("  <provides><binary>%s</binary></provides>\n"%appinfo['name'])
			if 'releases' in appinfo.keys():
				f.write("  <releases>\n")
				for release in appinfo['releases']:
					f.write("    <release version=\"%s\" urgency=\"medium\">"%release)
					f.write("</release>\n")
				f.write("  </releases>\n")
			f.write("  <launchable type=\"desktop-id\">%s.desktop</launchable>\n"%name)
			if appinfo['description']=='':
				with lock:
					try:
						if appinfo['name'] in self.descriptions_dict.keys():
							(description,icon)=self.descriptions_dict[appinfo['name']]
						else:
							(description,icon)=self._get_description_icon(appinfo['name'],repo_info)
							self.descriptions_dict.update({appinfo['name']:[description,icon]})
					except:
						description=''
						icon=''
			else:
				description=appinfo['description']
			summary=' '.join(list(description.split(' ')[:8]))
			if len(description.split(' '))>8:
				summary+="... "
			description="This is an AppImage bundle of app %s. It hasn't been tested by our developers and comes from a 3rd party dev team. Please use it carefully.\n%s"%(name,description)
			if summary=='':
				summary=' '.join(list(description.split(' ')[:8]))
			f.write("  <description><p></p><p>%s</p></description>\n"%description)
			f.write("  <summary>%s</summary>\n"%summary)
#			f.write("  <icon type=\"local\">%s</icon>\n"%appinfo['icon'])
			f.write("<icon type=\"cached\">"+name+"_"+name+".png</icon>\n")
			f.write("  <url type=\"homepage\">%s</url>\n"%appinfo['homepage'])
			f.write("  <bundle type=\"appimage\">%s</bundle>\n"%appinfo['name'])
			f.write("  <keywords>\n")
			keywords=name.split("-")
			banned_keywords=["linux","x86_64","i386","ia32","amd64"]
			for keyword in keywords:
				#Better than isalpha method for this purpose
				if keyword.isidentifier() and keyword not in banned_keywords:
					f.write("	<keyword>%s</keyword>\n"%keyword)
			f.write("	<keyword>appimage</keyword>\n")
			f.write("  </keywords>\n")
			f.write("  <categories>\n")
			f.write("	<category>AppImage</category>\n")
			if 'categories' in appinfo.keys():
				for category in appinfo['categories']:
					f.write("	<category>%s</category>\n"%category)
			f.write("  </categories>\n")
			f.write("</component>\n")
			f.write("</components>\n")
			f.close()
	#def _write_xml_file

	def _get_description_icon(self,app_name,repo_info):
		desc=''
		icon=''
		if repo_info['info_url']:
			if '$(appname)' in repo_info['info_url']:
				info_url=info_url.replace('$(appname)',app_name)
			self._debug("Getting description from repo/app %s - %s "%(repo_info['repo_name'],repo_info['info_url']))
			try:
				with urllib.request.urlopen(info_url) as f:
					#Scrap target info page
					if repo_name=='probono':
						content=(f.read().decode('utf-8'))
						soup=BeautifulSoup(content,"html.parser")
						description_div=soup.findAll('div', attrs={ "class" : "description-text"})
						icon_div=soup.findAll('div', attrs={ "class" : "avatar-icon avatar-large description-icon "})
				if len(description_div)>0:
					desc=description_div[0].text
					desc=desc.replace(':','.')
					desc=desc.replace('&','&amp;')
				if len(icon_div)>0:
					icon_str=str(icon_div[0])
					icon=icon_str.split(' ')[9]
					icon=icon.lstrip('url(')
					if icon.startswith('http'):
						icon=icon.rstrip(');"></div>')
						icon=self._download_file(icon,app_name)
			except Exception as e:
				print("Can't get description from "+repo_info['info_url'])
				print(str(e))
				pass
		return([desc,icon])
	#def _get_description

	def _download_file(self,url,app_name='app',target_file=''):
		if target_file=='':
			target_file=self.icons_dir+'/'+app_name+".png"
		if not os.path.isfile(target_file):
			if not os.path.isfile(target_file):
				self._debug("Downloading %s to %s"%(url,target_file))
				try:
					with urllib.request.urlopen(url) as response, open(target_file, 'wb') as out_file:
						bf=16*1024
						acumbf=0
						file_size=int(response.info()['Content-Length'])
						while True:
							if acumbf>=file_size:
							    break
							shutil.copyfileobj(response, out_file,bf)
							acumbf=acumbf+bf
					st = os.stat(target_file)
				except Exception as e:
					self._debug("Unable to download %s"%url)
					self._debug("Reason: %s"%e)
					target_file=url
		return(target_file)
	#def _download_file

	def _init_appinfo(self):
		appInfo={'appstream_id':'',\
		'id':'',\
		'name':'',\
		'version':'',\
		'releases':[],\
		'package':'',\
		'license':'',\
		'summary':'',\
		'description':'',\
		'categories':[],\
		'icon':'',\
		'screenshot':'',\
		'thumbnails':[],\
		'video':'',\
		'homepage':'',\
		'installerUrl':'',\
		'state':'',\
		'depends':'',\
		'kudos':'',\
		'suggests':'',\
		'extraInfo':'',\
		'size':'',\
		'bundle':'',\
		'updatable':'',\
		}
		return(appInfo)


catalogue=appimageToAppstream()
catalogue.get_bundles_catalogue()
