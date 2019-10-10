#!/usr/bin/env python
# coding: UTF-8
# ==================================================================
# Ce module gère un catalogue de livres.
# ------------------------------------------------------------------
# 07/09/2019 |    | DDL | Version initiale
# ==================================================================

import logging
import google_books
#import amazon_books
import standard_books
import open_books

from google.appengine.ext import db
from google.appengine.ext.db import Key


# -------------------------------------------------------------------------------
# Creation de la table StoredData
# Defining a column as a StringProperty limits individual values to 1500 characters.
# To remove this limit, use a TextProperty instead.
# StringProperty supporte (multiline=True)
# -------------------------------------------------------------------------------
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


# -------------------------------------------------------------------------------
# Classe pour gérer le catalogue de livres
# -------------------------------------------------------------------------------
class catalog():

	# -------------------------------------------------------------------------------
	# Note sur GqlQuery: 
	# .get() retourne le premier élement trouvé
	# .run() retourne un objet itérable avec tous les élements trouvés (recommandé)
	# .fetch() retourne la liste tous les élements trouvés (lenteur)
	# -------------------------------------------------------------------------------

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
			std_data = standard_books.getInfo(isbn)		# on remplit avec des infos par defaut
			self.storeData(entry, std_data)
			google_data = google_books.getInfo(isbn)	# on complète avec des infos de Google
			self.storeData(entry, google_data)
			open_data = open_books.getInfo(isbn)		# on complète avec des infos de OpenLibray
			self.storeData(entry, open_data)
			open_data = open_books.getInfoFull(isbn)	# on complète avec le résumé de OpenLibray
			self.storeData(entry, open_data)
		else:
			# Si elle existe, on met à jour les infos
			google_data = google_books.getInfo(isbn)	# on complète avec des infos de Google
			self.storeData(entry, google_data)
			open_data = open_books.getInfo(isbn)		# on complète avec des infos de OpenLibray
			self.storeData(entry, open_data)
			open_data = open_books.getInfoFull(isbn)	# on complète avec le résumé de OpenLibray
			self.storeData(entry, open_data)

	# ----------------------------------------------------------------------------
	# Positionne le OWNER d'un livre (livre existant)
	# ----------------------------------------------------------------------------
	def setBookOwner(self, isbn, owner):
		entry = db.GqlQuery("SELECT * FROM StoredData WHERE tag = :1", isbn).get()
		if entry:
			entry.owner   = owner
			entry.put()

	# ----------------------------------------------------------------------------
	# Réception d'une demande de livre (ISBN requested by User)
	# ----------------------------------------------------------------------------
	def setBookRequirer(self, isbn, user):
		entry = db.GqlQuery("SELECT * FROM StoredData WHERE tag = :1", isbn).get()
		# Si le livre est connu en base, on positionne le requirer
		if entry:
			entry.requirer   = user
			entry.put()

	# ----------------------------------------------------------------------------
	# Suppression d'un livre (ISBN deleted by User)
	# ----------------------------------------------------------------------------
	def removeBook(self, isbn, user):
		entry = db.GqlQuery("SELECT * FROM StoredData WHERE tag = :1", isbn).get()
		if entry:
			# Si le owner est aussi le user qui demande la suppression: alors on peut la faire
			if entry.owner == user: 
				entry.description = u"Livre de ["+entry.owner+"] supprime par ["+user+"]"
				entry.put()
				entry.delete()

	# -------------------------------------------------------------------------------
	# Renvoie la liste complete des ISBN
	# -------------------------------------------------------------------------------
	def getISBNList(self):
		responselist = list()
		query = db.GqlQuery("SELECT tag FROM StoredData")
		results = query.run(limit=100)
		# for item in query: # est aussi possible, car run() est implicite
		for item in results: 
			responselist.append(item.tag)
		return responselist
		
	# -------------------------------------------------------------------------------
	# REnvoie la liste complete des USERS
	# -------------------------------------------------------------------------------
	def getUserList(self):
		responselist = list()
		query = db.GqlQuery("SELECT DISTINCT owner FROM StoredData")
		results = query.run(limit=100)
		for item in results: 
			responselist.append(item.owner)
		return responselist
		
	# -------------------------------------------------------------------------------
	# "user:toto"	Rebnoir la liste des ISBN du user TOTO
	# -------------------------------------------------------------------------------
	def getBookListOwnedBy(self, user):
		responselist = list()
		query = db.GqlQuery("SELECT * FROM StoredData WHERE owner = :1", user)
		results = query.run(limit=100)
		for item in results: 
			responselist.append(item.tag)
		return responselist
		
	# -------------------------------------------------------------------------------
	# Renvoie la liste des ISBN demandés au User
	# -------------------------------------------------------------------------------
	def getBookListRequestedTo(self, user):
		responselist = list()
		query = db.GqlQuery("SELECT * FROM StoredData WHERE owner = :1", user)
		results = query.run(limit=100)
		for item in results: 
			if not item.requirer: pass
			elif item.requirer == "null": pass
			else: 
				responselist.append(item.tag)
		return responselist
		
	# -------------------------------------------------------------------------------
	# Renvoie la liste  des ISBN demandés par le User
	# -------------------------------------------------------------------------------
	def getBookListRequestedBy(self, user):
		responselist = list()
		query = db.GqlQuery("SELECT * FROM StoredData WHERE requirer = :1", user)
		results = query.run(limit=100)
		for item in results: 
			responselist.append(item.tag)
		return responselist
		
	# -------------------------------------------------------------------------------
	# Renvoie les infos détaillées du livre 
	# -------------------------------------------------------------------------------
	def getBookInfo(self, isbn):
		entry = db.GqlQuery("SELECT * FROM StoredData WHERE tag = :1", isbn).get() 
		if entry:
			title = entry.title
			owner = entry.owner
			author = entry.author
			requirer = entry.requirer
			publisher = entry.publisher
			thumbnail = entry.thumbnail
			publishedDate = entry.publishedDate
		else:
			title = u"titre non trouvé"
			owner = ""
			author = ""
			requirer = ""
			publisher = ""
			thumbnail = ""
			publishedDate = ""
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
			picture = entry.thumbnail
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
	# Delete entry
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
	# Supprime tous les livres sans owner
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
	# On stocke les valeurs en BDD
	# ------------------------------------------------------------------------------
	def storeData(self , entry, book_data):
		if not book_data: return
		if "title"         in book_data : entry.title=book_data.get("title")
		if "author"        in book_data : entry.author=book_data.get("author")
		if "picture"       in book_data : entry.thumbnail=book_data.get("picture")
		if "language"      in book_data : entry.language=book_data.get("language")
		if "publisher"     in book_data : entry.publisher=book_data.get("publisher")
		if "description"   in book_data : entry.description=book_data.get("description")
		if "publishedDate" in book_data : entry.publishedDate=book_data.get("publishedDate")
		entry.put()
		
