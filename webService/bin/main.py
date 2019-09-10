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
from Catalog import Catalog

from cgi import escape	# Cette library remplace < par &lt;	> par &gt; et & par &amp;
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from django.utils import simplejson as json

cat = Catalog()

### =============================================================================
### Page principale
### =============================================================================
class MainPage(webapp.RequestHandler):

	# ---------------------------------------------------------------
	# Appelé lorsque l'on accède à la page principale
	# ---------------------------------------------------------------
	def get(self):
		write_page_header(self)
		write_page_intro_message(self) 	# affiche le message d'intro
		write_stored_data(self)			# affiche le contenu de la base
		write_page_footer(self)


### =============================================================================
### Tache de cleanup (appelé par Cron)
### =============================================================================
class Cleanup(webapp.RequestHandler):

	# ---------------------------------------------------------------
	# Appelé lorsque l'on accède à la page 
	# ---------------------------------------------------------------
	def get(self):
		self.response.out.write("<html><body>Task Cleanup STARTING<br/>")
		cat.cleanup()
		self.response.out.write("Task Cleanup DONE</body></html>\n")

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
		# Ajout d'un nouveau livre: "create"
		# ----------------------------------------------------------------------------
		if command_list[0] == "create":
			cat.createBook(tag)
			result = ["STORED", tag, command]
		# ----------------------------------------------------------------------------
		# Affectation d'un propriétaire au livre: "owner:toto"
		# ----------------------------------------------------------------------------
		elif command_list[0] == "owner":
			cat.setBookOwner(tag, command_list[1])
			result = ["UPDATED", tag, command]
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
		# Suppression d'un livre (deleted by) : "delete:toto"
		# ----------------------------------------------------------------------------
		elif command_list[0] == "delete":
			cat.removeBook(tag, command_list[1])
			result = ["DELETED", tag, command]
		# ----------------------------------------------------------------------------
		# Réception d'une demande de livre (requested by): "request:joe"
		# ----------------------------------------------------------------------------
		elif command_list[0] == "request":
			cat.requestBook(tag, command_list[1])
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

	# ---------------------------------------------------------------
	# Appelé lorsque l'on accède à la page avec un Browser
	# ---------------------------------------------------------------
	def get(self):
		self.response.out.write('''
		<html><body>
		<form action="/storeavalue" method="post" enctype=application/x-www-form-urlencoded>
			 <p>Tag<input   type="text" name="tag"   /></p>
			 <p>Value<input type="text" name="value" /></p>
			 <input type="hidden" name="fmt" value="html">
			 <input type="submit" value="Store a value">
		</form>
		<br/>
		<p>Examples: <br/>
			9782253121206 create<br/>
			9782707322210 create<br/>
			9782859406370<br/>
			9782070612888<br/>
			9782253049418 Pas de resumé<br/>
			9780345339713 Résumé en coding inconnu<br/>
		</p>
		</body></html>''')

	# ------------------------------------------------------------------------------
	# Appelé lorsque l'on clique sur le bouton "Store a value" (Browser), ou par le smartphone
	# ------------------------------------------------------------------------------
	def post(self):
		tag   = self.request.get('tag')
		value = self.request.get('value')
		# on enleve les " autour de la value, ajoutés par le module AppInventor 'StoreValue'
		if value[0] == '"': value = value[1:-1]
		self.store_a_value(tag, value)


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
		# "isbn:*"	Demande de la Liste complete des ISBN
		# -------------------------------------------------------------------------------
		if commande == "isbn:*":
			responselist = cat.getISBNList()
		# -------------------------------------------------------------------------------
		# "user:*"	Demande de la Liste complete des USERS
		# -------------------------------------------------------------------------------
		elif commande == "user:*":
			responselist = cat.getUserList()
		# -------------------------------------------------------------------------------
		# "user:toto"	Demande de la Liste des ISBN du user TOTO
		# -------------------------------------------------------------------------------
		elif command_list[0] == "user":
			responselist = cat.getBookListOwnedBy(command_list[1])
		# -------------------------------------------------------------------------------
		# "requestedto:toto"	Demande de la Liste des ISBN demandés à TOTO
		# -------------------------------------------------------------------------------
		elif command_list[0] == "requestedto":
			responselist = cat.getBookListRequestedTo(command_list[1])
		# -------------------------------------------------------------------------------
		# "requestedby:toto"	Demande de la Liste des ISBN demandés par TOTO
		# -------------------------------------------------------------------------------
		elif command_list[0] == "requestedby":
			responselist = cat.getBookListRequestedBy(command_list[1])
		# -------------------------------------------------------------------------------
		# "isbn:9700000000:userdata"	Demande des infos sur le livre 
		# -------------------------------------------------------------------------------
		elif command_list[0] == "isbn":
			responselist = cat.getBookInfo(command_list[1])
		# -------------------------------------------------------------------------------
		# "desc:9700000000"				Demande du résumé du livre 
		# -------------------------------------------------------------------------------
		elif command_list[0] == "desc":
			responselist = cat.getBookDescription(command_list[1])
		# -------------------------------------------------------------------------------
		# "pict:9700000000:userdata"	Demande de l'url de la couverture du livre 
		# -------------------------------------------------------------------------------
		elif command_list[0] == "pict":
			responselist = cat.getBookPicture(command_list[1])
		# -------------------------------------------------------------------------------
		# "requirer:9700000000"			Demande du demandeur du livre
		# -------------------------------------------------------------------------------
		elif command_list[0] == "requirer":
			responselist = cat.getBookRequirer(command_list[1])
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
		tag = self.request.get('tag')
		cat.deleteKey(entry_key_string)
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
		This list contains: [title, author, publisher, publication date, thumbnail url]</br>
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
					body {margin-left: 5% ; margin-right: 5%; margin-top: 0.5in; font-family: verdana, arial,"trebuchet ms", helvetica, sans-serif;}
					ul {list-style: disc;}
				</style>
				<title>Tiny Book Catalog</title>
			</head>
			<body>''')
	
# ------------------------------------------------------------------------------
# Generate the page footer
# ------------------------------------------------------------------------------
def write_page_footer(self):
	self.response.out.write('''</body></html>''')
	
# ------------------------------------------------------------------------------
# Generate the page Intro Message
# ------------------------------------------------------------------------------
def write_page_intro_message(self):
	self.response.out.write('''<h2>Tiny-Book-Catalog (App Inventor for Android using TinyWebDB component)</h2>''')
	self.response.out.write('''
		<table border=0>
		<tr valign="top">
		<td><image src="images/customLogo.gif" width="200" hspace="10"></td>
		<td>
			<p>
			This web service is designed to work with <b>App Inventor for Android</b> and the TinyWebDB component. </br>
			The end-goal of this service is to communicate with a mobile app created with App Inventor.
			</p>
			<p>
			This page is an interface to the web service to help programmers with debugging. </br>
			You can invoke the get and store operations by hand, view the existing entries, and also delete individual entries.
			</p>
		</td>
		</tr>
		</table>''')
	
# ------------------------------------------------------------------------------
# Show the tags and values as a table.
# ------------------------------------------------------------------------------
def write_stored_data(self):
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
	entries = cat.getAllItems()
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
		if e.thumbnail: self.response.out.write('<td><a href="%s">link</a></td>' % escape(e.thumbnail))
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
	handler.response.out.write('''<html><body>''')
	handler.response.out.write('''<em>The server will send this to the component:</em><p/>''')
	writer()
	handler.response.out.write('''<p><a href="/"><i>Return to Main Page</i></a>''')
	handler.response.out.write('''</body></html>''')

# ------------------------------------------------------------------------------
# Write to the Web (without checking fmt)
# ------------------------------------------------------------------------------
def WriteToWeb(handler, writer):
	handler.response.headers['Content-Type'] = 'text/html'
	handler.response.out.write('''<html><body>''')
	writer()
	handler.response.out.write('''<p><a href="/"><i>Return to Main Page</i></a>''')
	handler.response.out.write('''</body></html>''')


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
