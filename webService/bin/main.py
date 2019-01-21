#!/usr/bin/env python
# -*- coding: utf-8 -*-
### ===========================================================================================
### This is a web service for use with App Inventor for Android.
### This particular service stores and retrieves tag-value pairs 
### using the protocol necessary to communicate with the TinyWebDBcomponent of AppInventor.
### ===========================================================================================
### Author: DDL
### ===========================================================================================

import logging
from cgi import escape	# Cette library remplace < par &lt;	> par &gt; et & par &amp;
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.db import Key
from django.utils import simplejson as json
from google.appengine.api import urlfetch

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
	smallThumbnail	= db.StringProperty()		# on y stocke le SMALLTHUMBNAIL envoyé par l'API externe
	thumbnail		= db.StringProperty()		# on y stocke le THUMBNAIL envoyé par l'API externe
	textSnippet		= db.StringProperty(multiline=True)		# on y stocke le TEXTSNIPPET envoyé par l'API externe
	date			= db.DateTimeProperty(required=True, auto_now=True)	# Creation date

### ===========================================================================================
### Creation de la table UserData
### ===========================================================================================
class UserData(db.Model):
	name			= db.StringProperty(required=True)	# Prenom de l'utilisateur
	groupId			= db.StringProperty()				# nom du groupe d'amis
	role			= db.StringProperty()				# member, admin, waiting, closed


### ===========================================================================================
### ===========================================================================================
IntroMessage = '''
<table border=0>
<tr valign="top">
<td><image src="images/customLogo.gif" width="200" hspace="10"></td>
<td>
<p>
This web service is designed to work with <b>App Inventor for Android</b> and the TinyWebDB component. </br>
The end-goal of this service is to communicate with a mobile app created with App Inventor.
</p>
This page is an interface to the web service to help programmers with debugging. </br>
You can invoke the get and store operations by hand, view the existing entries, and also delete individual entries.
</p>
</td> </tr> </table>'''

DefaultDescription = u"Pas de résumé."	# on force en unicode, à cause des accents, pour pouvoir l'affecter à une entry.

### =============================================================================
### Page principale
### =============================================================================
class MainPage(webapp.RequestHandler):

	# ---------------------------------------------------------------
	# Appelé lorsque l'on accède à la page principale
	# ---------------------------------------------------------------
	def get(self):
		write_page_header(self)
		self.response.out.write(IntroMessage) 	# affiche le message d'intro
		show_stored_data(self)					# affiche le contenu de la base
		self.response.out.write('</body></html>')

### =============================================================================
### Tache de cleanup (appelé par Cron)
### =============================================================================
class Cleanup(webapp.RequestHandler):

	# ---------------------------------------------------------------
	# Appelé lorsque l'on accède à la page 
	# ---------------------------------------------------------------
	def get(self):
		self.response.out.write("<html><body>Task Cleanup GET<br/>")
		entries = db.GqlQuery("SELECT * FROM StoredData WHERE owner = NULL")
		for item in entries:
			item.delete()
		self.response.out.write("Cleanup DONE</body></html>\n")

### =============================================================================
### Implementing the operations
### =============================================================================
### Each operation is design to respond to the JSON request or to the Web form, 
### depending on whether the fmt input to the post is json or html.
###
### Each operation is a class.	
### The class includes the method that actually, manipulates the DB, 
### followed by the methods that respond to POST and to GET.
### =============================================================================

