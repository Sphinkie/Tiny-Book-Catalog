#!/usr/bin/env python
# coding: UTF-8
# ==================================================================
# Ce module retourne des valeurs pour un livre, issues de OpenLibrary
# Voir la description de l'API : https://openlibrary.org/developers/api
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
import urllib2
from django.utils import simplejson as json

# ------------------------------------------------------------------------------
# Demande des infos sur le livre
# ------------------------------------------------------------------------------
def getInfo(isbn):
	data = dict()
	data_dico = dict()
	url_json = "https://openlibrary.org/api/books?bibkeys=ISBN:"+str(isbn)+"&format=json&jscmd=data"
	try:
		result = urllib2.urlopen(url_json)
		contents = result.read()
		logging.debug('Received from openlibrary with jscmd=data: %s '%(contents))
	except urllib2.URLError:
		logging.exception("Exception while fetching url %s"%url_json)
		return data
	# Analyse des data recues
	dico = json.loads(contents)
	if len(dico)>0:
		if "ISBN:"+isbn in dico.keys():
			data_dico = dico["ISBN:"+isbn]
			if "publish_date" in data_dico.keys(): data["publishedDate"] = data_dico["publish_date"][-4:]
			if "publishers"   in data_dico.keys(): data["publisher"] = data_dico["publishers"][0]["name"]
			if "cover"        in data_dico.keys(): data["picture"] = data_dico["cover"]["medium"]
			if "authors"      in data_dico.keys(): data["author"]= data_dico["authors"][0]["name"]
			if "title"        in data_dico.keys(): data["title"] = data_dico["title"]
	return data

# ------------------------------------------------------------------------------
# Demande des infos completes sur le livre (il y a parfois un résumé en plus)
# ------------------------------------------------------------------------------
def getInfoFull(isbn):
	data = dict()
	url_json = "https://openlibrary.org/api/books?bibkeys=ISBN:"+str(isbn)+"&format=json"
	try:
		result = urllib2.urlopen(url_json)
		contents = result.read()
		logging.debug('Received from openlibrary: %s '%(contents))
	except urllib2.URLError:
		logging.exception("Exception while fetching url %s"%url_json)
		# if result: logging.error("Error: " + str(result.status_code))
		return data
	# -----------------------------------------------------------
	# contents : var_OLBookInfo = {flux json};
	# -----------------------------------------------------------
	dico = json.loads(contents)
	if len(dico)>0:
		if "info_url" in dico["ISBN:"+isbn].keys(): 
			info_url = dico["ISBN:"+isbn]["info_url"]
			getTitleInfo(info_url, data)
		if "thumbnail_url" in dico["ISBN:"+isbn].keys():
			thumbnail_url = dico["ISBN:"+isbn]["thumbnail_url"]
			getCoverInfo(thumbnail_url, data)
	return data

# ------------------------------------------------------------------------------
# Extraction des informations de info_url. On les met dans le dico 'data'
# ------------------------------------------------------------------------------
def getTitleInfo(url, data):
	# url est du type: https://openlibrary.org/books/OL8984046M/Les_perroquets
	url_path = url.split("/")
	# on transforme en: https://openlibrary.org/books/OL8984046M.json
	url_json = url_path[0]+"//"+url_path[2]+"/"+url_path[3]+"/"+url_path[4]+".json"
	try:
		result = urllib2.urlopen(url_json)
		contents = result.read()
		logging.debug('Received from openlibrary: %s '%(contents))
	except urllib2.URLError:
		logging.exception("Exception while fetching url %s"%url_json)
		return
	dico = json.loads(contents)
	if len(dico)>0:
		if "title"        in dico.keys(): data["title"] = dico["title"]
		if "publishers"   in dico.keys(): data["publisher"] = dico["publishers"][0]
		if "publish_date" in dico.keys(): data["publishedDate"] = dico["publish_date"][-4:]
		if "languages"    in dico.keys(): data["language"] = str(dico["languages"][0]["key"]).split("/")[2]
		if "description"  in dico.keys(): data["description"] = dico["description"]["value"]
		if "authors"      in dico.keys(): 
			author_url = dico["authors"][0]["key"]
			getAuthorInfo(author_url, data)

# ------------------------------------------------------------------------------
# Extraction des informations de l'auteur
# ------------------------------------------------------------------------------
def getAuthorInfo(url, data):
	# url est du type: /authors/OL1980306A
	url_json=str("https://openlibrary.org"+url+".json")
	try:
		result = urllib2.urlopen(url_json)
		contents = result.read()
		logging.debug('Received from openlibrary: %s '%(contents))
	except urllib2.URLError:
		logging.exception("Exception while fetching url %s"%url_json)
		return
	dico = json.loads(contents)
	if len(dico)>0:
		data["author"] = dico["name"]
	
# ------------------------------------------------------------------------------
# Extraction des informations de couverture
# ------------------------------------------------------------------------------
def getCoverInfo(url_S, data):
	# url est du type: https://covers.openlibrary.org/b/id/990870-S.jpg
	# Note: on a aussi l'info dans la balise Covers du flux Json
	url_M = url_S.replace("-S.jpg", "-M.jpg")
	# on prend l'image de taille M (on a: S M L)
	data["picture"] = url_M

# ------------------------------------------------------------------------------
# Execution
# ------------------------------------------------------------------------------
if __name__ == '__main__':

	print (getInfo("9782253121206"))
