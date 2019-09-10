#!/usr/bin/env python
# coding: UTF-8
# ==================================================================
# Ce module retourne des valeurs pour un livre, issues de googleapis.com
# ------------------------------------------------------------------
# 07/09/2019 |    | DDL | Version initiale
# ==================================================================

import logging
from google.appengine.api import urlfetch
from django.utils import simplejson as json

# -----------------------------------------------------------------------------------------------------------
# Appel de Google Books
# doc = https://cloud.google.com/appengine/docs/standard/python/issue-requests#Python_Fetching_URLs_in_Python
# https://www.googleapis.com/books/v1/volumes?q=isbn:9782253121206&country=US
# -----------------------------------------------------------------------------------------------------------

def getInfo(isbn):
	data = dict()
	url = "https://www.googleapis.com/books/v1/volumes?q=isbn:"+str(isbn)+"&country=US"
	try:
		result = urlfetch.fetch(url)
		if result.status_code == 200:
			contents = result.content
			logging.debug('%s '%(contents))
		else:
			print("Error: " + str(result.status_code))
			return data
	except urlfetch.InvalidURLError:
		print("URL is an empty or invalid string")
	except urlfetch.DownloadError:
		print("<html>Server cannot be contacted</html>")
	'''
	print("<html>")
	print(str(url)+"\n")
	print(str(result)+"\n")
	print(str(contents)+"\n")
	print("</html>")
	'''
	# -----------------------------------------------------------
	# contents : flux json contenant les infos du livre.
	# -----------------------------------------------------------
	dico = json.loads(contents)
	if dico.get("totalItems",0)>0 :
		if "volumeInfo" in dico['items'][0].keys():
			data["title"]		 = dico['items'][0]['volumeInfo'].get("title","")
			data["author"]		 = dico['items'][0]['volumeInfo'].get("authors",["null"])[0]	# on prend le premier de la liste d'auteurs
			data["publisher"]	 = dico['items'][0]['volumeInfo'].get("publisher","")
			publishedDate  		 = dico['items'][0]['volumeInfo'].get("publishedDate","")
			data["publishedDate"]= publishedDate.split('-')[0]
			data["language"]	 = dico['items'][0]['volumeInfo'].get("language","")
			# Description du livre (cad le résumé)
			if "searchInfo" in dico['items'][0].keys(): 
				data["description"] = dico['items'][0]['searchInfo'].get("textSnippet",u"Pas de résumé")	# unicode
			data["description"] = dico['items'][0]['volumeInfo'].get("description",u"Pas de résumé")		# unicode
			# Couverture du livre
			picture_number    = len(data["title"])%5		# valeurs possibles: 0-1-2-3-4
			data["picture"] = "old-book-"+str(picture_number)+".jpg"
			if "imageLinks" in dico['items'][0]['volumeInfo'].keys():
				# data["picture"] = dico['items'][0]['volumeInfo']['imageLinks'].get("smallThumbnail","")
				data["picture"]	= dico['items'][0]['volumeInfo']['imageLinks'].get("thumbnail","")
	return data
		

# ------------------------------------------------------------------------------
# Execution
# ------------------------------------------------------------------------------
if __name__ == '__main__':

	print (getInfo("9782253121206"))
