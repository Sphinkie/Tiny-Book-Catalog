#!/usr/bin/env python
# coding: UTF-8
# ==================================================================
# Ce module retourne des valeurs pour un livre, issues de amazon.com
# Note: il faut un compte AWS pour pouvoir utiliser cette API + une autorisation de AMAZON
# Autorisation que AMAZON ne m'a pas donné...
# ------------------------------------------------------------------
# 07/09/2019 |    | DDL | Version initiale
# ==================================================================

import logging
import sys, os, base64, datetime, hashlib, hmac 
import ConfigParser		# "configparser" en Python 3 (Parser de fichiers INI)
import requests 		# pip install requests

from google.appengine.api import urlfetch


# -----------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------

class amazon_books:

	# -----------------------------------------------------------------------------------------------------------
	# Constructeur
	# -----------------------------------------------------------------------------------------------------------
	def __init__(self):
		# List of signed headers in the canonical_headers list in alpha order.
		self.signed_headers = "host;x-amz-date"
		# Variables internes
		self.access_key = ""
		self.secret_key = ""
		self.canonical_request = ""
		self.authorization_header = ""
		self.headers = ""
		# On lit les clefs fournies par Amazon avec le compte AWS
		self._setKeys("aws.key")
		# La requete à envoyer à Amazon
		self.canonical_querystring = "Action=DescribeRegions&Version=2013-10-15"	# ICI: une requete simple : LA LISTE DES REGIONS DU MONDE

	# -----------------------------------------------------------------------------------------------------------
	# FONCTION PRICIPALE: envoie la requète à Amazon
	# -----------------------------------------------------------------------------------------------------------
	def getInfo(self,isbn):
		# Date pour le Header
		t = datetime.datetime.utcnow()
		amzdate = t.strftime('%Y%m%dT%H%M%SZ')
		# Timestamp pour les credentials
		datestamp = t.strftime('%Y%m%d')
		self._createCanonicalRequest(amzdate)
		self._createSignature(amzdate,datestamp)
		self._sendRequest("https://ec2.amazonaws.com")

	# -----------------------------------------------------------------------------------------------------------
	# Cette fonctions lit les clefs "AMAZON" préalablement enregistrées dans un fichier.
	# -----------------------------------------------------------------------------------------------------------
	def _setKeys(self,key_file):
		keys = ConfigParser.ConfigParser()
		keys.read(key_file) 
		self.access_key = keys.get('aws','access_key')
		self.secret_key = keys.get('aws','secret_key')
		if access_key is None or secret_key is None:
			print('No access key is available.')
			return False
			# sys.exit()
		else:
			return True

	# -----------------------------------------------------------------------------------------------------------
	# Creation de la Request Canonique
	# -----------------------------------------------------------------------------------------------------------
	def _createCanonicalRequest(self, amzdate):
		method = 'GET'
		canonical_uri = "/"
		# Query string values must be URL-encoded (space=%20). The parameters must be sorted by name.
		canonical_headers = "host:" + host + "\n" + "x-amz-date:" + amzdate + "\n"
		# Hash of the request body content. For GET requests, the payload is an empty string ("").
		payload_hash = hashlib.sha256(("").encode('utf-8')).hexdigest()
		# Combine elements to create canonical request
		self.canonical_request = method + "\n" + canonical_uri + "\n" + self.canonical_querystring + "\n" + canonical_headers + "\n" + self.signed_headers + "\n" + payload_hash
	
	# -----------------------------------------------------------------------------------------------------------
	# Creation de la Signature
	# -----------------------------------------------------------------------------------------------------------
	def _createSignature(self, amzdate, datestamp):
		algorithm = "AWS4-HMAC-SHA256"
		region    = "us-east-1"
		service   = "ec2"
		credential_scope = datestamp + '/' + region + "/" + service + "/aws4_request"
		string_to_sign = algorithm + '\n' +  amzdate + '\n' + credential_scope + '\n' + hashlib.sha256(self.canonical_request.encode('utf-8')).hexdigest()
		# Create the signing key using the function defined above.
		signing_key = self.getSignatureKey(self.secret_key, datestamp, region, service)
		# Sign the string_to_sign using the signing_key
		signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()
		# Ajout de la signature dans le header. (Note: il est aussi possible de mettre la signature dans la query)
		authorization_header = algorithm + ' ' + 'Credential=' + self.access_key + '/' + credential_scope + ', ' +  'SignedHeaders=' + self.signed_headers + ', ' + 'Signature=' + signature	
		# Python note: The 'host' header is added automatically by the Python 'requests' library.
		self.headers = {'x-amz-date':amzdate, 'Authorization':authorization_header}
		
	# -----------------------------------------------------------------------------------------------------------
	# Send the request.
	# -----------------------------------------------------------------------------------------------------------
	def _sendRequest(self, endpoint):
		request_url = endpoint + '?' + self.canonical_querystring
		result = requests.get(request_url, headers=self.headers)
		return result

	# -----------------------------------------------------------------------------------------------------------
	# Key derivation functions. 
	# http://docs.aws.amazon.com/general/latest/gr/signature-v4-examples.html#signature-v4-examples-python
	# -----------------------------------------------------------------------------------------------------------
	def sign(self, key, msg):
		return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

	def getSignatureKey(self, key, dateStamp, regionName, serviceName):
		kDate    = self.sign(('AWS4' + key).encode('utf-8'), dateStamp)
		kRegion  = self.sign(kDate, regionName)
		kService = self.sign(kRegion, serviceName)
		kSigning = self.sign(kService, 'aws4_request')
		return kSigning


'''	
# -----------------------------------------------------------------------------------------------------------
# Appel de l'API AWS
# doc = https://docs.aws.amazon.com/fr_fr/AWSECommerceService/latest/DG/EX_LookupbyISBN.html
# -----------------------------------------------------------------------------------------------------------
def getInfo(isbn):
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
'''
	
	
	

# ------------------------------------------------------------------------------
# Execution
# ------------------------------------------------------------------------------
if __name__ == '__main__':

	A = amazon_books()

	result = A.getInfo("9782253121206")
	
	print('\n++++++++++++++++++++++++++++++++++++')
	print('BEGIN REQUEST')
	print('++++++++++++++++++++++++++++++++++++')
	print('Request URL = ' + A.canonical_querystring)

	print('\n++++++++++++++++++++++++++++++++++++')
	print('RESPONSE')
	print('++++++++++++++++++++++++++++++++++++')
	print('Response code: %d\n' % result.status_code)
	print(result.text)
	print('\n')
