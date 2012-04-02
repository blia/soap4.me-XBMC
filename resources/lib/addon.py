#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import urllib2, urllib, os, xml.dom.minidom, cookielib, base64
try:
	import json
except:
	import simplejson as json
from StringIO import StringIO
import gzip
import socket, sys
import time
try:
	import hashlib
except:
	import md5 as hashlib
socket.setdefaulttimeout(15)

h = int(sys.argv[1])

__addon__ = xbmcaddon.Addon(id = 'plugin.video.soap4me')

addon_icon	  = __addon__.getAddonInfo('icon')
addon_fanart  = __addon__.getAddonInfo('fanart')
addon_path	  = __addon__.getAddonInfo('path')
addon_type	  = __addon__.getAddonInfo('type')
addon_id	  = __addon__.getAddonInfo('id')
addon_author  = __addon__.getAddonInfo('author')
addon_name	  = __addon__.getAddonInfo('name')
addon_version = __addon__.getAddonInfo('version')
addon_profile = __addon__.getAddonInfo('profile')

icon   = xbmc.translatePath(addon_icon)
fanart = xbmc.translatePath(addon_fanart)
profile = xbmc.translatePath(addon_profile)
xbmcplugin.setPluginFanart(h, fanart)

def showMessage(heading, message, times = 3000):
	xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, "%s")'%(heading, message, times, icon))


def soap4me_get_cashe(id, cashe_min):
	cashe_path = os.path.join(profile, 'cashe')
	if not os.path.exists(cashe_path):
		os.makedirs(cashe_path)

	path_file = cashe_path +"/"+ str(id)
	max_time = time.time() - cashe_min * 60

	if os.path.exists(path_file) and os.path.getmtime(path_file) >= max_time:
		f = open(path_file, "r")
		text = f.read()
		f.close()
		return text
	return False



def soap4me_save_cashe(id, text):
	cashe_path = os.path.join(profile, 'cashe')
	if not os.path.exists(cashe_path):
		os.makedirs(cashe_path)

	path_file = cashe_path +"/"+ str(id)

	f = open(path_file, "w")
	f.write(text)
	f.close()





def soap4me_login():
	try:
		url = "http://soap4.me/login/"
		username = __addon__.getSetting('username')
		password = __addon__.getSetting('password')

		if (not len(username)) and (not len(password)):
			__addon__.openSettings()
			username = __addon__.getSetting('username')
			password = __addon__.getSetting('password')


		CJ = cookielib.CookieJar()
		urllib2.install_opener(urllib2.build_opener(urllib2.HTTPCookieProcessor(CJ)))

		req = urllib2.Request(url)
		req.add_header('User-Agent', 'xbmc for soap')
		req.add_header('Content-Type', 'application/x-www-form-urlencoded')

		cookie_path = os.path.join(profile, 'cookie')
		if not os.path.exists(cookie_path):
			os.makedirs(cookie_path)
			print '[%s]: os.makedirs(cookie_path=%s)' % (addon_id, cookie_path)

		auth = urllib.urlencode({"login":username, "password":password})
		f = urllib2.urlopen(req, auth)

		for Cook in CJ:
			cookie_file = os.path.join(cookie_path, Cook.name)
			cf = open(cookie_file, 'w')
			cf.write(Cook.value)
			cf.close()

		a = f.read()
		f.close()

		data = json.loads(a)
		if not data["ok"]:
			raise Exception(data["error"])

		token = data["token"]
		save_token(token)

		return token

	except Exception, e:
		print '[%s]: GET EXCEPTION: %s' % (addon_id, e)
		return None

def save_token(token):
	token_path = os.path.join(profile, 'token')
	if not os.path.exists(token_path):
		os.makedirs(token_path)
		print '[%s]: os.makedirs(cookie_path=%s)' % (addon_id, token_path)

	ft = open(token_path + "/soap4.me", "w")
	ft.write(token)
	ft.close()

def get_token():
	token_path = os.path.join(profile, 'token')
	if not os.path.exists(token_path):
		return False

	if not os.path.exists(token_path + "/soap4.me"):
		return False

	ft = open(token_path + "/soap4.me", "r")
	token = ft.read()
	ft.close()

	return token


