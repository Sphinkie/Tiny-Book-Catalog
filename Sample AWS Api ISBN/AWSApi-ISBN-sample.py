# ------------------------------------------------------------------------------------------------------
# Utilisation de GET avec un en-tete Authorization (Python)
# A partir de l'exemple fournit par AWS, qui effectue une requete GET pour interroger l'api EC2, on fait une requète l'api ItemSearch ISBN
#
# ABOUT THIS PYTHON SAMPLE: This sample is part of the AWS General Reference 
# Signing AWS API Requests top available at
# https://docs.aws.amazon.com/general/latest/gr/sigv4-signed-request-examples.html
# AWS Version 4 signing example
# See: http://docs.aws.amazon.com/general/latest/gr/sigv4_signing.html
# This version makes a GET request and passes the signature in the Authorization header.
#
# ------------------------------------------------------------------------------------------------------
# Ce n'est pas les clefs de l'utilisateur IAM qu'il faut utiilser mais celles de l'affiliate,
# comme expliqué par Martin Verot ci-dessous: (voir http://agregationchimie.free.fr/book_isbn.php)
# ------------------------------------------------------------------------------------------------------
# Pour Amazon, comme beaucoup de personnes l'utilise aussi, c'est très facile de trouver de l'aide, mais la soumission des requêtes est un peu plus technique, heureusement, je suis tombé sur cette page pour avoir l'obtention de la signature sans trop me casser la tête. Le plus compliqué est de s'y retrouver parmi les possibilités pour les identifiants, l'IAM inutile, la nécessité d'avoir aussi un compte affilié, bref, plus les petites tracasseries liées à la création de multiples comptes que des difficultés techniques.
# Les points positifs :
# - Les couvertures de livre à gogo et dans toutes les dimensions
# - La base de données très complète
# - La documentation assez bien fournie
# Les points négatifs :
# - Les informations qui sont en général de mauvaise qualité (auteurs en particulier)
# - Les tracasseries pratiques: la nécessité d'avoir un compte AWS, mais pas besoin d'IAM, mais d'avoir un compte affilié
# - Le côté commercial: la nécessité de donner son numéro de carte bleue pour un compte AWS même si c'est gratuit.
# - Le côté commercial une deuxième fois : la nécessité de faire des rétroliens publicitaires avec le compte "associates" pour qu'il reste ouvert.
# - La complexité pour avoir une signature qui marche.
# ------------------------------------------------------------------------------------------------------
# Pour l'instant: TESTS NEGATIFS (erreur 403)
# - s'enregistrer en tant que affiliate (partenaires.amazon.fr): on obtient un affiliateTag (= ID partenaire)
# * La region doit-elle être 'us-xxx' ou 'eu-x'x' ??
# - Dans 'Outils', s'inscrire à 'Product Advertising API' 
# * Pour l'instant, le bouton "je m'inscris" est grisé. Pourquoi ??
# ------------------------------------------------------------------------------------------------------
# Exemple de requete de BBVA (https://bbvaopen4u.com/en/actualidad/apis-books-amazon-google-books-isbn-and-their-open-apis)
# http://webservices.amazon.com/onca/xml?service=AWSECommerceService
#	&AWSAccessKeyId=$AWS_KEY
#	&AssociateTag=$TAG_DE_AMAZON
#	&Operation=ItemSearch
#	&Keywords=$TERMINO_A_BUSCAR
#	&SearchIndex=Books
#	&Timestamp=[YYYY-MM-DDThh:mm:ssZ]
#	&Signature=[Request Signature]
# ------------------------------------------------------------------------------------------------------
# Exemple de requete de la doc AWS:
# http://webservices.amazon.com/onca/xml?Service=AWSECommerceService
# 	&Operation=ItemLookup
# 	&ResponseGroup=Large
# 	&SearchIndex=All
# 	&IdType=ISBN
# 	&ItemId=076243631X
# 	&AWSAccessKeyId=[Your_AWSAccessKeyID]
# 	&AssociateTag=[Your_AssociateTag]
# 	&Timestamp=[YYYY-MM-DDThh:mm:ssZ]
# 	&Signature=[Request_Signature]
# ------------------------------------------------------------------------------------------------------
# Exemple de requete MartinVerot:
#   Service=AWSECommerceService
#   &Operation=ItemLookup
#   &ResponseGroup=Large
#   &SearchIndex=All
#   &IdType=ISBN
#   &ItemId=076243631X
#   &AWSAccessKeyId=XXXXXXXXX
#   &AssociateTag=XXXXXXXXX
#   &Timestamp=[Y-m-d\TH:i:s\Z]			# ajouté par le script
# 	&Signature=[Request_Signature]	    # ajouté par le script
# ------------------------------------------------------------------------------------------------------

