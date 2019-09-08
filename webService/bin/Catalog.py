#!/usr/bin/env python
# -*- coding: utf-8 -*-
### ===========================================================================================
### 
### 
### 
### ===========================================================================================
### Author: DDL
### ===========================================================================================

import logging
# from standard_book 
import standard_book

from django.utils import simplejson as json

from google.appengine.api import urlfetch
from google.appengine.ext import db
from google.appengine.ext.db import Key


### ===========================================================================================
### Creation de la table StoredData
### Defining a column as a StringProperty limits individual values to 500 characters.
### To remove this limit, use a TextProperty instead.
### ===========================================================================================
class StoredData(db.Model):
	tag				= db.StringProperty()		# on y stocke le code ISBN
	owner			= db.StringProperty()		# on y stocke le OWNER envoyé par le smartphone
	requirer		= db.StringProperty()		# on y stocke le DEMANDEUR envoyé le smartphone
	title			= db.StringProperty()		# on y stocke le TITLE envoyé par l'API externe
	author			= db.StringProperty()		# on y stocke le AUTHOR envoyé par l'API externe
	publisher		= db.StringProperty()		# on y stocke le PUBLISHER envoyé par l'API externe
	publishedDate	= db.StringProperty()		# on y stocke le PUBLISHEDDATE envoyé par l'API externe
	description		= db.TextProperty()			# on y stocke le DESCRIPTION envoyé par l'API externe
	language		= db.StringProperty()		# on y stocke le LANGUAGE envoyé par l'API externe
	thumbnail		= db.StringProperty()		# on y stocke le THUMBNAIL envoyé par l'API externe
	date			= db.DateTimeProperty(required=True, auto_now=True)	# Creation date


#DefaultDescription = u"Pas de résumé."	# on force en unicode, à cause des accents, pour pouvoir l'affecter à une entry.
# standard_book_api = standard_book_api()


### =============================================================================