### =============================================================================
### Classe liée à la page /StoreAValue
### =============================================================================
class StoreAValue(webapp.RequestHandler):

	# ------------------------------------------------------------------------------
	# Traitement du bouton "Store a value"
	# Note: get() retourne 1 element, fetch() retourne une liste, et run() retourne un objet itérable
	# ------------------------------------------------------------------------------
	def store_a_value(self, tag, command):
		command_list = command.split(':')
		# ----------------------------------------------------------------------------
		# Affectation d'un propriétaire au livre: "owner:toto"
		# ----------------------------------------------------------------------------
		if command_list[0] == "owner":
			entry = db.GqlQuery("SELECT * FROM StoredData WHERE tag = :1", tag).get()
			if entry:
				# S'il y a deja une Entry dans la base avec ce tag ISBN: on met à jour le owner
				entry.owner = command_list[1]
				entry.put()
			result = ["UPDATED", tag, command]
		# ----------------------------------------------------------------------------
		# Ajout d'un nouveau livre
		# ----------------------------------------------------------------------------
		elif command_list[0] == "create":
			# Note: There's a potential readers/writers error here...
			entry = db.GqlQuery("SELECT * FROM StoredData WHERE tag = :1", tag).get()
			if not entry:
				# Si cette entry n'existe pas, on crée une nouvelle entry
				entry = StoredData(tag = tag)
				entry.put()
				self.fillEntryWithDefaultInfo(entry, tag)
				self.fillEntryWithGoogleBooksInfo(entry,tag)
			else:
				# Si elle existe, on met à jour les infos
				self.fillEntryWithGoogleBooksInfo(entry,tag)		
			result = ["STORED", tag, command]
		# ----------------------------------------------------------------------------
		# Appropriation de tous les livres (debug)
		# ----------------------------------------------------------------------------
		elif command_list[0] == "MaintenanceSpecialOp":
			'''
			# On fait une mise à jour de tous les owner !
			query = db.GqlQuery("SELECT * FROM StoredData")
			for item in query: 				# run() est implicite
				item.owner = command_list[1]
				item.put()
			'''
			result = ["CHANGED", tag, command]
		# ----------------------------------------------------------------------------
		# Suppression d'un livre
		# ----------------------------------------------------------------------------
		elif command_list[0] == "delete":
			# On recupère le owner du livre
			entry = db.GqlQuery("SELECT * FROM StoredData WHERE tag = :1", tag).get()
			if entry:
				entry.description = "Livre de ["+entry.owner+"] supprime par ["+command_list[1]+"]"	# Ne pas mettre d'accents dans ce texte: plantage unicode/ascii
				entry.put()
				# Si c'est le même user qui demande la suppression: alors on peut la faire
				if entry.owner == command_list[1]: entry.delete()
			result = ["DELETED", tag, command]
		# ----------------------------------------------------------------------------
		# Réception d'une demande de livre
		# ----------------------------------------------------------------------------
		elif command_list[0] == "request":
			# Ce livre est-t-il bien connu en base ?
			entry = db.GqlQuery("SELECT * FROM StoredData WHERE tag = :1", tag).get()
			if entry:
				# Si oui
				entry.requirer = command_list[1]
				entry.put()
			result = ["UPDATED", tag, command]
		# ----------------------------------------------------------------------------
		# Autres cas
		# ----------------------------------------------------------------------------
		else:
			result = ["UNDEFINED", tag, command]
		# Send back a confirmation message. 
		# The TinyWebDB component ignores the message (it just notes that it was received), 
		# but other components might use this.
		WritePhoneOrWeb(self, lambda : json.dump(result, self.response.out))

	# ------------------------------------------------------------------------------
	# On renseigne les valeurs par défaut
	# ------------------------------------------------------------------------------
	def fillEntryWithDefaultInfo(self, entry, isbn):
		entry.title			 = "Code ISBN: %s"%(isbn)
		entry.author		 = "Livre non reconnu"
		entry.requirer		 = "null"
		entry.description	 = DefaultDescription
		entry.smallThumbnail = "pages.jpg"
		entry.thumbnail		 = "pages.jpg"
		entry.put()

	# -----------------------------------------------------------------------------------------------------------
	# Appel de Google Books
	# doc = https://cloud.google.com/appengine/docs/standard/python/issue-requests#Python_Fetching_URLs_in_Python
	# -----------------------------------------------------------------------------------------------------------
	def fillEntryWithGoogleBooksInfo(self, entry, isbn):
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
					if "searchInfo" in dico["items"][0].keys(): entry.description = dico["items"][0]["searchInfo"].get("textSnippet",DefaultDescription)
					entry.description = dico["items"][0]["volumeInfo"].get("description",DefaultDescription)
					# Couverture du livre (thumbnail pour affichage sur PC, et smallThumbnail pour affichage sur smartphone)
					picture_number       = len(entry.title)%5		# valeurs possibles: 0-1-2-3-4
					entry.smallThumbnail = "old-book-"+str(picture_number)+".jpg"
					if "imageLinks" in dico["items"][0]["volumeInfo"].keys():
						entry.smallThumbnail = dico["items"][0]["volumeInfo"]["imageLinks"].get("smallThumbnail","")
						entry.thumbnail		 = dico["items"][0]["volumeInfo"]["imageLinks"].get("thumbnail","")
					entry.put()
	
	# -----------------------------------------------------------------------------------------------------------
	# Appel de l'API AWS
	# doc = https://docs.aws.amazon.com/fr_fr/AWSECommerceService/latest/DG/EX_LookupbyISBN.html
	# -----------------------------------------------------------------------------------------------------------
	def fillEntryWithAWSBooksInfo(self, entry, isbn):
		url = "http://webservices.amazon.com/onca/xml?"
  		url += "Service=AWSECommerceService"
  		url += "&Operation=ItemLookup"		# ou: &Operation=ItemSearch
  		url += "&ResponseGroup=Large"
  		url += "&SearchIndex=All"		# ou: &SearchIndex=Books
  		url += "&IdType=ISBN"
  		url += "&ItemId="+str(isbn)
  		url += "&AWSAccessKeyId="+[Your_AWSAccessKeyID]
  		url += "&AssociateTag="+[Your_AssociateTag]
  		url += "&Timestamp="+[YYYY-MM-DDThh:mm:ssZ]
  		url += "&Signature="+[Request_Signature]
		result = urlfetch.fetch(url)
		contents = result.content
		logging.debug('%s '%(contents))
		# -----------------------------------------------------------
		# contents : flux xml contenant les infos du livre.
		# -----------------------------------------------------------
	
	# ------------------------------------------------------------------------------
	# Appelé lorsque l'on clique sur le bouton "Store a value", ou par le smartphone
	# ------------------------------------------------------------------------------
	def post(self):
		tag = self.request.get('tag')
		value = self.request.get('value')
		# on enleve les " autour de la value, ajoutés par le module AppInventor 'StoreValue'
		if value[0] == '"': value = value[1:-1]
		self.store_a_value(tag, value)
	
	# ---------------------------------------------------------------
	# Appelé lorsque l'on accède à la page avec un Browser
	# ---------------------------------------------------------------
	def get(self):
		self.response.out.write('''
		<html><body>
		<form action="/storeavalue" method="post" enctype=application/x-www-form-urlencoded>
			 <p>Tag<input type="text" name="tag" /></p>
			 <p>Value<input type="text" name="value" /></p>
			 <input type="hidden" name="fmt" value="html">
			 <input type="submit" value="Store a value">
		</form>
		</body></html>\n''')