# en cours:
#    obtenir les access_key de l'affiliate
#    tester .com ou .fr

import sys, os, base64, datetime, hashlib, hmac
import ConfigParser		# configparser en Python 3
import requests 		# pip install requests


# ------------------------------------------------------------------------------------------------------
# Key derivation functions. See:
# http://docs.aws.amazon.com/general/latest/gr/signature-v4-examples.html#signature-v4-examples-python
# ------------------------------------------------------------------------------------------------------
def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

# ------------------------------------------------------------------------------------------------------
# getSignatureKey
# ------------------------------------------------------------------------------------------------------
def getSignatureKey(key, dateStamp, regionName, serviceName):
    kDate    = sign(('AWS4' + key).encode('utf-8'), dateStamp)
    kRegion  = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, 'aws4_request')
    return kSigning

	
# ------------------------------------------------------------------------------------------------------
# Read AWS access key from env. variables or configuration file. 
# Best practice is NOT to embed credentials in code.
# ------------------------------------------------------------------------------------------------------
keys = ConfigParser.ConfigParser()
keys.read('aws.key') 
access_key    = keys.get('aws','access_key')
secret_key    = keys.get('aws','secret_key')
associate_tag = keys.get('aws','associate_tag')
if access_key is None or secret_key is None:
    print('No access key is available.')
    sys.exit()

# ------------------------------------------------------------------------------------------------------
# Create a date for headers and the credential string
# ------------------------------------------------------------------------------------------------------
t = datetime.datetime.utcnow()
amzdate   = t.strftime('%Y%m%dT%H%M%SZ')
datestamp = t.strftime('%Y%m%d')                # Date w/o time, used in credential scope
timestamp = t.strftime('%Y-%m-%dT%H:%M:%SZ')    # YYYY-MM-DDThh:mm:ssZ, used in request_url

# ------------------------------------------------------------------------------------------------------
# REQUEST VALUES 
# ------------------------------------------------------------------------------------------------------
service = 'AWSECommerceService'
host    = 'webservices.amazon.fr'
#region = 'us-east-1'
region = 'eu-west-1'
endpoint = 'http://webservices.amazon.fr/onca/xml'
#request_parameters = 'Operation=ItemLookup&ResponseGroup=large&SearchIndex=All&IdType=ISBN&ItemId=076243631X'
#request_parameters = 'Operation=ItemSearch&SearchIndex=Books&IdType=ISBN&ItemId=076243631X'
#request_parameters = 'Service=AWSECommerceService&AWSAccessKeyId='+access_key+'&AssociateTag='+associate_tag+'&Operation=ItemSearch&SearchIndex=Books&IdType=ISBN&ItemId=076243631X'
request_parameters  = 'Service=AWSECommerceService&Operation=ItemLookup&ResponseGroup=Large&SearchIndex=All&IdType=ISBN&ItemId=076243631X' + '&AWSAccessKeyId='+access_key + '&AssociateTag='+associate_tag
	
# ------------------------------------------------------------------------------------------------------
# ************* TASK 1: CREATE A CANONICAL REQUEST *************
# http://docs.aws.amazon.com/general/latest/gr/sigv4-create-canonical-request.html
# ------------------------------------------------------------------------------------------------------

