#!/usr/bin/env python
# -*- coding: utf-8 -*-
### ===========================================================================================
### 
### 
### 
### ===========================================================================================
### Author: DDL
### ===========================================================================================

from google.appengine.ext import db
from google.appengine.ext.db import Key




### ===========================================================================================
### Creation de la table UserData
### ===========================================================================================
class UsersData(db.Model):
	name			= db.StringProperty(required=True)	# Prenom de l'utilisateur
	groupName		= db.StringProperty()				# nom du groupe d'amis
	role			= db.StringProperty()				# member, admin, waiting, closed
### =============================================================================

# ---------------------------------------------------------------
# Note sur GqlQuery: 
# .get() retourne le premier élement trouvé
# .run() retourne un objet itérable avec tous les élements trouvés (recommandé)
# .fetch() retourne la liste tous les élements trouvés (lenteur)
# ---------------------------------------------------------------
class Users:

	# ----------------------------------------------------------------------------
	# Ajout d'un nouvel user
	# ----------------------------------------------------------------------------
	def createUser(self, username):
		entry = db.GqlQuery("SELECT * FROM UsersData WHERE name = :1", username).get()
		if not entry:
			# Si cette entry n'existe pas, on crée une nouvelle entry
			entry = UsersData(name = username, role="waiting")
			entry.put()
			return entry.key().id()
		else:
			return ""

	# -------------------------------------------------------------------------------
	# Renvoie l'ID d'un User : BAD: PLUSIEURS USERS PEUVENT AVOIR LE MEME NAME
	# -------------------------------------------------------------------------------
	def gerUserId(self, username):
		entry = db.GqlQuery("SELECT * FROM UsersData WHERE name = :1", username).get()
		if entry:
			return entry.key().id()
		else:
			return ""

	# ----------------------------------------------------------------------------
	# set user role for his group
	# ----------------------------------------------------------------------------
	def setRole(self, userId, role):
		entry = db.GqlQuery("SELECT * FROM UsersData WHERE name = :1", username).get()
		if entry:
			# Si cette entry existe, on positionne son role
			entry.role=role
			entry.put()

	# ----------------------------------------------------------------------------
	# set family group
	# ----------------------------------------------------------------------------
	def setGroup(self, userId, groupname):
		# Note: There's a potential readers/writers error here...
		entry = db.GqlQuery("SELECT * FROM UsersData WHERE name = :1", username).get()
		if entry:
			# Si cette entry existe, on positionne son groupe
			entry.groupName=groupname
			entry.put()