### =============================================================================
### Classe liée à la page /GetValue
### Pour la synthaxe du query, voir:
### https://cloud.google.com/appengine/docs/standard/python/datastore/gqlqueryclass
### =============================================================================
class GetValue(webapp.RequestHandler):

	# ---------------------------------------------------------------
	# Traitement du bouton 'Get value'
	# Note sur GqlQuery: 
	# .get() retourne le premier élement trouvé
	# .run() retourne un objet itérable avec tous les élements trouvés (recommandé)
	# .fetch() retourne la liste tous les élements trouvés (lenteur)
	# ---------------------------------------------------------------
	def get_value(self, commande):
		command_list = commande.split(":")
		responselist = []
		# -------------------------------------------------------------------------------
		# "isbn:*"	Liste complete des ISBN
		# -------------------------------------------------------------------------------
		if commande == "isbn:*":
			# on renvoie la liste complete des ISBN
			query = db.GqlQuery("SELECT tag FROM StoredData")
			results = query.run(limit=100)
			# for item in query: # est aussi possible, car run() est implicite
			for item in results: responselist.append(item.tag)
		# -------------------------------------------------------------------------------
		# "user:*"	Liste complete des USERS
		# -------------------------------------------------------------------------------
		elif commande == "user:*":
			query = db.GqlQuery("SELECT DISTINCT owner FROM StoredData")
			results = query.run(limit=100)
			for item in results: responselist.append(item.owner)
		# -------------------------------------------------------------------------------
		# "user:toto"	Liste des ISBN du user TOTO
		# -------------------------------------------------------------------------------
		elif command_list[0] == "user":
			query = db.GqlQuery("SELECT * FROM StoredData WHERE owner = :1", command_list[1])
			results = query.run(limit=100)
			for item in results: responselist.append(item.tag)
		# -------------------------------------------------------------------------------
		# "requestedto:toto"	Liste des ISBN demandés à TOTO
		# -------------------------------------------------------------------------------
		elif command_list[0] == "requestedto":
			query = db.GqlQuery("SELECT * FROM StoredData WHERE owner = :1", command_list[1])
			results = query.run(limit=100)
			for item in results: 
				if not item.requirer: pass
				elif item.requirer == "null": pass
				else: 
					responselist.append(item.tag)
		# -------------------------------------------------------------------------------
		# "requestedby:toto"	Liste des ISBN demandés par TOTO
		# -------------------------------------------------------------------------------
		elif command_list[0] == "requestedby":
			query = db.GqlQuery("SELECT * FROM StoredData WHERE requirer = :1", command_list[1])
			results = query.run(limit=100)
			for item in results: responselist.append(item.tag)
		# -------------------------------------------------------------------------------
		# "isbn:9700000000:userdata"	Renvoie les infos sur le livre 
		# -------------------------------------------------------------------------------
		elif command_list[0] == "isbn":
			entry = db.GqlQuery("SELECT * FROM StoredData WHERE tag = :1", command_list[1]).get() 
			if entry:
				title = entry.title
				owner = entry.owner
				author = entry.author
				requirer = entry.requirer
				publisher = entry.publisher
				publishedDate = entry.publishedDate
				smallThumbnail = entry.smallThumbnail
			else:
				title = "titre non trouvé"
				owner = ""
				author = ""
				requirer = ""
				publisher = ""
				publishedDate = ""
				smallThumbnail = ""
			# if it is a html request, clean the variables.
			if self.request.get('fmt') == "html":
				if (title): title = escape(title)
				if (owner): owner = escape(owner)
				if (author): author = escape(author)
				if (requirer): requirer = escape(requirer)
				if (publisher): publisher = escape(publisher)
				if (publishedDate): publishedDate = escape(publishedDate)
				if (smallThumbnail): smallThumbnail = escape(smallThumbnail)
			# On remplit la liste des valeurs à retourner à l'application
			responselist = [title,author,publisher,publishedDate,smallThumbnail,requirer,owner]
		# -------------------------------------------------------------------------------
		# "desc:9700000000"	Renvoie le résumé du livre 
		# -------------------------------------------------------------------------------
		elif command_list[0] == "desc":
			entry = db.GqlQuery("SELECT * FROM StoredData WHERE tag = :1", command_list[1]).get() 
			if entry:
				description = entry.description
				snippet = entry.textSnippet
			else:
				description = ""
				snippet = ""
			# On remplit la liste des valeurs à retourner à l'application
			if description=="": responselist = [snippet]
			else: responselist = [description]
		# -------------------------------------------------------------------------------
		# "pict:9700000000:userdata"	Renvoie l'url de la couverture du livre 
		# -------------------------------------------------------------------------------
		elif command_list[0] == "pict":
			entry = db.GqlQuery("SELECT * FROM StoredData WHERE tag = :1", command_list[1]).get() 
			if entry:
				picture = entry.smallThumbnail
			else:
				picture = ""
			# On remplit la liste des valeurs à retourner à l'application
			responselist = [picture]
		# -------------------------------------------------------------------------------
		# "requirer:9700000000"	Renvoie le demandeur du livre, et son propriétaire actuel
		# -------------------------------------------------------------------------------
		elif command_list[0] == "requirer":
			entry = db.GqlQuery("SELECT * FROM StoredData WHERE tag = :1", command_list[1]).get() 
			if entry:
				requirer = entry.requirer
				owner    = entry.owner
			else:
				requirer = ""
				owner    = ""
			# On remplit la liste des valeurs à retourner à l'application
			responselist = [requirer,owner]
		# -------------------------------------------------------------------------------
		# Autres cas
		# -------------------------------------------------------------------------------
		else:
			responselist = ["unknown command","","","",""]
		# -------------------------------------------------------------
		# Envoi de la reponse
		# -------------------------------------------------------------
		# On ajoute le label "VALUE" à la réponse Json.
		# The TinyWebDB component makes no use of this, but other programs might.
		WritePhoneOrWeb(self, lambda : json.dump(["VALUE", commande, responselist], self.response.out))
		# Le programme original ne retournait que la valeur de Value
		# WritePhoneOrWeb(self, lambda : json.dump(["VALUE", tag, value], self.response.out))

	# ---------------------------------------------------------------
	# Appelé lorsque l'on clique sur le bouton 'Get value', ou appel de TinyWebDB
	# ---------------------------------------------------------------
	def post(self):
		tag = self.request.get('tag')
		self.get_value(tag)

	# ---------------------------------------------------------------
	# Appelé lorsque l'on accède à la page avec un browser
	# ---------------------------------------------------------------
	def get(self):
		self.response.out.write('''
		<html><body>
		<form action="/getvalue" method="post" enctype=application/x-www-form-urlencoded>
			 <p>Tag<input type="text" name="tag" /></p>
			 <input type="hidden" name="fmt" value="html">
			 <input type="submit" value="Get value">
		</form>
		</body></html>\n''')


