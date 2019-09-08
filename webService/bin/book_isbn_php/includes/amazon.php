<?php 
header("Content-Type: text/plain", true);

$book=array("isbn_13"=>'', "id_worldcat"=>'', "id_google"=>'','ASIN'=>'', 'cover'=>'', 'title'=>'', 'authors'=>'', "description"=>'', "publisher"=>'', 'date'=>'', "numberOfPages"=>0,'nb_book'=>0,'url'=>'');
$q = urlencode(htmlentities($_GET['q']));


$private_key = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";
$params["AWSAccessKeyId"] = "xxxxxxxxxxxxxxxxxxxx";
$params["AssociateTag"] = "xxxxxxxxxxxxxxxxxxxx-20";


// GMT timestamp
$params["Timestamp"] = gmdate("Y-m-d\TH:i:s\Z");



function signAmazonUrl($url, $secret_key)
{
    $original_url = $url;
    // Decode anything already encoded
    $url = urldecode($url);
    // Parse the URL into $urlparts
    $urlparts       = parse_url($url);
    // Build $params with each name/value pair
    foreach (split('&', $urlparts['query']) as $part) {
        if (strpos($part, '=')) {
            list($name, $value) = split('=', $part, 2);
        } else {
            $name = $part;
            $value = '';
        }
        $params[$name] = $value;
    }
    // Include a timestamp if none was provided
    if (empty($params['Timestamp'])) {
        $params['Timestamp'] = gmdate('Y-m-d\TH:i:s\Z');
    }
    // Sort the array by key
    ksort($params);
    // Build the canonical query string
    $canonical       = '';
    foreach ($params as $key => $val) {
        $canonical  .= "$key=".rawurlencode(utf8_encode($val))."&";
    }
    // Remove the trailing ampersand
    $canonical       = preg_replace("/&$/", '', $canonical);
    // Some common replacements and ones that Amazon specifically mentions
    $canonical       = str_replace(array(' ', '+', ',', ';'), array('%20', '%20', urlencode(','), urlencode(':')), $canonical);
    // Build the sign
    $string_to_sign             = "GET\n{$urlparts['host']}\n{$urlparts['path']}\n$canonical";
    // Calculate our actual signature and base64 encode it
    $signature            = base64_encode(hash_hmac('sha256', $string_to_sign, $secret_key, true));
    // Finally re-build the URL with the proper string and include the Signature
    $url = "{$urlparts['scheme']}://{$urlparts['host']}{$urlparts['path']}?$canonical&Signature=".rawurlencode($signature);
    return $url;
}

	$amazon_request=signAmazonUrl('http://webservices.amazon.com/onca/xml?Service=AWSECommerceService&Operation=ItemLookup&ResponseGroup=Large&SearchIndex=All&IdType=ISBN&ItemId='.$q.'&AWSAccessKeyId='.$params["AWSAccessKeyId"].'&AssociateTag='.$params["AssociateTag"].'&Timestamp='.$params["Timestamp"], $private_key);



$xml = simplexml_load_file($amazon_request); //retrieve URL and parse XML content
$book['url']=$amazon_request;
$book['ASIN']=(string) $xml->Items->Item->ASIN;
$book['cover']=(string) $xml->Items->Item->MediumImage->URL;
$book['isbn_13']=(string) $xml->Items->Item->ItemAttributes->EAN;
if(strlen((string) $xml->Items->Item->ItemAttributes->Publisher)>0){
	//Manufacturer Label
	$book['publisher']=(string) $xml->Items->Item->ItemAttributes->Publisher;	
} else if(strlen((string) $xml->Items->Item->ItemAttributes->Manufacturer)>0){
	$book['publisher']=(string) $xml->Items->Item->ItemAttributes->Manufacturer;	
} else if(strlen((string) $xml->Items->Item->ItemAttributes->Label)>0){
	$book['publisher']=(string) $xml->Items->Item->ItemAttributes->Label;	
}

$book['title']=(string) $xml->Items->Item->ItemAttributes->Title;
$book['authors']=(string) $xml->Items->Item->ItemAttributes->Author;

if(strlen($book['isbn_13'])>=10){
	$book['nb_book']=1;
	}

echo json_encode($book);
?>