# Step 1 is to define the verb (GET, POST, etc.)
method = 'GET'

# Step 2: Create canonical URI--the part of the URI from domain to query string
# (use '/' if no path)
canonical_uri = '/onca/xml' 

# Step 3: Create the canonical query string. In this example (a GET request),
# request parameters are in the query string. 
# Query string values must be URL-encoded (space=%20). The parameters must be sorted by name.
# For this example, the query string is pre-formatted in the request_parameters variable.
canonical_querystring = request_parameters

# Step 4: Create the canonical headers and signed headers. Header names
# must be trimmed and lowercase, and sorted in code point order from
# low to high. Note that there is a trailing \n.
canonical_headers = 'host:' + host + '\n' + 'x-amz-date:' + amzdate + '\n'

# Step 5: Create the list of signed headers. This lists the headers
# in the canonical_headers list, delimited with ";" and in alpha order.
# Note: The request can include any headers; canonical_headers and
# signed_headers lists those that you want to be included in the 
# hash of the request. "Host" and "x-amz-date" are always required.
signed_headers = 'host;x-amz-date'

# Step 6: Create payload hash (hash of the request body content). 
# For GET requests, the payload is an empty string ("").
payload_hash = hashlib.sha256(('').encode('utf-8')).hexdigest()

# Step 7: Combine elements to create canonical request
canonical_request = method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash

# ------------------------------------------------------------------------------------------------------
# ************* TASK 2: CREATE THE STRING TO SIGN*************
# Match the algorithm to the hashing algorithm you use, either SHA-1 or SHA-256 (recommended)
# ------------------------------------------------------------------------------------------------------
algorithm = 'AWS4-HMAC-SHA256'
credential_scope = datestamp + '/' + region + '/' + service + '/' + 'aws4_request'
string_to_sign   = algorithm + '\n' +  amzdate + '\n' +  credential_scope + '\n' +  hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()

# ------------------------------------------------------------------------------------------------------
# ************* TASK 3: CALCULATE THE SIGNATURE *************
# Create the signing key using the function defined above.
# ------------------------------------------------------------------------------------------------------
signing_key = getSignatureKey(secret_key, datestamp, region, service)
# Sign the string_to_sign using the signing_key
signature  = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()

# ------------------------------------------------------------------------------------------------------
# ************* TASK 4: ADD SIGNING INFORMATION TO THE REQUEST *************
# ------------------------------------------------------------------------------------------------------
# The signing information can be either in a query string value or in a header named Authorization.
# This code shows how to use a header.
# Create authorization header and add to request headers.
authorization_header = algorithm + ' ' + 'Credential=' + access_key + '/' + credential_scope + ', ' +  'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature

# The request can include any headers, but MUST include "host", "x-amz-date", 
# and (for this scenario) "Authorization". "host" and "x-amz-date" must
# be included in the canonical_headers and signed_headers, as noted earlier.
# Order here is not significant.
# Python note: The 'host' header is added automatically by the Python 'requests' library.
headers = {'x-amz-date':amzdate, 'Authorization':authorization_header}




# ------------------------------------------------------------------------------------------------------
# ************* SEND THE REQUEST *************
# ------------------------------------------------------------------------------------------------------
request_url = endpoint + '?' + canonical_querystring

# request_url = request_url+'&AWSAccessKeyId='+access_key+'&Signature='+signature+'&Timestamp='+timestamp+'&AssociateTag='+associate_tag
request_url = request_url+'&Signature='+signature+'&Timestamp='+timestamp

print('\n++++++++++++++++++++++++++++++++++++')
print('GET REQUEST')
print('++++++++++++++++++++++++++++++++++++')
print('Request URL = ' + request_url)
r = requests.get(request_url, headers=headers)

print('\n++++++++++++++++++++++++++++++++++++')
print('RESPONSE')
print('++++++++++++++++++++++++++++++++++++')
print('Response code: %d\n' % r.status_code)
print(r.text)
print('')

