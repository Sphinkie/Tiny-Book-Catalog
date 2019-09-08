#!/usr/bin/env python
# coding: UTF-8
# ==================================================================
# Ce module retourne des valeurs pour un livre, issues de OpenLibrary
# ------------------------------------------------------------------
# 08/09/2019 |    | DDL | Version initiale
# ==================================================================
#
# Exemple de livre inconnu, on a : var _OLBookInfo = {};
#
# Exemple nominal: 
# https://openlibrary.org/api/books?bibkeys=ISBN:9782859406370
# var _OLBookInfo = {"ISBN:9782859406370": 
#                            {	"bib_key": "ISBN:9782859406370", 
#								"preview": "noview", 
#								"thumbnail_url": "https://covers.openlibrary.org/b/id/990870-S.jpg",
#								"preview_url": "https://openlibrary.org/books/OL8984046M/L'\u00eele_des_perroquets", 
# 								"info_url": "https://openlibrary.org/books/OL8984046M/L'\u00eele_des_perroquets"     }
#					};
# Il faut alors aller sur l'URL : https://openlibrary.org/books/OL8984046M.json
# On a un flux json
# {	"publishers": ["Ph\u00e9bus"], 
#  	"physical_format": "Mass Market Paperback", 
#	"key": "/books/OL8984046M", 
#	"weight": "9.9 ounces", 
#	"title": "L'\u00eele des perroquets", 
#	"identifiers": {"librarything": ["5348098"], "goodreads": ["156736"]}, 
#	"isbn_13": ["9782859406370"], 
#	"covers": [990870], 
#	"created": {"type": "/type/datetime", "value": "2008-04-30T09:38:13.731961"}, 
#	"languages": [{"key": "/languages/fre"}], 
#	"isbn_10": ["2859406379"], "latest_revision": 7, 
#	"last_modified": {"type": "/type/datetime", "value": "2011-04-25T20:10:14.808025"}, 
#	"authors": [{"key": "/authors/OL1980306A"}], 
#	"publish_date": "September 1, 1999", 
#	"oclc_numbers": ["468418530"], "works": [{"key": "/works/OL7054263W"}], "type": {"key": "/type/edition"}, "physical_dimensions": "6.8 x 4.8 x 0.8 inches", "revision": 7}
#
# https://openlibrary.org/authors/OL1980306A.json
# {	"name": "Robert Margerit", 
#	"personal_name": "Robert Margerit", 
#	"last_modified": {"type": "/type/datetime", "value": "2008-08-22 04:38:47.44964"}, "key": "/authors/OL1980306A", 
#	"birth_date": "1910", "type": {"key": "/type/author"}, "id": 7096704, "revision": 2}
#
# https://covers.openlibrary.org/b/id/990870-S.jpg	(40x60)
# https://covers.openlibrary.org/b/id/990870-M.jpg	(180x260)
# https://covers.openlibrary.org/b/id/990870-L.jpg	(324x476)



import logging
from google.appengine.api import urlfetch
from django.utils import simplejson as json


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
def getInfo(isbn):
	data = dict()
	url = "https://openlibrary.org/api/books?bibkeys=ISBN:"+str(isbn)
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
	print(str(url)+"<br/>")
	print(str(contents)+"<br/>")
	print("</html>")
	'''
	# -----------------------------------------------------------
	# contents : var_OLBookInfo = {flux json};
	# -----------------------------------------------------------
	(variable, flux_jason) = contents.split("=")
	# on enlève le ; final
	dico = json.loads(flux_jason[0:-1])
	if len(dico)>0:
		info_url = dico["ISBN:"+isbn]["info_url"]
		thumbnail_url = dico["ISBN:"+isbn]["thumbnail_url"]
		data["description"] = info_url
		getBookInfo(info_url, data)
		getCoverInfo(thumbnail_url, data)
	return data

# ------------------------------------------------------------------------------
# Extraction des informations de info_url
# ------------------------------------------------------------------------------
def getBookInfo(url, data):
	# url est du type: https://openlibrary.org/books/OL8984046M/Les_perroquets
	url_path = url.split("/")
	url_json = url_path[0]+"//"+url_path[2]+"/"+url_path[3]+"/"+url_path[4]+".json"
	result = urlfetch.fetch(url_json)
	contents = result.content
	logging.debug('%s '%(contents))
	dico = json.loads(contents)
	if len(dico)>0:
		data["title"] = dico["title"]
		data["publisher"] = dico["publishers"][0]
		data["publishedDate"] = dico["publish_date"][-4:]
		data["language"] = str(dico["languages"][0]["key"]).split("/")[2]
		author_url = dico["authors"][0]["key"]
		getAuthorInfo(author_url, data)

# ------------------------------------------------------------------------------
# Extraction des informations de l'auteur
# ------------------------------------------------------------------------------
def getAuthorInfo(url, data):
	# url est du type: /authors/OL1980306A
	url_json=str("https://openlibrary.org"+url+".json")
	result = urlfetch.fetch(url_json)
	contents = result.content
	logging.debug('%s '%(contents))
	dico = json.loads(contents)
	if len(dico)>0:
		data["author"] = dico["name"]
	
# ------------------------------------------------------------------------------
# Extraction des informations de couverture
# ------------------------------------------------------------------------------
def getCoverInfo(url_S, data):
	# url est du type: https://covers.openlibrary.org/b/id/990870-S.jpg
	# on a aussi l'info dans la balise Covers du flux Json
	url_M = url_S.replace("-S.jpg", "-M.jpg")
	# on prend l'image de taille M (on a: S M L)
	data["picture"] = url_M

# ------------------------------------------------------------------------------
# Execution
# ------------------------------------------------------------------------------
if __name__ == '__main__':

	print (getInfo("9782253121206"))
