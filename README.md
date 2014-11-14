linkssandra
===========

POC (Prove of concept) for professional social network composed of a web application + NOSql Cassandra data store.


How to 
===========

import datastore:

	cqlsh -f cql/linkssandra_db.cql

in unix environment run:
	 
	source links/bin/activate
	
	python manage.py runserver 0.0.0.0:8182
	