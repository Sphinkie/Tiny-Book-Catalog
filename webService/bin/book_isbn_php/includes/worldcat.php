<?php
header("Content-Type: text/plain", true);
$wskey = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";
$q = urlencode(htmlentities(intval($_GET['q'])));
$url="http://www.worldcat.org/webservices/catalog/content/isbn/".$q."?wskey=".$wskey;
$book=array("isbn_13"=>'', "id_worldcat"=>'', "id_google"=>'', 'cover'=>'', 'title'=>'', 'authors'=>'', "description"=>'', "publisher"=>'', 'date'=>'', "numberOfPages"=>0,nb_book=>0,'url'=>'','isPartOf'=>'','position'=>'');
$xml = simplexml_load_file($url); 
$book['url']=$url;
for ($i=0;$i<count ($xml->controlfield);$i++){
		if($xml->controlfield[$i]['tag']=='008'){
			$book['id_worldcat']=str_replace(" ","",(string) $xml->controlfield[$i]);
		}
		$book['nb_book']=1;	
	}
for ($i=0;$i<count ($xml->datafield);$i++){
	if($xml->datafield[$i]['tag']=='020'){//ISBN
		if(preg_match("/(\d{10,13})/i", (string) $xml->datafield[$i]->subfield[0],$matches)){
				if(strlen($matches[1])>strlen($book['isbn_13'])) {
				$book['isbn_13']=$matches[1];
				}
			}
	}else if($xml->datafield[$i]['tag']=='245'){//Auteurs et titre
		foreach($xml->datafield[$i]->subfield as $key =>  $value){
			if($value['code']=='c'){
				$book['authors']=(string) $value;
			} else if($value['code']=='a'){
				$book['title']=(string) $value;				
			} else if($value['code']=='b' OR $value['code']=='n' OR $value['code']=='p'){
				$book['title'].=' '.(string) $value;
			}
		}
	} else if($xml->datafield[$i]['tag']=='260'){//date de parution et éditeur
		foreach($xml->datafield[$i]->subfield as $key =>  $value){
			if($value['code']=='b'){
				$book['publisher']=str_replace(",","",(string) $value);
			} else if($value['code']=='c' AND preg_match("/(\d{4})/i", (string) $value,$matches)){
				$book['date'].=(string) $matches[1];
			}
		}
	}else if($xml->datafield[$i]['tag']=='300'){//Nombre de pages
		foreach($xml->datafield[$i]->subfield as $key =>  $value){
			if($value['code']=='a' AND preg_match("/(\d*)\s*p/i", (string) $value,$matches)){
				$book['numberOfPages']=(string) $matches[1];
			} 
		}
	}else if($xml->datafield[$i]['tag']=='490'){//Collection
		foreach($xml->datafield[$i]->subfield as $key =>  $value){
			if($value['code']=='a'){
				$book['isPartOf']=(string) $value;
			} else if($value['code']=='v'){
				$book['position']=(string) $value;			
			}
		}
	}
	
}
echo json_encode($book);
?>

