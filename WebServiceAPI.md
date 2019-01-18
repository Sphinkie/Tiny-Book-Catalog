# Tiny-Book-Catalog
*Share your books with your friends (Android)*

The webService contains three pages:
- MainPage: list of the books in database
- /storeavalue : allows the Android application to modify values in the database
- /getvalue: permit to the Android application to get values from the database

## <u>Store A Value</u>

The Android application send two parameters: **tag** and **value**.

**Tag** is the objet to store. **Value** is the command to apply.

* tag = <isbn_code> value = "`create:`" create an entry in the database for this book
* tag = <isbn_code> value = "`owner:john`" set the *owner* of the book to the user *John*
* tag = <isbn_code> value = "`requirer:bob`" set the *requirer* of the book to the user *Bob*
* tag = <isbn_code> value = "`deletedby:john`" remove the book from the database

## <u>Get Value</u>

The Android application send a **tag** and get a **value** as a response.

- tag = "`isbn:*`" returns the list of all isbn in database.
- tag = "`isbn:9876543210[:requestid]`" returns an information list about the book. The *requestid* is optionnal. The returned list contains [title, author, publisher, publication date, small thumbnail url, requirer, owner].
- tag = "`pict:9876543210[:requestid]` returns the picture url of the book (isbn). The *requestid* is optionnal.
- tag ="`desc:9876543210`" returns the description (abstract) of the book (isbn).
- tag = "`requirer:9876543210`" returns the requirer and the owner of the book.
- tag = "`user:*`" returns the list of all known owners.
- tag = "`user:john`" returns the list of all isbn which have *John* for owner.
- tag = "`requestedby:bob`" returns the list of isbn requested by *Bob* (*Bob* is the requirer).
- tag = "`requestedto:john`" returns the list of isbn belonging to *John*  and requested by somebody. (owner is *John* and requirer is not null).

Note: "9876543210" represent an ISBN code.

The **tag** is also returned in the response, so the Android application can get back the *requestid*, if needed.