### =============================================================================
### The DeleteEntry is called from the Web only, by pressing one of the
### buttons on the main page.	So there's no get method, only a post.
### =============================================================================
class DeleteEntry(webapp.RequestHandler):

	# ---------------------------------------------------------------
	# Appelé lorsque l'on clique sur le bouton
	# ---------------------------------------------------------------
	def post(self):
		logging.debug('/deleteentry?%s\n|%s|' %(self.request.query_string, self.request.body))
		entry_key_string = self.request.get('entry_key_string')
		key = db.Key(entry_key_string)
		tag = self.request.get('tag')
		db.run_in_transaction(dbSafeDelete,key)
		self.redirect('/')


### =============================================================================
### Procedures used to display the main page
### =============================================================================

# ------------------------------------------------------------------------------
# Show the API
# ------------------------------------------------------------------------------
def write_available_operations(self):
	self.response.out.write('''
		<p>Available calls:\n
		<ul>
		<li><a href="/storeavalue">/storeavalue</a>: Stores a data, given a tag (isbn) and a value (command).</li>
		<li><b>value "create:"</b>: Create an entry in the database for this book.</li>
		<li><b>value "owner:john"</b>: Set the owner of the book.</li>
		<li><b>value "deletedby:john"</b>: Remove the book from the database.</li>
		<li><b>value "requestedby:bob"</b>: Set the requirer of the book.</li>
		</br>
		<li><a href="/getvalue">/getvalue</a>: Retrieves a list of information stored under a given tag (isbn).</br>
		<li><b>tag "isbn:*"</b>: returns the list of all isbn in database.</li>
		<li><b>tag "isbn:123456789[:requestid]"</b>: Returns an information list about the book. <i>requestid</i> is optionnal.</li>
		This list contains: [title, author, publisher, publication date, small thumbnail url]</br>
		Returns empty strings if no value is stored.</br>
		<li><b>tag "pict:123456789[:requestid]</b>": Returns the picture url of the book (isbn). <i>requestid</i> is optionnal.</li>
		<li><b>tag "desc:123456789"</b>: Returns the description (abstract) of the book (isbn).</li>
		<li><b>tag "user:*"</b>: Returns the list of all known owners.</li>
		<li><b>tag "user:john"</b>: Returns the list of all isbn which have "john" for owner.</li>
		</ul>''')

