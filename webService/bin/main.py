#!/usr/bin/env python
### =============================================================================
### This is a web service for use with App Inventor for Android.
### This particular service stores and retrieves tag-value pairs 
### using the protocol necessary to communicate with the TinyWebDBcomponent of AppInventor.
### =============================================================================
### Author: DDL
### =============================================================================

import logging
from cgi import escape	# remplace < par &lt;  > par &gt; et & par &amp;
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.db import Key
from django.utils import simplejson as json
from google.appengine.api import urlfetch

### =============================================================================
### Creation des colonnes de la table StoredData
### =============================================================================
class StoredData(db.Model):
  tag     = db.StringProperty()						# on y stocke le code ISBN
  value   = db.StringProperty(multiline=True)		# on y stocke le OWNER envoyé par le smartphone
  # Defining value as a string property limits individual values to 500 characters.
  # To remove this limit, define value to be a text property instead, 
  # by commenting out the previous line and replacing it by this one:
  # value db.TextProperty()
  date           = db.DateTimeProperty(required=True, auto_now=True)
  title          = db.StringProperty()		# on y stocke le TITLE envoyé par l'API externe
  author         = db.StringProperty()		# on y stocke le AUTHOR envoyé par l'API externe
  publisher      = db.StringProperty()		# on y stocke le PUBLISHER envoyé par l'API externe
  publishedDate  = db.StringProperty()		# on y stocke le PUBLISHEDDATE envoyé par l'API externe
  description    = db.TextProperty()		# on y stocke le DESCRIPTION envoyé par l'API externe
  language       = db.StringProperty()		# on y stocke le LANGUAGE envoyé par l'API externe
  smallThumbnail = db.StringProperty()		# on y stocke le SMALLTHUMBNAIL envoyé par l'API externe
  thumbnail      = db.StringProperty()		# on y stocke le THUMBNAIL envoyé par l'API externe
  textSnippet    = db.StringProperty()		# on y stocke le TEXTSNIPPET envoyé par l'API externe
  


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


### =============================================================================
### Page principale
### =============================================================================
class MainPage(webapp.RequestHandler):

  # ---------------------------------------------------------------
  # Appelé lorsque l'on accède à la page principale
  # ---------------------------------------------------------------
  def get(self):
    write_page_header(self);
    self.response.out.write(IntroMessage) 	# affiche le message d'intro
    write_available_operations(self)		# affiche la liste des operations possibles
    show_stored_data(self)					# affiche le contenu de la base
    self.response.out.write('</body></html>')

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
  # ------------------------------------------------------------------------------
  def store_a_value(self, tag, command):
    # ----------------------------------------------------------------------------
    # Affectation d'un propriétaire au livre: ""owner:toto""
    # ----------------------------------------------------------------------------
    if command[0:6]=="owner:":
      if entry:
        # S'il y a deja une Entry dans la base avec ce tag ISBN: on met à jour le owner
        # (en enlevant les quillemets autour du nom
        entry.value = command[7:-1]
    # ----------------------------------------------------------------------------
    # Ajout d'un nouveau livre
    # ----------------------------------------------------------------------------
    else:
      # Note: There's a potential readers/writers error here...
      entry = db.GqlQuery("SELECT * FROM StoredData WHERE tag = :1", tag).get()
      # Si cette entry n'existe pas, on crée une nouvelle Entry
      if not entry:  entry = StoredData(tag = tag)
      entry.put()
      
      # appel API externe
      url = "https://www.googleapis.com/books/v1/volumes?q=isbn:"+str(tag)+"&country=US"
      ## ----------------
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
      logging.debug('dico %s '%(dico))
      # "description"
      if dico.get("totalItems",0)>0:
        if "volumeInfo" in dico["items"][0].keys():
          entry.title         = dico["items"][0]["volumeInfo"].get("title","")
          entry.author        = dico["items"][0]["volumeInfo"].get("authors",["Unknown"])[0]	# on prend le premier de la liste d'auteurs
          entry.publisher     = dico["items"][0]["volumeInfo"].get("publisher","")
          entry.publishedDate = dico["items"][0]["volumeInfo"].get("publishedDate","")
          entry.language      = dico["items"][0]["volumeInfo"].get("language","FR")
          entry.description   = dico["items"][0]["volumeInfo"].get("description","")
          if "imageLinks" in dico["items"][0]["volumeInfo"].keys():
            entry.smallThumbnail = dico["items"][0]["volumeInfo"]["imageLinks"].get("smallThumbnail","")
            entry.thumbnail      = dico["items"][0]["volumeInfo"]["imageLinks"].get("thumbnail","")
          if "searchInfo" in dico["items"][0].keys():
            abstract = dico["items"][0]["searchInfo"].get("textSnippet","")
            # abstract.encode("UTF-16LE")				# Ca ne change rien
            abstract.replace("&#39;","'") 			# ne marche pas (on a &#39; à la place des ')
            entry.textSnippet = abstract
        entry.put()
      # print ("</br>")
      # Send back a confirmation message. 
      # The TinyWebDB component ignores the message (it just notes that it was received), 
      # but other components might use this.
      result = ["STORED", tag, command]
      WritePhoneOrWeb(self, lambda : json.dump(result, self.response.out))
  
  # ---------------------------------------------------------------
  # Appelé lorsque l'on clique sur le bouton "Store a value", ou par le smartphone
  # ---------------------------------------------------------------
  def post(self):
    tag = self.request.get('tag')
    value = self.request.get('value')
    # on enleve les " autour du tag
    if tag[0]=='"': tag = tag[1:-1]
    self.store_a_value(tag, value)
  
  # ---------------------------------------------------------------
  # Appelé lorsque l'on accède à la page
  # ---------------------------------------------------------------
  def get(self):
    self.response.out.write('''
    <html><body>
    <form action="/storeavalue" method="post" enctype=application/x-www-form-urlencoded>
       <p>Tag<input type="text" name="tag" /></p>
       <p>Value<input type="text" name="value" /></p>
       <input type="hidden" name="fmt" value="html">
       <input type="submit" value="Store a value">
    </form></body></html>\n''')