def GET(token, tu, post=None, cahse_min = False):
	try:
		CJ = cookielib.CookieJar()
		urllib2.install_opener(urllib2.build_opener(urllib2.HTTPCookieProcessor(CJ)))
		req = urllib2.Request(tu)
		req.add_header('User-Agent', 'xbmc for soap')
		req.add_header('Accept-encoding', 'gzip')
		req.add_header('x-api-token', token)

		if post: req.add_header('Content-Type', 'application/x-www-form-urlencoded')

		cookie_path = os.path.join(profile, 'cookie')
		if not os.path.exists(cookie_path):
			os.makedirs(cookie_path)
			print '[%s]: os.makedirs(cookie_path=%s)' % (addon_id, cookie_path)

		cookie_send = {}
		for cookie_fname in os.listdir(cookie_path):
			cookie_file = os.path.join(cookie_path, cookie_fname)
			if os.path.isfile(cookie_file):
				cf = open(cookie_file, 'r')
				cookie_send[os.path.basename(cookie_file)] = cf.read()
				cf.close()
			else: print '[%s]: NOT os.path.isfile(cookie_file=%s)' % (addon_id, cookie_file)

		cookie_string = urllib.urlencode(cookie_send).replace('&','; ')
		req.add_header('Cookie', cookie_string)

		response = urllib2.urlopen(req, post)

		for Cook in CJ:
			cookie_file = os.path.join(cookie_path, Cook.name)
			cf = open(cookie_file, 'w')
			cf.write(Cook.value)
			cf.close()

		a = ""
		if response.info().get('Content-Encoding') == 'gzip':
			buf = StringIO( response.read())
			f = gzip.GzipFile(fileobj=buf)
			a = f.read()
		else:
			a = response.read()
			response.close()

		return a

	except Exception, e:
		print '[%s]: GET EXCEPTION: %s' % (addon_id, e)
		showMessage(tu, e, 5000)
		return None

def soap4me_get_titles():
	try:
		token = get_token()

		if not token:
			token = soap4me_login()

		read_data = soap4me_get_cashe("index", 30)
		if not read_data:

			print "Reload index cache"
			read_data = GET(token, "http://soap4.me/api/soap/")
			if read_data == '{"ok":0}':
				raise Exception("Bad get titles")
			soap4me_save_cashe("index", read_data)

		data = json.loads(read_data)
		return data

	except e:
		raise Exception('[%s]: GET EXCEPTION: %s' % (addon_id, e))
		print '[%s]: GET EXCEPTION: %s' % (addon_id, e)
		return None

def soap4me_get_episodes(sid):
	try:
		token = get_token()

		if not token:
			token = soap4me_login()

		read_data = soap4me_get_cashe("s"+str(sid), 15)
		if not read_data:
			print "Reload %s cache"%str(sid)
			read_data = GET(token, "http://soap4.me/api/episodes/"+str(sid)+"/")
			if read_data == '{"ok":0}':
				raise Exception("Bad token")
			soap4me_save_cashe("s"+str(sid), read_data)

		data = json.loads(read_data)
		return data


	except e:
		raise Exception('[%s]: GET EXCEPTION: %s' % (addon_id, e))
		print '[%s]: GET EXCEPTION: %s' % (addon_id, e)
		return None

def soap4me_get_play(sid, eid, ehash):
	try:
		token = get_token()

		if not token:
			token = soap4me_login()

		myhash = hashlib.md5(str(token)+str(eid)+str(sid)+str(ehash)).hexdigest()
		data = urllib.urlencode({"what": "player", "do": "load", "token":token, "eid":eid, "hash":myhash})


		read_data = GET(token, "http://soap4.me/callback/", data)
		if read_data == '{"ok":0}':
			raise Exception("Soap4me error")

		data = json.loads(read_data)
		if data["ok"] == 1:
			return "http://%s.soap4.me/%s/%s/%s/" % (data["server"], token, eid, myhash)

		raise Exception(data["error"])

	except Exception, e:
		print '[%s]: GET EXCEPTION: %s' % (addon_id, e)
		return None