# ------------------------------------------------------------------------------
# Generate the page header
# ------------------------------------------------------------------------------
def write_page_header(self):
	self.response.headers['Content-Type'] = 'text/html'
	self.response.out.write('''
		 <html>
		 <head>
		 <style type="text/css">
				body {margin-left: 5% ; margin-right: 5%; margin-top: 0.5in;
				font-family: verdana, arial,"trebuchet ms", helvetica, sans-serif;}
				ul {list-style: disc;}
		 </style>
		 <title>Tiny Book Catalog</title>
		 </head>
		 <body>''')
	self.response.out.write('<h2>Tiny-Book-Catalog (App Inventor for Android using TinyWebDB component)</h2>')

# ------------------------------------------------------------------------------
# Show the tags and values as a table.
# ------------------------------------------------------------------------------
def show_stored_data(self):
	self.response.out.write('''
		<p><table border=1>
			<tr>
				 <th>Tag</th>
				 <th>Owner</th>
				 <th>Title</th>
				 <th>Author</th>
				 <th>PublishedDate</th>
				 <th>Description</th>
				 <th>Image</th>
				 <th>Created (GMT)</th>
			</tr>''')
	# This next line is replaced by the one under it, in order to help protect against SQL injection attacks.	
	# Does it help enough?
	#entries = db.GqlQuery("SELECT * FROM StoredData ORDER BY tag")
	entries = StoredData.all().order("-date")
	for e in entries:
		entry_key_string = str(e.key())
		self.response.out.write('<tr>')
		self.response.out.write('<td>%s</td>' % escape(e.tag))
		if e.owner: self.response.out.write('<td>%s</td>' % escape(e.owner))
		else: self.response.out.write('<td></td>')
		if e.title: self.response.out.write('<td>%s</td>' % escape(e.title))
		else: self.response.out.write('<td></td>')
		if e.author: self.response.out.write('<td>%s</td>' % escape(e.author))
		else: self.response.out.write('<td></td>')
		if e.publishedDate: self.response.out.write('<td>%s</td>' % escape(e.publishedDate))
		else: self.response.out.write('<td></td>')
		if e.description: self.response.out.write('<td>%s</td>' % escape(e.description))
		else: self.response.out.write('<td></td>')
		if e.smallThumbnail: self.response.out.write('<td><a href="%s">link</a></td>' % escape(e.smallThumbnail))
		else: self.response.out.write('<td></td>')
		self.response.out.write('<td><font size="-1">%s</font></td>\n' % e.date.ctime())
		self.response.out.write('''
			<td><form action="/deleteentry" method="post" enctype=application/x-www-form-urlencoded>
				<input type="hidden" name="entry_key_string" value="%s">
				<input type="hidden" name="tag" value="%s">
				<input type="hidden" name="fmt" value="html">
				<input type="submit" style="background-color: red" value="Delete"></form>
			</td>\n''' %(entry_key_string, escape(e.tag)))
		self.response.out.write('</tr>')
	self.response.out.write('</table>')