# ---------------------------------------------------------------
# Note sur GqlQuery: 
# .get() retourne le premier élement trouvé
# .run() retourne un objet itérable avec tous les élements trouvés (recommandé)
# .fetch() retourne la liste tous les élements trouvés (lenteur)
# ---------------------------------------------------------------
class Catalog():

	def __init__(self): 
		pass

	# ----------------------------------------------------------------------------
	# S'il y a deja une Entry dans la base avec ce tag ISBN: on met à jour le owner
	# ----------------------------------------------------------------------------
	def setBookOwner(self, isbn, owner):
		entry = db.GqlQuery("SELECT * FROM StoredData WHERE tag = :1", isbn).get()
		if entry:
			entry.owner = owner
			entry.put()
	
	# ----------------------------------------------------------------------------
	# Ajout d'un nouveau livre
	# ----------------------------------------------------------------------------
	def createBook(self, isbn):
		# Note: There's a potential readers/writers error here...
		entry = db.GqlQuery("SELECT * FROM StoredData WHERE tag = :1", isbn).get()
		if not entry:
			# Si cette entry n'existe pas, on crée une nouvelle entry
			entry = StoredData(tag = isbn, requirer="null")
			entry.put()
			#self._fillEntryWithDefaultInfo(entry, isbn)
			book_data = standard_book.getInfo(isbn)
			self.storeData(entry, book_data)
			self._fillEntryWithGoogleBooksInfo(entry,isbn)
		else:
			# Si elle existe, on met à jour les infos
			self._fillEntryWithGoogleBooksInfo(entry,isbn)
			pass

	# ----------------------------------------------------------------------------
	# Suppression d'un livre  (ISBN deleted by User)
	# ----------------------------------------------------------------------------
	def removeBook(self, isbn, user):
		# On recupère le owner du livre
		entry = db.GqlQuery("SELECT * FROM StoredData WHERE tag = :1", isbn).get()
		if entry:
			# Si c'est le même user qui demande la suppression: alors on peut la faire
			if entry.owner == user: 
				entry.description = "Livre de ["+entry.owner+"] supprime par ["+user+"]"	# Ne pas mettre d'accents dans ce texte: plantage unicode/ascii
				entry.put()
				entry.delete()

	# ----------------------------------------------------------------------------
	# Réception d'une demande de livre (ISBN requested by User)
	# ----------------------------------------------------------------------------
	def requestBook(self, isbn, user):
		# Ce livre est-t-il bien connu en base ?
		entry = db.GqlQuery("SELECT * FROM StoredData WHERE tag = :1", isbn).get()
		if entry:
			# Si oui
			entry.requirer = user
			entry.put()

	# -----------------------------------------------------------------------------------------------------------
	# Appel de Google Books
	# doc = https://cloud.google.com/appengine/docs/standard/python/issue-requests#Python_Fetching_URLs_in_Python
	# https://www.googleapis.com/books/v1/volumes?q=isbn:9782253121206&country=US
	# -----------------------------------------------------------------------------------------------------------
	def _fillEntryWithGoogleBooksInfo(self, entry, isbn):
		url = "https://www.googleapis.com/books/v1/volumes?q=isbn:"+str(isbn)+"&country=US"
		result = urlfetch.fetch(url)
		'''try:
			if result.status_code == 200:
				self.response.out.write(result.content)
			else:
				self.response.out.write("Error: " + str(result.status_code))
		except urlfetch.InvalidURLError:
			self.response.out.write("URL is an empty string or obviously invalid")
		except urlfetch.DownloadError:
			self.response.out.write("Server cannot be contacted")
		'''
		contents = result.content
		logging.debug('%s '%(contents))
		# -----------------------------------------------------------
		# contents : flux json contenant les infos du livre.
		# -----------------------------------------------------------
		dico = json.loads(contents)
		# Note: On peut aussi stocker dans la base de la façon suivante:
		# entry.update({'title' : dico["items"][0]["volumeInfo"].get("title",""),
		#				'author': dico["items"][0]["volumeInfo"].get("authors",["null"])[0],
		# 				'number': 4,
		#				'bool'	: False,
		#				'text'	: 'some text'})
		if dico.get("totalItems",0) >0:
			if "volumeInfo" in dico["items"][0].keys():
				entry.title			 = dico["items"][0]["volumeInfo"].get("title","")
				entry.author		 = dico["items"][0]["volumeInfo"].get("authors",["null"])[0]	# on prend le premier de la liste d'auteurs
				entry.publisher		 = dico["items"][0]["volumeInfo"].get("publisher","")
				publishedDate  		 = dico["items"][0]["volumeInfo"].get("publishedDate","")
				entry.publishedDate  = publishedDate.split('-')[0]
				entry.language		 = dico["items"][0]["volumeInfo"].get("language","")
				# Description du livre (cad le résumé)
				if "searchInfo" in dico["items"][0].keys(): 
					entry.description = dico["items"][0]["searchInfo"].get("textSnippet",DefaultDescription)
				entry.description = dico["items"][0]["volumeInfo"].get("description",DefaultDescription)
				# Couverture du livre (thumbnail)
				picture_number       = len(entry.title)%5		# valeurs possibles: 0-1-2-3-4
				entry.thumbnail = "old-book-"+str(picture_number)+".jpg"
				if "imageLinks" in dico["items"][0]["volumeInfo"].keys():
					# entry.thumbnail = dico["items"][0]["volumeInfo"]["imageLinks"].get("smallThumbnail","")
					entry.thumbnail	= dico["items"][0]["volumeInfo"]["imageLinks"].get("thumbnail","")
				entry.put()
	
	# -----------------------------------------------------------------------------------------------------------
	# Appel de l'API AWS
	# doc = https://docs.aws.amazon.com/fr_fr/AWSECommerceService/latest/DG/EX_LookupbyISBN.html
	# -----------------------------------------------------------------------------------------------------------
	def _fillEntryWithAWSBooksInfo(self, entry, isbn):
		url = "http://webservices.amazon.com/onca/xml?"
		url += "Service=AWSECommerceService"
		url += "&Operation=ItemLookup"		# ou: &Operation=ItemSearch
		url += "&ResponseGroup=Large"
		url += "&SearchIndex=All"		# ou: &SearchIndex=Books
		url += "&IdType=ISBN"
		url += "&ItemId="+str(isbn)
		url += "&AWSAccessKeyId="+"[Your_AWSAccessKeyID]"
		url += "&AssociateTag="+"[Your_AssociateTag]"
		url += "&Timestamp="+"[YYYY-MM-DDThh:mm:ssZ]"
		url += "&Signature="+"[Request_Signature]"
		result = urlfetch.fetch(url)
		contents = result.content
		logging.debug('%s '%(contents))
		# -----------------------------------------------------------
		# contents : flux xml contenant les infos du livre.
		# -----------------------------------------------------------
	
	# -------------------------------------------------------------------------------
	# on renvoie la liste complete des ISBN
	# -------------------------------------------------------------------------------
	def getISBNList(self):
		query = db.GqlQuery("SELECT tag FROM StoredData")
		results = query.run(limit=100)
		# for item in query: # est aussi possible, car run() est implicite
		for item in results: 
			responselist.append(item.tag)
		return responselist
		
	# -------------------------------------------------------------------------------
	# Liste complete des USERS
	# -------------------------------------------------------------------------------
	def getUserList(self):
		query = db.GqlQuery("SELECT DISTINCT owner FROM StoredData")
		results = query.run(limit=100)
		for item in results: 
			responselist.append(item.owner)
		return responselist
		
	# -------------------------------------------------------------------------------
	# "user:toto"	Liste des ISBN du user TOTO
	# -------------------------------------------------------------------------------
	def getBookListOwnedBy(self, user):
		query = db.GqlQuery("SELECT * FROM StoredData WHERE owner = :1", user)
		results = query.run(limit=100)
		for item in results: 
			responselist.append(item.tag)
		return responselist
		
	# -------------------------------------------------------------------------------
	# Liste des ISBN demandés à TOTO
	# -------------------------------------------------------------------------------
	def getBookListRequestedTo(self, user):
		query = db.GqlQuery("SELECT * FROM StoredData WHERE owner = :1", user)
		results = query.run(limit=100)
		for item in results: 
			if not item.requirer: pass
			elif item.requirer == "null": pass
			else: 
				responselist.append(item.tag)
		return responselist
		
	# -------------------------------------------------------------------------------
	# Liste des ISBN demandés par TOTO
	# -------------------------------------------------------------------------------
	def getBookListRequestedBy(self, user):
		query = db.GqlQuery("SELECT * FROM StoredData WHERE requirer = :1", user)
		results = query.run(limit=100)
		for item in results: 
			responselist.append(item.tag)
		return responselist
		
	# -------------------------------------------------------------------------------
	# Renvoie les infos sur le livre 
	# -------------------------------------------------------------------------------
	def getBookInfo(self, isbn):
		entry = db.GqlQuery("SELECT * FROM StoredData WHERE tag = :1", isbn).get() 
		if entry:
			title = entry.title
			owner = entry.owner
			author = entry.author
			requirer = entry.requirer
			publisher = entry.publisher
			publishedDate = entry.publishedDate
			thumbnail = entry.thumbnail
		else:
			title = "titre non trouvé"
			owner = ""
			author = ""
			requirer = ""
			publisher = ""
			publishedDate = ""
			thumbnail = ""
		# if it is a html request, clean the variables.
		if self.request.get('fmt') == "html":
			if (title): title = escape(title)
			if (owner): owner = escape(owner)
			if (author): author = escape(author)
			if (requirer): requirer = escape(requirer)
			if (publisher): publisher = escape(publisher)
			if (publishedDate): publishedDate = escape(publishedDate)
			if (thumbnail): thumbnail = escape(thumbnail)
		# On remplit la liste des valeurs à retourner à l'application
		return [title,author,publisher,publishedDate,thumbnail,requirer,owner]

		
	# -------------------------------------------------------------------------------
	# Renvoie le résumé du livre (dans une liste)
	# -------------------------------------------------------------------------------
	def getBookDescription(self, isbn):
		entry = db.GqlQuery("SELECT * FROM StoredData WHERE tag = :1", isbn).get() 
		if entry:
			description = entry.description
		else:
			description = ""
		# On remplit la liste des valeurs à retourner à l'application
		return [description]
		
	# -------------------------------------------------------------------------------
	# Renvoie l'url de la couverture du livre (dans une liste)
	# -------------------------------------------------------------------------------
	def getBookPicture(self, isbn):
		entry = db.GqlQuery("SELECT * FROM StoredData WHERE tag = :1", isbn).get() 
		if entry:
			picture = entry.smallThumbnail
		else:
			picture = ""
		# On remplit la liste des valeurs à retourner à l'application
		return [picture]
		
	# -------------------------------------------------------------------------------
	# Renvoie le demandeur du livre, et son propriétaire actuel
	# -------------------------------------------------------------------------------
	def getBookRequirer(self, isbn):
		entry = db.GqlQuery("SELECT * FROM StoredData WHERE tag = :1", isbn).get() 
		if entry:
			requirer = entry.requirer
			owner    = entry.owner
		else:
			requirer = ""
			owner    = ""
		# On remplit la liste des valeurs à retourner à l'application
		return [requirer,owner]

	# -------------------------------------------------------------------------------
	# delete entry
	# -------------------------------------------------------------------------------
	def deleteKey(self, entry_key):
		key = db.Key(entry_key)
		db.run_in_transaction(self.dbSafeDelete, key)

	# ------------------------------------------------------------------------------
	# Delete an item from database (if exists)
	# ------------------------------------------------------------------------------
	def dbSafeDelete(self, key):
		if db.get(key):	db.delete(key)

	# ------------------------------------------------------------------------------
	# Supprime tous les items sans owner
	# ------------------------------------------------------------------------------
	def cleanup(self):
		entries = db.GqlQuery("SELECT * FROM StoredData WHERE owner = NULL")
		for item in entries:
			item.delete()

	# ------------------------------------------------------------------------------
	# Retourne tous les items
	# ------------------------------------------------------------------------------
	def getAllItems(self):
		# This next line is replaced by the one under it, in order to help protect against SQL injection attacks.	
		# Does it help enough?
		#entries = db.GqlQuery("SELECT * FROM StoredData ORDER BY date")
		return StoredData.all().order("-date")	
		
	# ------------------------------------------------------------------------------
	# On stocke les valeurs
	# ------------------------------------------------------------------------------
	def storeData(self , entry, book_data):
		if "title"   in book_data: entry.title=book_data.get("title")
		if "author"  in book_data: entry.author=book_data.get("author")
		if "desc"    in book_data: entry.description=book_data.get("desc")
		if "picture" in book_data: entry.thumbnail=book_data.get("picture")
		entry.put()
		