### =============================================================================
### Classe liée à la page /GetValue
### Pour la synthaxe du query, voir:
### https://cloud.google.com/appengine/docs/standard/python/datastore/gqlqueryclass
### get() return 1 element, fetch() returne une liste, et run() retourne un resultat itérable
### =============================================================================
class GetValue(webapp.RequestHandler):

  # ---------------------------------------------------------------
  # Traitement du bouton 'Get value'
  # ---------------------------------------------------------------
  def get_value(self, commande):
    command = commande.split(":")
    responselist = []
    # -------------------------------------------------------------
    # "isbn:*"	Liste complete des ISBN
    # -------------------------------------------------------------
    if commande == "isbn:*":
      # on renvoie la liste complete des ISBN
      query = db.GqlQuery("SELECT tag FROM StoredData")
      results = query.run(limit=100)
      # for item in query: # est aussi possible, car run() est implicite
      for item in results: responselist.append(item.tag)
    # -------------------------------------------------------------
    # "user:*"		Liste complete des USERS
    # -------------------------------------------------------------
    elif commande == "user:*":
      query = db.GqlQuery("SELECT DISTINCT value FROM StoredData")
      results = query.fetch(limit=100)
      for item in results: responselist.append(item.value)
    # -------------------------------------------------------------
    # "user:toto"	Liste des ISBN du user TOTO
    # -------------------------------------------------------------
    elif commande[0:5] == "user:":
      query = db.GqlQuery("SELECT * FROM StoredData WHERE value = :1", '"'+commande[5:]+'"')
      results = query.run(limit=100)
      for item in results: responselist.append(item.tag)
    # -------------------------------------------------------------
    # "isbn:9700000000:request_id"	Renvoie les infos sur le livre 
    # -------------------------------------------------------------
    elif commande[0:5] == "isbn:":
      entry = db.GqlQuery("SELECT * FROM StoredData WHERE tag = :1", command[1]).get() 
      if entry:
        title = entry.title
        author = entry.author
        publisher = entry.publisher
        publishedDate = entry.publishedDate
        smallThumbnail = entry.smallThumbnail
      else:
        title = "titre non trouvé"
        author = "-"
        publisher = "-"
        publishedDate = "-"
        smallThumbnail = ""
      # if it is a html request, clean the variables.
      if self.request.get('fmt') == "html":
        if (title): title = escape(title)
        if (author): owner = escape(author)
        if (publisher): publisher = escape(publisher)
        if (publishedDate): publishedDate = escape(publishedDate)
        if (smallThumbnail): smallThumbnail = escape(smallThumbnail)
      # On remplit la liste des valeurs à retourner à l'application
      responselist = [title,author,publisher,publishedDate,smallThumbnail]
    # -------------------------------------------------------------
    # "desc:9700000000"	Renvoie le résumé du livre 
    # -------------------------------------------------------------
    elif commande[0:5] == "desc:":
      entry = db.GqlQuery("SELECT * FROM StoredData WHERE tag = :1", command[1]).get() 
      if entry:
        description = entry.description
        snippet = entry.textSnippet
      else:
        description = ""
        snippet = ""
      # On remplit la liste des valeurs à retourner à l'application
      if description=="": responselist = [snippet]
      else: responselist = [description]
    # -------------------------------------------------------------
    # "pict:9700000000"	Renvoie l'url de la couverture du livre 
    # -------------------------------------------------------------
    elif commande[0:5] == "pict:":
      entry = db.GqlQuery("SELECT * FROM StoredData WHERE tag = :1", command[1]).get() 
      if entry:
        picture = entry.smallThumbnail
      else:
        picture = ""
      # On remplit la liste des valeurs à retourner à l'application
      responselist = [picture]
    # -------------------------------------------------------------
    # Autres cas
    # -------------------------------------------------------------
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
  # Appelé lorsque l'on clique sur le bouton 'Get value'
  # ---------------------------------------------------------------
  def post(self):
    tag = self.request.get('tag')
    self.get_value(tag)

  # ---------------------------------------------------------------
  # Appelé lorsque l'on accède à la page
  # ---------------------------------------------------------------
  def get(self):
    self.response.out.write('''
    <html><body>
    <form action="/getvalue" method="post" enctype=application/x-www-form-urlencoded>
       <p>Tag<input type="text" name="tag" /></p>
       <input type="hidden" name="fmt" value="html">
       <input type="submit" value="Get value">
    </form></body></html>\n''')


