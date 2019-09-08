# On peut tester les request sur le Scratchpad d'amazon.fr, et voir des exemples de code.
# https://webservices.amazon.fr/scratchpad

import urllib	 # pour parser les commandes GET
import requests	 # pour envoyer les commandes GET # pip install requests
try:
        import ConfigParser as cp # python 2
except:
        import configparser as cp # Python 3
import datetime
import base64, hashlib, hmac

# ------------------------------------------------------------------------------------------------------
# Fonction de signature Amazon de Brandon Checketts. See:
# https://www.brandonchecketts.com/archives/2009/06
# ------------------------------------------------------------------------------------------------------
def signAmazonUrl(url, secret_key):
	original_url = url
	print (original_url,'\n')
	# Decode anything already encoded
	# url = urldecode(url)
	# Parse the URL into urlparts
	urlparts = urllib.parse.urlparse(url)
	print ('urlparts:\n',urlparts,'\n')
	'''ParseResult(scheme='http', netloc='webservices.amazon.com', path='/onca/xml', params='',
	query='Service=AWSECommerceService&Operation=ItemLookup&SearchIndex=All&IdType=ISBN&ItemId=076243631X&...', fragment='')
	'''
	# ------------------------------
	# on extrait les paramètres dans un dictionnaire.
	# ------------------------------
	parameters = urllib.parse.unquote(urlparts[4])  # Le 4eme champ est 'query'
	param_list = parameters.split('&')              # Liste des parametres
	print ('param_list:\n',param_list,'\n')
	params = dict()
	for param in param_list:
		key=param.split('=')[0]
		val=param.split('=')[1]
		params[key]=val
	print ('params:\n',params,'\n')
	# Include a timestamp if none was provided
	if 'Timestamp' not in params:
		t = datetime.datetime.utcnow()
		params['Timestamp'] = t.strftime('%Y-%m-%dT%H:%M:%SZ')    # YYYY-MM-DDThh:mm:ssZ, used in request_url
	# Sort the array by key
	sorted_keys = sorted(params.keys())
	print ('sorted_keys:\n',sorted_keys,'\n')
	# Build the canonical query string
	canonical = ''
	for key in sorted_keys:
		#canonical += key + rawurlencode(utf8_encode(val)) + '&'
		canonical += key+'='+params[key]+ '&'
	# Remove the trailing ampersand
	canonical = canonical[:-1]
	# Some common replacements and ones that Amazon specifically mentions
	canonical = canonical.replace(' ','%20')
	canonical = canonical.replace('+','%20')
	canonical = canonical.replace(',','%2C')
	canonical = canonical.replace(';','%3A')
	print ('canonical:\n',canonical,'\n')
	# Build the sign
	string_to_sign = 'GET\n'+urlparts[1]+'\n'+urlparts[2]+'\n'+canonical  # 1:host 2:path
	print ('string_to_sign:\n',string_to_sign,'\n')
	# Calculate our actual signature and base64 encode it
	signing_key = secret_key
	# Exemple:
	signing_key = b'1234567890'  # secret_key  # ou "1234567890"
	bytes_string = """GET
webservices.amazon.com
/onca/xml
AWSAccessKeyId=00000000000000000000&ItemId=0679722769&Operation=ItemLookup&ResponseGroup=ItemAttributes%2COffers%2CImages%2CReviews&Service=AWSECommerceService&Timestamp=2009-01-01T12%3A00%3A00Z&Version=2009-01-06"""
	# result : 'Nace+U3Az4OhN7tISqgs1vdLBHBEijWcBeCqL5xN9xg='

	bytes_string = (string_to_sign).encode('UTF-8')
	signature = hmac.new(signing_key, bytes_string, hashlib.sha256).hexdigest()        # ou .digest() ??
	dig = hmac.new(signing_key, msg=bytes_string, digestmod=hashlib.sha256).digest()
	base64.b64encode(dig).decode()      # py3k-mode
		
	# Finally re-build the URL with the proper string and include the Signature
	#url = urlparts[0]+'://'+urlparts[1]+urlparts[2]+'?'+canonical+'&Signature='+rawurlencode(signature)
	url = urlparts[0]+'://'+urlparts[1]+urlparts[2]+'?'+canonical+'&Signature='+signature   #0:scheme 1:host 2:path
	print('final url:\n'+url)
	return url

'''
# To use it, just wrap your Amazon URL with the signAmazonUrl() function and pass it your original string and secret key as arguments.
As an example:
xml = file_get_contents('http://webservices.amazon.com/onca/xml?some-parameters');
# becomes

xml = file_get_contents(signAmazonUrl('http://webservices.amazon.com/onca/xml?some-parameters', secret_key));
# Like most all of the variations of this, it does require the hash functions be installed to use the hash_hmac() function.
That function is generally available in PHP 5.1+. Older versions will need to install it with Pecl.
I tried using a couple of versions that try to create the Hash in pure PHP code, but none worked and installing it via Pecl was pretty simple.
'''



# ------------------------------------------------------------------------------------------------------
# Exemple d'utilisation
# ------------------------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------------------------------
# Read AWS access key from configuration file. 
# ------------------------------------------------------------------------------------------------------
keys = cp.ConfigParser()
keys.read('aws.key') 
access_key    = keys.get('aws','access_key')
secret_key    = keys.get('aws','secret_key')
associate_tag = keys.get('aws','associate_tag')
if access_key is None or secret_key is None:
    print('No access key is available.')
    sys.exit()

# ------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------
request_url = 'http://webservices.amazon.fr/onca/xml?Service=AWSECommerceService'+ \
	'&Operation=ItemLookup&ResponseGroup=Large&SearchIndex=All&IdType=ISBN'+ \
	'&ItemId=076243631X' + \
	'&AWSAccessKeyId='+access_key + \
	'&AssociateTag='+associate_tag

amazon_request=signAmazonUrl(request_url, secret_key)
	
# ------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------
print('\n++++++++++++++++++++++++++++++++++++')
print('GET REQUEST')
print('++++++++++++++++++++++++++++++++++++')
print('Request URL = ' + amazon_request)
r = requests.get(amazon_request) #, headers=headers)
#content = urllib2.urlopen(request_url).read()
#print (content)

print('\n++++++++++++++++++++++++++++++++++++')
print('RESPONSE')
print('++++++++++++++++++++++++++++++++++++')
print('Response code: %d\n' % r.status_code)
print(r.text)
print('')

	

