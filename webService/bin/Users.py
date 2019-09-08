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
class UserData(db.Model):
	name			= db.StringProperty(required=True)	# Prenom de l'utilisateur
	groupId			= db.StringProperty()				# nom du groupe d'amis
	role			= db.StringProperty()				# member, admin, waiting, closed
### =============================================================================

# ---------------------------------------------------------------
# Note sur GqlQuery: 
# .get() retourne le premier élement trouvé
# .run() retourne un objet itérable avec tous les élements trouvés (recommandé)
# .fetch() retourne la liste tous les élements trouvés (lenteur)
# ---------------------------------------------------------------
class Users():

	def createUSer(self):
		pass

# ------------------------------------------------------------------------------
# Execution
# ------------------------------------------------------------------------------
if __name__ == '__main__':
	main()