def soap4me_draw_titles():
	data = soap4me_get_titles()

	for row in data:
		info = {}
		info['title'] = str(row['title'])
		info['plot'] = row['description'].encode('utf-8')
		serial = str(row['sid'])
		img = "http://covers.s4me.ru/soap/big/"+str(row['sid'])+".jpg"

		vtype = 'video'
		IsFolder = True

		uri = '%s?comtype=serial&serial=%s' % (sys.argv[0], urllib.quote_plus(serial))

		li = xbmcgui.ListItem(info['title'], iconImage = img, thumbnailImage = img)

		li.setInfo(type = vtype, infoLabels = info)
		xbmcplugin.addDirectoryItem(h, uri, li, IsFolder)

	xbmcplugin.addSortMethod(h, xbmcplugin.SORT_METHOD_UNSORTED)
	xbmcplugin.addSortMethod(h, xbmcplugin.SORT_METHOD_DATE)
	xbmcplugin.addSortMethod(h, xbmcplugin.SORT_METHOD_DURATION)
	xbmcplugin.addSortMethod(h, xbmcplugin.SORT_METHOD_GENRE)
	xbmcplugin.addSortMethod(h, xbmcplugin.SORT_METHOD_TITLE)
	xbmcplugin.addSortMethod(h, xbmcplugin.SORT_METHOD_VIDEO_RATING)
	xbmcplugin.addSortMethod(h, xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
	xbmcplugin.addSortMethod(h, xbmcplugin.SORT_METHOD_VIDEO_TITLE)
	xbmcplugin.addSortMethod(h, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
	xbmcplugin.addSortMethod(h, xbmcplugin.SORT_METHOD_LABEL)
	xbmcplugin.endOfDirectory(h)

def soap4me_draw_seasons(sid):
	data = soap4me_get_episodes(sid)
	season = {}
	for episode in data:
		if int(episode['season']) not in season:
			season[int(episode['season'])] = episode['season_id']
	# season.sort()
	if len(season) == 1:
		soap4me_draw_episodes(sid,'1')
	else:
		for row in season:
			info = {}
			info['title'] = "Season %s"%str(row)
			img = "http://covers.s4me.ru/season/big/%s.jpg"%season[row]
			IsFolder = True
			vtype = 'video'
			uri = '%s?comtype=season&serial=%s&season=%s' % (sys.argv[0], urllib.quote_plus(str(sid)), urllib.quote_plus(str(row)))
			li = xbmcgui.ListItem(info['title'], iconImage = img, thumbnailImage = img)
			li.setInfo(type = vtype, infoLabels = info)
			xbmcplugin.addDirectoryItem(h, uri, li, IsFolder)

	xbmcplugin.endOfDirectory(h)

def soap4me_draw_episodes(sid,season):
	data = soap4me_get_episodes(sid)
	
	ShowHdIfPossible = __addon__.getSetting('HD')
	
	episode_names = {}
	for episode in data:
		if season == episode['season']:
			if ShowHdIfPossible == 'true':
				if episode['title_en'] not in episode_names.keys():
					episode_names[episode['title_en']] = episode['eid']
				else:
					if episode['quality'] == '720p':
						episode_names[episode['title_en']] = episode['eid']
			else:
				if episode['title_en'] not in episode_names.keys():
					episode_names[episode['title_en']] = episode['eid']
				else:
					if episode['quality'] == 'SD':
						episode_names[episode['title_en']] = episode['eid']
	
	for row in data:
		if season == row['season']:
			print row['eid'],episode_names.values()
			if row['eid'] in episode_names.values():
				info = {}
				info['title'] = "S" + str(row['season']) \
							  + "E" + str(row['episode']) + " | " \
							  + row['quality'].encode('utf-8') + " | " \
							  + row['translate'].encode('utf-8') + " | " \
							  + row['title_en'].encode('utf-8').replace('&#039;', "'").replace("&amp;", "&").replace('&quot;','"')
				info['plot'] = row['spoiler'].encode('utf-8')
				serial = str(sid)
				episode = str(row['eid'])
				ehash = str(row['hash'])
				img = "http://covers.s4me.ru/season/big/%s.jpg"%str(row['season_id'])

				IsFolder = False
				info['season'] = int(row['season'])
				info['episode'] = int(row['episode'])

				vtype = 'video'

				uri = '%s?comtype=play&serial=%s&episode=%s&hash=%s&title=%s' % (sys.argv[0], urllib.quote_plus(serial), urllib.quote_plus(episode), urllib.quote_plus(ehash), urllib.quote_plus(info['title']))

				li = xbmcgui.ListItem(info['title'], iconImage = img, thumbnailImage = img)
				li.setProperty('IsPlayable', 'true')
				li.setInfo(type = vtype, infoLabels = info)
				xbmcplugin.addDirectoryItem(h, uri, li, IsFolder)

	xbmcplugin.addSortMethod(h, xbmcplugin.SORT_METHOD_UNSORTED)
	xbmcplugin.addSortMethod(h, xbmcplugin.SORT_METHOD_DATE)
	xbmcplugin.addSortMethod(h, xbmcplugin.SORT_METHOD_DURATION)
	xbmcplugin.addSortMethod(h, xbmcplugin.SORT_METHOD_GENRE)
	xbmcplugin.addSortMethod(h, xbmcplugin.SORT_METHOD_TITLE)
	xbmcplugin.addSortMethod(h, xbmcplugin.SORT_METHOD_VIDEO_RATING)
	xbmcplugin.addSortMethod(h, xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
	xbmcplugin.addSortMethod(h, xbmcplugin.SORT_METHOD_VIDEO_TITLE)
	xbmcplugin.addSortMethod(h, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
	xbmcplugin.addSortMethod(h, xbmcplugin.SORT_METHOD_LABEL)
	xbmcplugin.endOfDirectory(h)

def soap4me_play(params):
	videourl = soap4me_get_play(params["serial"], params["episode"], params["hash"])
	item = xbmcgui.ListItem(path = videourl)
	item.setInfo(type='video', infoLabels = {'title':params['title']})
	xbmcplugin.setResolvedUrl(h, True, item)
	xbmc.sleep(6000)

def get_params(paramstring):
	param={}
	if len(paramstring)>=2:
		params=paramstring
		cleanedparams=params.replace('?','')
		if (params[len(params)-1]=='/'):
			params=params[0:len(params)-2]
		pairsofparams=cleanedparams.split('&')
		param={}
		for i in range(len(pairsofparams)):
			splitparams={}
			splitparams=pairsofparams[i].split('=')
			if (len(splitparams))==2:
				param[splitparams[0]]=splitparams[1]
	if len(param) > 0:
		for cur in param:
			param[cur] = urllib.unquote_plus(param[cur])
	return param

def addon_main():
	params = {}
	try:
		params = get_params(sys.argv[2])
		type = params["comtype"]
	except:
		type = "index"

	if type == "play":
		soap4me_play(params)
	elif type == "serial":
		soap4me_draw_seasons(params['serial'])
	elif type == "season":
		soap4me_draw_episodes(params['serial'],params['season'])
	else:
		soap4me_draw_titles()