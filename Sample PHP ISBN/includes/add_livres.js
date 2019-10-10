$(document).ready(function() {


var load_book=function (){
	isbn = $('input[name="isbn"]').val();
	isbn = isbn.replace(/[\-\s]/g,'');

if(isbn !==''){
	var book_complet={id:'',title:'', isbn_13:'', cover:'', authors:'', 'description':'', publisher:'', date:0, numberOfPages:0, 'id_worldcat':'','id_google':'','ASIN':'','url':'','isPartOf':'','position':''};
	var book_g={id:'',title:'', isbn_13:'', cover:'', authors:'', 'description':'', publisher:'', date:0, numberOfPages:0, 'id_worldcat':'','id_google':'','ASIN':'','url':''};
	var book_w={id:'',title:'', isbn_13:'', cover:'', authors:'', 'description':'', publisher:'', date:0, numberOfPages:0, 'id_worldcat':'','id_google':'','ASIN':'','url':'','isPartOf':'','position':''};
	var book_a={id:'',title:'', isbn_13:'', cover:'', authors:'', 'description':'', publisher:'', date:0, numberOfPages:0, 'id_worldcat':'','id_google':'','ASIN':'','url':''};

function getGoogleBook(isbn) {
return $.ajax({
  url: "https://www.googleapis.com/books/v1/volumes",
  method: "GET", 
  data: {'q' : 'isbn:'+isbn//, Si on a une clé, la mettre sur la ligne suivante
  //'key' : 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
  },
  dataType: "json"});
}

function getWorldcatBook(isbn) {
return $.ajax({
  url: "includes/worldcat.php",
  method: "GET", 
  data: {'q' : isbn},
  dataType: "json"});
}

function getAmazonBook(isbn) {
return $.ajax({
  url: "includes/amazon.php",
  method: "GET", 
  data: {'q' : isbn},
  dataType: "json"});
}

$.when(getGoogleBook(isbn),getWorldcatBook(isbn),getAmazonBook(isbn)).then(
function(data1,data2,data3) {
	var i;
	var book_g = {id:'',title:'', isbn_13:'', cover:'', authors:'', 'description':'', publisher:'', date:0, numberOfPages:0, 'id_worldcat':'','id_google':''};
	var nb_livres = data1[0].totalItems;
	var authors = '';
	var j = 0;	
	var isbn_13=0;

$('#test').html('');				
//Traitement du résultat de Gogle books
if(nb_livres > 0 && nb_livres<100){
	for(i = 0; i < nb_livres; i+=1){
		//couverture
		if(data1[0]['items'][i]){
			if(data1[0]['items'][i]['volumeInfo']['imageLinks']){
				if(data1[0]['items'][i]['volumeInfo']['imageLinks']['smallThumbnail']) {
					book_g.cover=data1[0]['items'][i]['volumeInfo']['imageLinks']['smallThumbnail'];
				}				
			}
		//Titre				
		if(data1[0]['items'][i]['volumeInfo']['title']) {
			book_g.title=	data1[0]['items'][i]['volumeInfo']['title'];		
		}
		if(data1[0]['items'][i]['volumeInfo']['subtitle']) {
			book_g.title+=' '+	data1[0]['items'][i]['volumeInfo']['subtitle'];		
		}				
		//Auteurs				
		if(data1[0]['items'][i]['volumeInfo']['authors']) {

			for(j = 0; j<data1[0]['items'][i]['volumeInfo']['authors'].length;j+=1){
				authors += data1[0]['items'][i]['volumeInfo']['authors'][j]+', ';}
			authors = authors.slice(0, -2);	
			book_g.authors=authors;
		}
		//Description				
		if(data1[0]['items'][i]['volumeInfo']['description']) {
			book_g['description']=data1[0]['items'][i]['volumeInfo']['description'];
		}
		//éditeur				
		if(data1[0]['items'][i]['volumeInfo']['publisher']) {
			book_g.publisher=data1[0]['items'][i]['volumeInfo']['publisher'];		
		}
		//date de parution 				
		if(data1[0]['items'][i]['volumeInfo']['publishedDate']) {
			book_g.date=data1[0]['items'][i]['volumeInfo']['publishedDate'];			
		}	
		//nb de pages 				
		if(data1[0]['items'][i]['volumeInfo']['pageCount']) {
			book_g.numberOfPages=data1[0]['items'][i]['volumeInfo']['pageCount'];	
		}												
		//ISBN				
		if(data1[0]['items'][i]['volumeInfo']['industryIdentifiers']) {
			for(j = 0; j<data1[0]['items'][i]['volumeInfo']['industryIdentifiers'].length;j+=1){
				if(data1[0]['items'][i]['volumeInfo']['industryIdentifiers'][j]["type"]==='ISBN_13'){isbn_13=data1[0]['items'][i]['volumeInfo']['industryIdentifiers'][j]['identifier'];}}
			if(isbn_13!==0){
				book_g.isbn_13=isbn_13;
			}		
		}
		}
		book_g.url='https://www.googleapis.com/books/v1/volumes?q='+'isbn:'+isbn;
	}
}
		
book_w = data2[0];		
book_a = data3[0];
//on corrige le titre de worldcat	
book_w.title=book_w.title.replace('/','')	
//On compile les différents résultats pour les combiner
if (book_w.isbn_13 === book_g.isbn_13 && book_w.isbn_13 === book_a.isbn_13){
	book_complet.isbn_13=book_g.isbn_13;
}else if(book_w.isbn_13===isbn){
	book_complet.isbn_13=book_w.isbn_13;
}else if(book_a.isbn_13===isbn){
	book_complet.isbn_13=book_a.isbn_13;
}else if(book_g.isbn_13===isbn){
	book_complet.isbn_13=book_g.isbn_13;
}else if(book_w.isbn_13 !== ''){
	book_complet.isbn_13=book_w.isbn_13;
}else if(book_a.isbn_13 !== ''){
	book_complet.isbn_13=book_a.isbn_13;
}else if(book_g.isbn_13 !== ''){
	book_complet.isbn_13=book_g.isbn_13;
}


if(book_g.id_google!==''){
	book_complet.id_google = book_g.id_google;
}
if(book_a.ASIN !== ''){
	book_complet.ASIN = book_a.ASIN;
}
if(book_a.cover.length > 0){
	book_complet.cover = book_a.cover;
}else if (book_g.cover.length > 0) {
	book_complet.cover = book_g.cover;
}
if(book_w.numberOfPages > 0){
	book_complet.numberOfPages = book_w.numberOfPages;
}else if(book_g.numberOfPages > 0){
	book_complet.numberOfPages = book_g.numberOfPages;
}

if(book_g['description'].length > 0){
	book_complet['description'] = book_g['description'];
}
if(book_w.date.length > 0){
	book_complet.date = book_w.date;
}else if (book_g.date.length > 0) {
	book_complet.date = book_g.date;
}
if(book_w.publisher.length > 0){
	book_complet.publisher = book_w.publisher;
}else if (book_g.publisher.length > 0) {
	book_complet.publisher = book_g.publisher;
}else if (book_a.publisher.length > 0) {
	book_complet.publisher = book_a.publisher;
}
if(book_w.authors.length > 0){
	book_complet.authors = book_w.authors.replace(/\.\.\./g,'');
}else if (book_g.authors.length > 0) {
	book_complet.authors = book_g.authors;
}else if (book_a.authors.length > 0) {
	book_complet.authors = book_a.authors;
}
if (book_w.title.length > 0) {
	book_complet.title = book_w.title.replace('/','');
}else if(book_a.title.length > 0){
	book_complet.title = book_a.title;
}else if (book_g.title.length > 0) {
	book_complet.title = book_g.title;
}

if(book_w.isPartOf.length > 0) {
	book_complet.isPartOf = book_w.isPartOf;
}
if (book_w.position.length > 0) {
	book_complet.position = book_w.position;
}


//Affichage du livre

var display_book = function(isbn,refname,title,book,display_url){
	var editable_fields=["name","author","publisher","datePublished","numberOfPages"];
	var editable_textareas=["description"];
	var k = 0;
	if(typeof display_url === 'undefined'){
		display_url = false;
	}	

	$('#test').append('<h2>'+title+'</h2><form method="post" action=""><div class="books" id="'+refname+'_'+isbn+'">\n\t<div class="couverture">\n\t</div>\n\t<div itemscope itemtype="http://schema.org/Book" class="bookdescription">\n\t\t<span itemprop="name" class="name">\n\t\t</span>\n\t\t<span class="right_2">de <span itemprop="author" class="author"></span><br>\nISBN 13 : <span itemprop="isbn" class="isbn"></span><br>\n Éditeur : <span itemprop="publisher" class="publisher"></span>, <span itemprop="datePublished" class="datePublished"></span>, <span itemprop="numberOfPages" class="numberOfPages"></span>	 p.<br><span itemprop="isPartOf" class="isPartOf"></span><span itemprop="position" class="position"></span></span> \n\t<p itemprop="description" class="description"></p><p class="url"></p></div>\n</div><input type="submit" value="Ajouter le livre"></form>');	/*
	 
	 */
		$('.isPartOf','#'+refname+'_'+isbn).append(book.isPartOf);		
		$('.position','#'+refname+'_'+isbn).append(book.position);	
		$('#'+refname+'_'+isbn+' > .couverture').append('<img src="'+book.cover+'" alt="couverture du livre"><br>');	
		$('.name','#'+refname+'_'+isbn).append(book.title);
		$( '.author','#'+refname+'_'+isbn).append(book.authors);
		$('.description','#'+refname+'_'+isbn).append(book['description']);	
		$('.publisher','#'+refname+'_'+isbn).append(book.publisher);
		$('.datePublished','#'+refname+'_'+isbn).append(book.date);		
		$('.numberOfPages','#'+refname+'_'+isbn).append(book.numberOfPages);		
		$('.isbn','#'+refname+'_'+isbn).append(book.isbn_13);
		if(display_url === true){
			$('.url','#'+refname+'_'+isbn).append(book.url);
		}
}
	//Affichage du livre complet
	display_book(isbn,'full','Proposition complète',book_complet,false);
	//Afichage de Worldcat
	if(book_w.nb_book>0){
		display_book(isbn,'worldcat','Résultat WorldCat',book_w,true);
	}else{$('#test').append('<h2>Aucun livre trouvé dans WorldCat</h2>');}
	//Affichage d'Amazon
	if(book_a.nb_book>0){
			display_book(isbn,'amazon','Résultat Amazon',book_a,true);
	}else{$('#test').append('<h2>Aucun livre trouvé chez Amazon</h2>');}	
	//Affichage de google books
	if(nb_livres > 0 && nb_livres<100){
		display_book(isbn,'google','Résultat Google Books',book_g,true);
	}else{$('#test').append('<h2>Aucun livre trouvé dans Google books</h2>');}	
});
}};


if($('input[name="isbn"]').val()!==''){
	load_book();	
}
$('input[name="isbn"]').on("change",function(){load_book();});
	


 });
