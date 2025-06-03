# nomadScnClonerTranslator

Python script for automatic content translation of an interatctive tourist guide mobile app called Nomad Games.
The content is fetched directly from the database, sent with async calls to the Google Translate API, and then inserted back to the database. 
Looks simple but coding it actually took me almost just as long as coding the entire test automation framework for our app because it relies on mysql.connector a lot.
Guess I should learn a different library for SQL in Python...