### =============================================================================
### Utility procedures for generating the output
### =============================================================================

# ------------------------------------------------------------------------------
# Write response to the smartphone or to the Web depending on fmt.
#	 Handler is an appengine request handler.	
#	 Writer is a thunk (i.e. a procedure of no arguments) that does the write when invoked.
# ------------------------------------------------------------------------------
def WritePhoneOrWeb(handler, writer):
	if handler.request.get('fmt') == "html":
		WritePhoneOrWebToWeb(handler, writer)
	else:
		handler.response.headers['Content-Type'] = 'application/jsonrequest'
		writer()

# ------------------------------------------------------------------------------
# Result when writing to the Web
# ------------------------------------------------------------------------------
def WritePhoneOrWebToWeb(handler, writer):
	handler.response.headers['Content-Type'] = 'text/html'
	handler.response.out.write('<html><body>')
	handler.response.out.write('''<em>The server will send this to the component:</em><p/>''')
	writer()
	handler.response.out.write('''<p><a href="/"><i>Return to Main Page</i></a>''')
	handler.response.out.write('</body></html>')

# ------------------------------------------------------------------------------
# Write to the Web (without checking fmt)
# ------------------------------------------------------------------------------
def WriteToWeb(handler, writer):
	handler.response.headers['Content-Type'] = 'text/html'
	handler.response.out.write('<html><body>')
	writer()
	handler.response.out.write('''<p><a href="/"><i>Return to Main Page</i></a>''')
	handler.response.out.write('</body></html>')

# ------------------------------------------------------------------------------
# Delete an item from database (if exists)
# ------------------------------------------------------------------------------
def dbSafeDelete(key):
	if db.get(key):	db.delete(key)


# ------------------------------------------------------------------------------
# Assign a class to each URL
# ------------------------------------------------------------------------------
application = webapp.WSGIApplication([('/',              MainPage),
									  ('/storeavalue',   StoreAValue),
									  ('/deleteentry',   DeleteEntry),
									  ('/getvalue',      GetValue),
									  ('/tasks/cleanup', Cleanup)  ],
									debug=True)

# ------------------------------------------------------------------------------
# Main program
# ------------------------------------------------------------------------------
def main():
	run_wsgi_app(application)

# ------------------------------------------------------------------------------
# Execution
# ------------------------------------------------------------------------------
if __name__ == '__main__':
	main()
