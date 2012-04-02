#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os, xbmcaddon
__settings__ = xbmcaddon.Addon(id='plugin.video.soap4me')
sys.path.append(os.path.join(__settings__.getAddonInfo('path').replace(';', ''), 'resources', 'lib'))

if (__name__ == "__main__" ):
	import addon
	addon.addon_main()