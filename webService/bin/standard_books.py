#!/usr/bin/env python
# coding: UTF-8
# ==================================================================
# Ce Module retourne des valeurs par defaut pour un livre.
# ------------------------------------------------------------------
# 07/09/2019 |    | DDL | Version initiale
# ==================================================================


# ------------------------------------------------------------------------------
# On renseigne les valeurs par défaut pour un livre
# ------------------------------------------------------------------------------
def getInfo(isbn):
	data = dict()
	data["title"]  	= "Code ISBN: %s"%(isbn)
	data["author"]	= "Inconnu"
	data["description"]	= u"Pas de résumé."		# on force en unicode, à cause des accents, pour pouvoir l'affecter à une entry.
	data["picture"]	= "pages.jpg"
	return data



# ------------------------------------------------------------------------------
# Execution
# ------------------------------------------------------------------------------
if __name__ == '__main__':

	print (getInfo("9782253121206"))