### =============================================================================
### The DeleteEntry is called from the Web only, by pressing one of the
### buttons on the main page.  So there's no get method, only a post.
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
    <li><a href="/storeavalue">/storeavalue</a>: Stores a data, given a tag (isbn) and a value (owner).</li>
    <li><a href="/getvalue">/getvalue</a>: Retrieves the value (list)stored under a given tag (isbn).  Returns the empty string if no value is stored.</br>
    The list contains: [title, author, publisher, publishedDate, small thumbnail url]</br>
    The list does not contain: image url, description.</li>
    <li>tag "isbn:*": returns the list of all tags (isbn) in database.</li>
    <li>tag "isbn:123456789[:requestid]": returns information list about this book (isbn). <i>requestid</i> is optionnal.</li>
    <li>tag "*user:*": returns the list of all known owners.</li>
    <li>tag "*user:john": returns the list of all tags (isbn) which have "john" for owner.</li>
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
  self.response.out.write('<h2>Tiny-Book-Catalog (App Inventor for Android - using TinyWebDB component)</h2>')

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
         <th>publishedDate</th>
         <th>description</th>
         <th>image</th>
         <th>Created (GMT)</th>
      </tr>''')
  # This next line is replaced by the one under it, in order to help
  # protect against SQL injection attacks.  Does it help enough?
  #entries = db.GqlQuery("SELECT * FROM StoredData ORDER BY tag")
  entries = StoredData.all().order("-tag")
  for e in entries:
    entry_key_string = str(e.key())
    self.response.out.write('<tr>')
    self.response.out.write('<td>%s</td>' % escape(e.tag))
    if e.value: self.response.out.write('<td>%s</td>' % escape(e.value))
    else:   self.response.out.write('<td></td>')
    if e.title: self.response.out.write('<td>%s</td>' % escape(e.title))
    else:   self.response.out.write('<td></td>')
    if e.author: self.response.out.write('<td>%s</td>' % escape(e.author))
    else:   self.response.out.write('<td></td>')
    if e.publishedDate: self.response.out.write('<td>%s</td>' % escape(e.publishedDate))
    else:   self.response.out.write('<td></td>')
    if e.description: self.response.out.write('<td>%s</td>' % escape(e.description))
    else:   self.response.out.write('<td></td>')
    if e.smallThumbnail: self.response.out.write('<td><a href="%s">link</a></td>' % escape(e.smallThumbnail))
    else:   self.response.out.write('<td></td>')
    self.response.out.write('<td><font size="-1">%s</font></td>\n' % e.date.ctime())
    self.response.out.write('''
      <td><form action="/deleteentry" method="post" enctype=application/x-www-form-urlencoded>
        <input type="hidden" name="entry_key_string" value="%s">
        <input type="hidden" name="tag" value="%s">
        <input type="hidden" name="fmt" value="html">
        <input type="submit" style="background-color: red" value="Delete"></form></td>\n''' %(entry_key_string, escape(e.tag)))
    self.response.out.write('</tr>')
  self.response.out.write('</table>')



### =============================================================================
### Utility procedures for generating the output
### =============================================================================

# ------------------------------------------------------------------------------
# Write response to the smartphone or to the Web depending on fmt.
#   Handler is an appengine request handler.  
#   Writer is a thunk (i.e. a procedure of no arguments) that does the write when invoked.
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
  WriteWebFooter(handler, writer)


# ------------------------------------------------------------------------------
# Write to the Web (without checking fmt)
# ------------------------------------------------------------------------------
def WriteToWeb(handler, writer):
  handler.response.headers['Content-Type'] = 'text/html'
  handler.response.out.write('<html><body>')
  writer()
  WriteWebFooter(handler, writer)

def WriteWebFooter(handler, writer):
  handler.response.out.write('''<p><a href="/"><i>Return to Main Page</i></a>''')
  handler.response.out.write('</body></html>')

# ------------------------------------------------------------------------------
# Delete an item from database (if exists)
# ------------------------------------------------------------------------------
def dbSafeDelete(key):
  if db.get(key):  db.delete(key)


# ------------------------------------------------------------------------------
# Assign a class to each URL
# ------------------------------------------------------------------------------
application =     \
   webapp.WSGIApplication([('/', MainPage),
                           ('/storeavalue', StoreAValue),
                           ('/deleteentry', DeleteEntry),
                           ('/getvalue', GetValue)
                           ],
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
