# ZCQL

## Introduction

Catalyst Cloud Scale ZCQL serves as Catalyst’s own query language, similar to MySQL or PostgreSQL. It is used to perform data manipulations within the Catalyst Data Store. As a query engine powered by Catalyst, ZCQL enables developers to work with data using familiar SQL-like syntax while handling complex queries with high efficiency and scalability.

You can perform the following operations on the tables in your Data Store using ZCQL:

* Retrieval: Obtaining records from existing tables
* Insertion: Inserting records into the existing columns of an existing table
* Updating: Updating the value of existing columns in an existing table
* Deletion: Deleting records from an existing table

You can execute a variety of DML queries using ZCQL to obtain or manipulate data based on specific criteria by using
various clauses and statements such as the SQL Join clauses, Groupby
statements, OrderBy statements, and the WHERE and HAVING clauses. ZCQL also supports several built-in SQL numeric functions that help you execute arithmetic operations easily.

You can implement ZCQL queries in your Catalyst application's source code, such as in the functions or the client
component. For example, you pass a ZCQL query in a function's body to retrieve data from a table in the Data Store and
process it further.

The Catalyst console also provides a ZCQL query execution window, where you can execute queries and view the responses.
This allows you to test ZCQL queries easily, before implementing them in your application.

### SDK and API documentation

Catalyst offers ZCQL in the Java, Node.js, Python, Web, Android, iOS, and Flutter SDK packages, and as an API. For code samples on executing ZCQL
queries in these programming environments, refer to these help pages:

* Execute ZCQL Query - Java SDK
* Execute ZCQL Query - Node.js
SDK
* Execute ZCQL Query - Python SDK
* Execute ZCQL Query - Web SDK
* Execute ZCQL Query - Android SDK
* Execute ZCQL Query - iOS SDK
* Execute ZCQL Query - Flutter SDK
* Execute ZCQL Query - API

Note: 

* From December 01st, 2024, all your current projects in all your Orgs present in the Development Environment will be automatically mapped to ZCQL V2 Parser.

* From April 01st, 2025, all the projects present in all Orgs that have already been mapped to ZCQL V2 Parser in Development Environment will be automatically mapped to ZCQL V2 Parser in the Production Environment, if and when production is enabled for the project.

* To use ZCQL V2 in your code, you need to set the appropriate environment variable as shown in this help document.

You can refer to Catalyst Tutorials to get an
idea of ZCQL's implementation in the function or client code of the applications.


### Benefits

* Can perform data retrieval, insertion, updating, and deletion operations in the Catalyst Data Store
* Similarity to MySQL ensures ease of use and there is no separate learning curve
* Can test the execution of the queries in the console before implementing them in the application
* Can pass a ZCQL query in an API's body using the SDKs
* Can perform arithmetic and numerical operations on the result set using the ZCQL built-in functions
<br />

# SELECT


### General Syntax of SELECT

ZCQL supports data retrieval query operations using the SELECT command. This command lets you select a column or a set of columns from a base table and view the data records within the command&#39;s scope.

The general syntax for a basic ZCQL data retrieval operation is as follows:


SELECT {COLUMNS} FROM {BASE_TABLE_NAME} [JOIN_CLAUSE] 
[WHERE {WHERE_CONDITION}] [GROUP BY {GROUP_BY_COLUMN}] [ORDER BY {ORDER_BY_COLUMN}] 
LIMIT [{OFFSET}],{VALUE}

&lt;br /&gt;

Note:&lt;br /&gt;

* The base table is the table you execute the query on.
* You need not use the end-of-statement delimiter (;) at the end of a ZCQL query, while executing it in the ZCQL console.


The base table is the table you execute the query on.

We will discuss each ZCQL operation in detail with an example database and sample queries that you can execute on it.

Example Database:

Imagine you&#39;re developing a ticket booking application where users can view the movie listings and showtimes for various theaters in a city, and can book movie tickets using the application. Let&#39;s create a table named &#39;Movies&#39; that contains the showtime listings of the movies played in various theaters.

Sample records from the _Movies_ table are given below:

&lt;table class=&#34;content-table&#34;&gt;
&lt;thead&gt;
&lt;tr&gt;
&lt;th&gt;&lt;strong&gt;MovieID&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;MovieName&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;ShowDate&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;ShowTime&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;TheaterID&lt;/strong&gt;&lt;/th&gt;
&lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
&lt;tr&gt;
&lt;td&gt;2056&lt;/td&gt;
&lt;td&gt;The First Purge&lt;/td&gt;
&lt;td&gt;2018-07-13&lt;/td&gt;
&lt;td&gt;13:00:00&lt;/td&gt;
&lt;td&gt;047&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;2057&lt;/td&gt;
&lt;td&gt;Ant-Man and the Wasp&lt;/td&gt;
&lt;td&gt;2018-07-13&lt;/td&gt;
&lt;td&gt;14:20:00&lt;/td&gt;
&lt;td&gt;052&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;2058&lt;/td&gt;
&lt;td&gt;Hotel Transylvania 3: Summer Vacation&lt;/td&gt;
&lt;td&gt;2018-07-14&lt;/td&gt;
&lt;td&gt;17:00:00&lt;/td&gt;
&lt;td&gt;052&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;2059&lt;/td&gt;
&lt;td&gt;Skyscraper&lt;/td&gt;
&lt;td&gt;2018-07-14&lt;/td&gt;
&lt;td&gt;21:30:00&lt;/td&gt;
&lt;td&gt;053&lt;/td&gt;
&lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;
&lt;br /&gt;

### Basic SELECT

The SELECT statement is used to select the columns from a base table and display its records. You should mention the names of the columns that are to be displayed in the result set.

The syntax for using a basic SELECT statement is:

SELECT column_name(s) FROM base_table_name

&lt;br /&gt;

Example:

To select the _MovieID_ and _MovieName_ columns from the _Movies_ table, execute the following query:

SELECT MovieID, MovieName from Movies

&lt;br /&gt;

It will generate the following output:

&lt;table class=&#34;content-table&#34;&gt;
&lt;thead&gt;
&lt;tr&gt;
&lt;th&gt;&lt;strong&gt;MovieID&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;MovieName&lt;/strong&gt;&lt;/th&gt;
&lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
&lt;tr&gt;
&lt;td&gt;2056&lt;/td&gt;
&lt;td&gt;The First Purge&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;2057&lt;/td&gt;
&lt;td&gt;Ant-Man and the Wasp&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;2058&lt;/td&gt;
&lt;td&gt;Hotel Transylvania 3: Summer Vacation&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;2059&lt;/td&gt;
&lt;td&gt;Skyscraper&lt;/td&gt;
&lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;

&lt;br /&gt;

For columns that have been named using integers, you need to add the backtick **`** punctuation to diffrencitate between column name and value.

For example, a SELECT query on a table called *Numbers* with a column named *01* can be written in the following manner

SELECT `01` FROM Numbers&lt;br /&gt;

Note: You can fetch a maximum of 20 columns and a maximum of 300 rows in one SELECT query. If you require more records to be fetched, you can use the LIMIT clause to iterate the query and specify the offset and value accordingly.

&lt;br /&gt;

### SELECT \*

You can fetch records from all the columns of a base table, instead of selecting records from a particular column or columns, by using a &#39;\*&#39; following the SELECT statement. The &#39;\*&#39; denotes all the columns of the base table.

The syntax for selecting all the columns from a base table is:

SELECT * FROM base_table_name

&lt;br /&gt;

Note: SELECT \* allows you to fetch a maximum of 300 rows in one query. If you require more records to be fetched, you can use the LIMIT clause to iterate the query and specify the offset and value accordingly.

Example:

To display the records from all the columns of the _Movies_ table, execute the following query:

SELECT * FROM Movies


This will display records from all the columns in the _Movies_ table.

&lt;table class=&#34;content-table&#34;&gt;
&lt;thead&gt;
&lt;tr&gt;
&lt;th&gt;&lt;strong&gt;MovieID&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;MovieName&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;ShowDate&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;ShowTime&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;TheaterID&lt;/strong&gt;&lt;/th&gt;
&lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
&lt;tr&gt;
&lt;td&gt;2056&lt;/td&gt;
&lt;td&gt;The First Purge&lt;/td&gt;
&lt;td&gt;2018-07-13&lt;/td&gt;
&lt;td&gt;13:00:00&lt;/td&gt;
&lt;td&gt;047&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;2057&lt;/td&gt;
&lt;td&gt;Ant-Man and the Wasp&lt;/td&gt;
&lt;td&gt;2018-07-13&lt;/td&gt;
&lt;td&gt;14:20:00&lt;/td&gt;
&lt;td&gt;052&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;2058&lt;/td&gt;
&lt;td&gt;Hotel Transylvania 3: Summer Vacation&lt;/td&gt;
&lt;td&gt;2018-07-14&lt;/td&gt;
&lt;td&gt;17:00:00&lt;/td&gt;
&lt;td&gt;052&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;2059&lt;/td&gt;
&lt;td&gt;Skyscraper&lt;/td&gt;
&lt;td&gt;2018-07-14&lt;/td&gt;
&lt;td&gt;21:30:00&lt;/td&gt;
&lt;td&gt;053&lt;/td&gt;
&lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;

Before we discuss the various clauses and statements available for the SELECT operation, let&#39;s discuss the INSERT, UPDATE, and DELETE operations.

--------------------------------------------------------------------------------
title: "General Syntax of INSERT"
description: "ZCQL is Catalyst&#39;s own query language modelled after familiar query languages that you can use to query your app&#39;s database efficiently."
last_updated: "2026-07-02T09:34:09.974Z"
source: "https://docs.catalyst.zoho.com/en/cloud-scale/help/zcql/insert/"
service: "Cloud Scale"
--------------------------------------------------------------------------------


# INSERT


### General Syntax of INSERT

You can insert a record in a table by passing the values for each column of that table for that record.

The general syntax of a basic ZCQL data insertion operation is as follows:

INSERT INTO {BASE_TABLE_NAME} VALUES (VALUE1, VALUE2,..)

You must pass the values in the same order as the columns are present in the table.

Note:&lt;br /&gt;

* Ensure that you provide the right value for a column that matches the column&#39;s data type.
* For columns where the _IsUnique_ constraint is enabled, ensure that you don&#39;t enter values that are already present in other records. Similarly, for the columns where the _IsMandatory_ validator is enabled, ensure that you do not leave the data value blank.
* For a column where the data type is a Foreign Key, you must provide the ROWID of the parent table&#39;s record which it refers, as its value.


Example:

To insert a record in the _Movies_ table, execute the following query:

INSERT INTO Movies VALUES (2060,&#39;Mission: Impossible â€“ Fallout&#39;, &#39;2018-7-27&#39;,
&#39;16:00:00&#39;, 053)


Note: If the values to be inserted are String values, you must pass the values enclosed in single quotations as shown above. 

### Partial Insert

You can also pass values only for specific columns in a table by specifying the column names which the values need to be inserted for. The syntax for a partial insert is as follows:

INSERT INTO {BASE_TABLE_NAME} (COLUMN_NAME1, COLUMN_NAME2,..) VALUES (VALUE1, VALUE2,..)

To insert a record and pass values for the _MovieID_ and _TheaterID_ columns alone in the _Movies_ table, execute the following query:

INSERT INTO Movies (MovieID, TheaterID) VALUES (2061, 052)

&lt;br /&gt;

--------------------------------------------------------------------------------
title: "General Syntax of UPDATE"
description: "ZCQL is Catalyst&#39;s own query language modelled after familiar query languages that you can use to query your app&#39;s database efficiently."
last_updated: "2026-07-02T09:34:09.979Z"
source: "https://docs.catalyst.zoho.com/en/cloud-scale/help/zcql/update/"
service: "Cloud Scale"
--------------------------------------------------------------------------------


# UPDATE

### General Syntax of UPDATE

The UPDATE command enables you to update specific column values of existing records of a table in the Data Store. You can update the values of columns based on certain conditions. These conditions can be specified using the WHERE clause, which we will discuss later on in detail.

The general syntax of a basic ZCQL data updation operation is as follows:

UPDATE {BASE_TABLE_NAME} SET {COLUMN_NAME}={VALUE}[WHERE {WHERE_CONDITION}]


Note:&lt;br /&gt;

* Ensure that you provide the right value for a column that matches the column&#39;s data type.
* For columns where the _IsUnique_ constraint is enabled, ensure that you don&#39;t enter values that are already present in other records. Similarly, for the columns where the _IsMandatory_ validator is enabled, ensure that you do not leave the data value blank.
* For a column where the data type is a Foreign Key, you must provide the ROWID of the parent table&#39;s record which it refers, as its value.


Example:

To update the value of a specific movie name referred to by its _MovieID_ in the _Movies_ table, execute the following query:

UPDATE Movies SET MovieName=&#39;The Equalizer 2&#39;WHERE MovieID=2056

&lt;br /&gt;

Note: Similar to data insertion, if the values to be updated are String values, you must pass the values enclosed in single quotations.

--------------------------------------------------------------------------------
title: "General Syntax of DELETE"
description: "ZCQL is Catalyst&#39;s own query language modelled after familiar query languages that you can use to query your app&#39;s database efficiently."
last_updated: "2026-07-02T09:34:09.979Z"
source: "https://docs.catalyst.zoho.com/en/cloud-scale/help/zcql/delete/"
service: "Cloud Scale"
--------------------------------------------------------------------------------


# DELETE

### General Syntax of DELETE

The DELETE command enables you to delete one or more records from a table permanently. You can indicate the records to be deleted using the WHERE clause, which is explained in the next section, and specify the conditions.

The general syntax of a basic DELETE statement is as follows:

DELETE FROM {BASE_TABLE_NAME}[WHERE {WHERE_CONDITION}]


Example:

To delete the record of a specific show date in a particular theater from the Movies table, you can execute this query:

DELETE FROM Movies WHERE MovieID=2059 AND ShowDate=&#39;2018-07-14&#39; AND TheaterID=053

&lt;br /&gt;

Note: If you specify a string value in the WHERE condition, you must pass it enclosed in a single quotation.

--------------------------------------------------------------------------------
title: "WHERE Clause"
description: "ZCQL is Catalyst&#39;s own query language modelled after familiar query languages that you can use to query your app&#39;s database efficiently."
last_updated: "2026-07-02T09:34:09.979Z"
source: "https://docs.catalyst.zoho.com/en/cloud-scale/help/zcql/where/"
service: "Cloud Scale"
--------------------------------------------------------------------------------


# WHERE Clause

### Introduction

The WHERE clause is used to filter the data records on the basis of a specified condition or a set of conditions in the search queries. When the WHERE condition is used in a query, the data records are verified based on the specified conditions, and the commands are executed only on the records that satisfy the conditions.

For example, the syntax for using the WHERE condition in a SELECT statement is:

SELECT column_name(s) FROM base_table_name WHERE condition


The WHERE condition can be used with the UPDATE and DELETE statements as well.

&lt;br /&gt;

### Operators Supported by the WHERE Clause

You can use the following operators in the WHERE conditions in ZCQL queries:

&lt;table class=&#34;content-table&#34;&gt;
&lt;thead&gt;
&lt;tr&gt;
&lt;th class=&#34;w30p&#34;&gt;&lt;strong&gt;Operators&lt;/strong&gt;&lt;/th&gt;
&lt;th class=&#34;w70p&#34;&gt;&lt;strong&gt;Description&lt;/strong&gt;&lt;/th&gt;
&lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
&lt;tr&gt;
&lt;td&gt;=&lt;/td&gt;
&lt;td&gt;Equal to&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;IS&lt;/td&gt;
&lt;td&gt;TRUE if the operand is the same as the value&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;IS NULL&lt;/td&gt;
&lt;td&gt;TRUE if the operand is a null value&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;IS NOT NULL&lt;/td&gt;
&lt;td&gt;TRUE if the operand is not a null value&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;!=&lt;/td&gt;
&lt;td&gt;Not equal to&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;LIKE&lt;/td&gt;
&lt;td&gt;TRUE if the operand matches a pattern&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;NOT LIKE&lt;/td&gt;
&lt;td&gt;TRUE if the operand does not match a pattern&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;BETWEEN&lt;/td&gt;
&lt;td&gt;TRUE if the operand value is between the start and end values&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;IN&lt;/td&gt;
&lt;td&gt;TRUE if the operand is equal to a list of expressions&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;NOT IN&lt;/td&gt;
&lt;td&gt;TRUE if the operand is not equal to a list of expressions&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;&amp;gt;&lt;/td&gt;
&lt;td&gt;Greater than&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;&amp;gt;=&lt;/td&gt;
&lt;td&gt;Greater than or equal to&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;&amp;lt;&lt;/td&gt;
&lt;td&gt;Lesser than&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;&amp;lt;=&lt;/td&gt;
&lt;td&gt;Lesser than or equal to&lt;/td&gt;
&lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;

&lt;br /&gt;

Example:

To view a list of the movies that are screened on days other than July 13, 2018 from the Movies table, you can specify
the date condition in the query using the WHERE clause in the following way:

SELECT MovieName, ShowDate FROM Movies WHERE ShowDate IS &#39;2018-07-14&#39;


This will generate the following output:

&lt;table class=&#34;content-table&#34;&gt;
&lt;thead&gt;
&lt;tr&gt;
&lt;th&gt;&lt;strong&gt;MovieName&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;ShowDate&lt;/strong&gt;&lt;/th&gt;
&lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
&lt;tr&gt;
&lt;td&gt;Hotel Transylvania 3: Summer Vacation&lt;/td&gt;
&lt;td&gt;2018-07-14&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;Skyscraper&lt;/td&gt;
&lt;td&gt;2018-07-14&lt;/td&gt;
&lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;

&lt;br /&gt;

### Multiple WHERE Conditions

You can specify a maximum of five WHERE conditions in a single query. When multiple WHERE conditions are specified, you can use either an AND or an OR operator to link the conditions together. The functionalities of the AND and OR operators are:

* AND: Produces only the data records that satisfy both of the conditions that are associated with the AND operator.

* OR: Produces the data records that satisfy either of the conditions that are associated with the OR operator.

For example, the syntax for using multiple WHERE conditions in a SELECT statement is:

SELECT column_name(s)
FROM base_table_name
WHERE condition_1 AND|OR condition_2.. AND|OR condition_5



Example:

To view a list of the show dates and show times from the _Movies_ table for either &#39;The First Purge&#39; or &#39;Skyscraper&#39; movies that are screened on July 14, execute the following query:

SELECT MovieName, ShowDate, ShowTime FROM Movies WHERE MovieName=&#39;The First Purge&#39; OR MovieName=&#39;Skyscraper&#39; AND ShowDate=&#39;2018-07-14&#39;


There is only one record that matches the above conditions. The query will therefore generate the following result:

&lt;table class=&#34;content-table&#34;&gt;
&lt;thead&gt;
&lt;tr&gt;
&lt;th&gt;&lt;strong&gt;MovieName&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;ShowDate&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;ShowTime&lt;/strong&gt;&lt;/th&gt;
&lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
&lt;tr&gt;
&lt;td&gt;Skyscraper&lt;/td&gt;
&lt;td&gt;2018-07-14&lt;/td&gt;
&lt;td&gt;21:30:00&lt;/td&gt;
&lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;

&lt;br /&gt;

### LIKE Statement

The LIKE condition enables you to indicate records which contain a specific criteria and select all records that match that condition. For example, you can indicate a specific alphabet that the records you require to be fetched must begin with, or a particular value that they must contain.

For example, the syntax of the LIKE condition in an UPDATE statement is as follows:

UPDATE base_table_name
SET column_name(s)=value(s)
WHERE condition
LIKE *value* 


The &#39;\*&#39; can be used either before or after, or both before and after, the value that you specify. The &#39;\*&#39; is essentially a placeholder that indicates that any value can be replaced in its stead.

For example, to indicate that all records in a table that begin with the alphabet &#39;A&#39; must be fetched, you can enter the LIKE value as &#39;A\*&#39;. This specifies that after the letter A, any values can follow.

Example:

To update the records where the movie names begin with the letter &#39;S&#39; in the _Movies_ table, execute the following query:

UPDATE Movies SET ShowDate=&#39;2018-07-17&#39; WHERE MovieName like &#39;S*&#39;


This will update the following record and set the value:

&lt;table class=&#34;content-table&#34;&gt;
&lt;thead&gt;
&lt;tr&gt;
&lt;th&gt;&lt;strong&gt;MovieID&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;MovieName&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;ShowDate&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;ShowTime&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;TheaterID&lt;/strong&gt;&lt;/th&gt;
&lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
&lt;tr&gt;
&lt;td&gt;2059&lt;/td&gt;
&lt;td&gt;Skyscraper&lt;/td&gt;
&lt;td&gt;2018-07-17&lt;/td&gt;
&lt;td&gt;21:30:00&lt;/td&gt;
&lt;td&gt;053&lt;/td&gt;
&lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;
&lt;br /&gt;

Wildcard syntax and symbols such as \* and ? are also permitted to be used in ZCQL statements defined using the LIKE condition statement.

&lt;table class=&#34;content-table&#34;&gt;
	&lt;thead&gt;
		&lt;tr&gt;
			&lt;th class=&#34;w30p&#34;&gt;Wildcard Syntax&lt;/th&gt;
			&lt;th class=&#34;w70p&#34;&gt;Definition&lt;/th&gt;
		&lt;/tr&gt;
	&lt;/thead&gt;
	&lt;tbody&gt;
		&lt;tr&gt;
			&lt;td&gt;\*&lt;/td&gt;
			&lt;td&gt;Matches zero or more characters&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;?&lt;/td&gt;
			&lt;td&gt;Matches exactly one character&lt;/td&gt;
		&lt;/tr&gt;
	&lt;/tbody&gt;
&lt;/table&gt;

### BETWEEN Statement

The BETWEEN condition enables you to filter records by indicating the starting and ending values in a particular column containing numerical values. For example, you can select all the records where the percentage values are between 70 and 80.

For example, the syntax of a BETWEEN condition in a DELETE statement is as follows:

DELETE FROM base_table_name
WHERE condition
BETWEEN Value1 AND Value2

&lt;br /&gt;

Note: You can use the BETWEEN statement only for selecting &#39;Int&#39; or &#39;Double&#39; values in the Catalyst Data Store table. You will not be able to use it for any other data types.

Example:

To delete the records where the value of the MovieID is between 2056 and 2059 in the _Movies_ table, execute the following query:

DELETE FROM Movies WHERE MovieID BETWEEN 2056 AND 2059


The following records from the table will be deleted:

&lt;table class=&#34;content-table&#34;&gt;
&lt;thead&gt;
&lt;tr&gt;
&lt;th&gt;&lt;strong&gt;MovieID&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;MovieName&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;ShowDate&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;ShowTime&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;TheaterID&lt;/strong&gt;&lt;/th&gt;
&lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
&lt;tr&gt;
&lt;td&gt;2057&lt;/td&gt;
&lt;td&gt;Ant-Man and the Wasp&lt;/td&gt;
&lt;td&gt;2018-07-13&lt;/td&gt;
&lt;td&gt;14:20:00&lt;/td&gt;
&lt;td&gt;052&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;2058&lt;/td&gt;
&lt;td&gt;Hotel Transylvania 3: Summer Vacation&lt;/td&gt;
&lt;td&gt;2018-07-14&lt;/td&gt;
&lt;td&gt;17:00:00&lt;/td&gt;
&lt;td&gt;052&lt;/td&gt;
&lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;

Note: To produce the exact opposite result, you can use the NOT BETWEEN statement. The same syntax and conditions of a BETWEEN statement applies to NOT BETWEEN statements. 

&lt;br /&gt;

### Column to Column Comparison

You can compare two columns of the same table or in different tables by **referring to the column names with their respective table names** in the LHS and RHS of the comparison. The result of the comparison will return the rows that contain the same value for column1 and column2 in the table.

This comparison support in WHERE clause is applicable to the SELECT, UPDATE and DELETE queries.

You can compare any two columns that are of the following data types : BOOLEAN, DOUBLE, DATE, DATETIME, ENCRYPTED, VARCHAR, TEXT, INT and BIGINT.

Note: You cannot compare columns of two different data types. &lt;br /&gt;

**SELECT:**

The general syntax for column comparison within the same table is as follows:

SELECT * FROM tablename WHERE columnname1 = tablename.columnname2

**Example**:&lt;br /&gt;

Select MovieName FROM Movies WHERE Actor = Movies.Producer

&lt;table class=&#34;content-table&#34; style=&#34;width:30%&#34;&gt;
&lt;thead&gt;
    &lt;tr&gt;
        &lt;th&gt;MovieName&lt;/th&gt;
    &lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
    &lt;tr&gt;
        &lt;td&gt;The White River Kid&lt;/td&gt;
    &lt;/tr&gt;
    &lt;tr&gt;
        &lt;td&gt;Duplex&lt;/td&gt;
    &lt;/tr&gt;
    &lt;tr&gt;
        &lt;td&gt;Oppenheimer&lt;/td&gt;
    &lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;


**UPDATE:**

UPDATE Movies SET self_produced = &#34;Yes&#34; WHERE Actor = Movies.Producer

**DELETE:**

DELETE FROM Movies WHERE Actor = Movies.Producer &lt;br /&gt;

#### Comparison of Columns in Different Tables

You can also compare columns of two different tables as shown in the syntax below :

SELECT tablename1.columnname1, tablename2.columnname1 
FROM tablename2 LEFT JOIN tablename1 ON tablename2.columnname1 = tablename1.columnname2 
WHERE tablename1.columnname1 = tablename2.columnname2

**Example**:

SELECT Movies.name, Theatres.city from Theatres left join Movies on Theatres.ROWID = Movies.theatreID where Movies.distributionCity = theatre.city &lt;br /&gt;

&lt;table class=&#34;content-table&#34;&gt;
	&lt;thead&gt;
		&lt;tr&gt;
			&lt;th&gt;Name&lt;/th&gt;
			&lt;th&gt;CIty&lt;/th&gt;
		&lt;/tr&gt;
	&lt;/thead&gt;
	&lt;tbody&gt;
		&lt;tr&gt;
			&lt;td&gt;Dark Knight Rises&lt;/td&gt;
			&lt;td&gt;Los Angeles&lt;/td&gt;
		&lt;/tr&gt;
		&lt;tr&gt;
			&lt;td&gt;Titanic&lt;/td&gt;
			&lt;td&gt;New York&lt;/td&gt;
		&lt;/tr&gt;
	&lt;/tbody&gt;
&lt;/table&gt;
&lt;br /&gt;

Similarly, you can compare columns belonging to two different tables while executing the UPDATE and DELETE queries.


### Subqueries in WHERE Clause

A subquery is a query that is written inside another query statement. Catalyst enables you to execute simple singular subqueries with WHERE clause.  You can write subqueries with the WHERE clause in SELECT, UPDATE and DELETE queries.

The syntax of a subquery with WHERE clause is given below:

SELECT column_name FROM table_name WHERE column_name operator (SELECT column_name FROM table_name)
&lt;br /&gt;

**Example Database**

The employee details of Zylker Technologies are being maintained in the Data Store in the *Zylker_Employee_DB* table. The table contains the following columns and rows:

&lt;table class=&#34;content-table&#34;&gt;
	&lt;thead&gt;
		&lt;tr&gt;
			&lt;th class=&#34;w15p&#34;&gt;ID&lt;/th&gt;
			&lt;th class=&#34;w30p&#34;&gt;Name&lt;/th&gt;
			&lt;th class=&#34;w30p&#34;&gt;Department&lt;/th&gt;
            &lt;th class=&#34;w25p&#34;&gt;Salary&lt;/th&gt;
		&lt;/tr&gt;
	&lt;/thead&gt;
	&lt;tbody&gt;
		&lt;tr&gt;
			&lt;td&gt;ZT-001&lt;/td&gt;
			&lt;td&gt;Amelia Burrows&lt;/td&gt;
			&lt;td&gt;Product Management&lt;/td&gt;
            &lt;td&gt;15000&lt;/td&gt;
		&lt;/tr&gt;
		&lt;tr&gt;
			&lt;td&gt;ZT-2001&lt;/td&gt;
			&lt;td&gt;Bruce Wayne&lt;/td&gt;
			&lt;td&gt;Sr. Management&lt;/td&gt;
            &lt;td&gt;85000&lt;/td&gt;
		&lt;/tr&gt;
		&lt;tr&gt;
			&lt;td&gt;ZT-239&lt;/td&gt;
			&lt;td&gt;Clark Kane&lt;/td&gt;
			&lt;td&gt;Media Relations&lt;/td&gt;
            &lt;td&gt;85000&lt;/td&gt;
		&lt;/tr&gt;
		&lt;tr&gt;
			&lt;td&gt;ZT-4289&lt;/td&gt;
			&lt;td&gt;Michelle Mascarenhas&lt;/td&gt;
			&lt;td&gt;Finance&lt;/td&gt;
            &lt;td&gt;89000&lt;/td&gt;
		&lt;/tr&gt;
	&lt;/tbody&gt;
&lt;/table&gt;

An example subquery statement to list the salaries and the names of the employees who earn greater than the minimum salaried employee is given below:

SELECT Name, Salary FROM Zylker_Employee_DB WHERE Salary &gt; (SELECT MIN (Salary) FROM Zylker_Employee_DB)
&lt;br /&gt;

&lt;br /&gt;
&lt;table class=&#34;content-table&#34;&gt;
	&lt;thead&gt;
		&lt;tr&gt;
			&lt;th class=&#34;w50p&#34;&gt;Zylker_Employee_DB.Salary&lt;/th&gt;
			&lt;th class=&#34;w50p&#34;&gt;Zylker_Employee_DB.Name&lt;/th&gt;
		&lt;/tr&gt;
	&lt;/thead&gt;
	&lt;tbody&gt;
		&lt;tr&gt;
			&lt;td&gt;15000&lt;/td&gt;
			&lt;td&gt;Amelia Burrows&lt;/td&gt;
		&lt;/tr&gt;
		&lt;tr&gt;
			&lt;td&gt;85000&lt;/td&gt;
			&lt;td&gt;Bruce Wayne&lt;/td&gt;
		&lt;/tr&gt;
		&lt;tr&gt;
			&lt;td&gt;89000&lt;/td&gt;
			&lt;td&gt;Michelle Mascarenhas&lt;/td&gt;
		&lt;/tr&gt;
	&lt;/tbody&gt;
&lt;/table&gt;

Note: 

* This functionality is only available in ZCQL V2.

* From December 01st, 2024, all your current projects in all your Orgs present in the Development Environment will be automatically mapped to ZCQL V2 Parser.

* From April 01st, 2025, all the projects present in all Orgs that have already been mapped to ZCQL V2 Parser in Development Environment will be automatically mapped to ZCQL V2 Parser in the Production Environment, if and when production is enabled for the project.

&lt;br /&gt;

--------------------------------------------------------------------------------
title: "HAVING Clause"
description: "ZCQL is Catalyst&#39;s own query language modelled after familiar query languages that you can use to query your app&#39;s database efficiently."
last_updated: "2026-07-02T09:34:09.983Z"
source: "https://docs.catalyst.zoho.com/en/cloud-scale/help/zcql/having/"
service: "Cloud Scale"
--------------------------------------------------------------------------------


# HAVING Clause

### Introduction

The HAVING clause is used to select data records based on a specified condition. You can also apply ZCQL functions in the query using this clause. The HAVING clause can only be used with SELECT queries.

The syntax for using the HAVING clause is shown below:

SELECT column_name FROM base_table_name GROUP BY column_name HAVING column_name OPERATOR condition

### Operators Supported by the HAVING Clause

You can use the following operators in the HAVING conditions in ZCQL SELECT queries:

&lt;table class=&#34;content-table&#34;&gt;
	&lt;thead&gt;
		&lt;tr&gt;
			&lt;th class=&#34;w25p&#34;&gt;Operators&lt;/th&gt;
			&lt;th class=&#34;w75p&#34;&gt;Description&lt;/th&gt;
		&lt;/tr&gt;
	&lt;/thead&gt;
	&lt;tbody&gt;
		&lt;tr&gt;
			&lt;td&gt;=&lt;/td&gt;
			&lt;td&gt;Equal to&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;IS&lt;/td&gt;
			&lt;td&gt;TRUE if the operand is the same as the value&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;IS NULL&lt;/td&gt;
			&lt;td&gt;TRUE if the operand is a null value&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;IS NOT NULL&lt;/td&gt;
			&lt;td&gt;TRUE if the operand is not a null value&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;=!&lt;/td&gt;
			&lt;td&gt;Not equal to&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;LIKE&lt;/td&gt;
			&lt;td&gt;TRUE if the operand matches a pattern&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;NOT LIKE&lt;/td&gt;
			&lt;td&gt;TRUE if the operand does not match a pattern&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;BETWEEN&lt;/td&gt;
			&lt;td&gt;TRUE if the operand value is between the start and end values&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;IN&lt;/td&gt;
			&lt;td&gt;TRUE if the operand is equal to a list of expressions&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;NOT IN&lt;/td&gt;
			&lt;td&gt;TRUE if the operand is not equal to a list of expressions&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;&amp;gt;&lt;/td&gt;
			&lt;td&gt;Greater than&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;&amp;gt;=&lt;/td&gt;
			&lt;td&gt;Greater than or equal to&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;&amp;lt;&lt;/td&gt;
			&lt;td&gt;Lesser than&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;&amp;lt;=&lt;/td&gt;
			&lt;td&gt;Lesser than or equal to&lt;/td&gt;
		&lt;/tr&gt;
	&lt;/tbody&gt;
&lt;/table&gt;

### ZCQL Functions with HAVING Clause

ZCQL functions like SUM(), COUNT(), AVG(), etc., can be used with the HAVING clause in a SELECT query.

**Example Database**:

The employee details of Zylker Technologies are being maintained in the Data Store in the *Zylker_Employee_DB* table. The table contains the following columns and rows:

&lt;table class=&#34;content-table&#34;&gt;
	&lt;thead&gt;
		&lt;tr&gt;
			&lt;th class=&#34;w15p&#34;&gt;ID&lt;/th&gt;
			&lt;th class=&#34;w30p&#34;&gt;Name&lt;/th&gt;
			&lt;th class=&#34;w30p&#34;&gt;Department&lt;/th&gt;
            &lt;th class=&#34;w25p&#34;&gt;Salary&lt;/th&gt;
		&lt;/tr&gt;
	&lt;/thead&gt;
	&lt;tbody&gt;
		&lt;tr&gt;
			&lt;td&gt;ZT-001&lt;/td&gt;
			&lt;td&gt;Amelia Burrows&lt;/td&gt;
			&lt;td&gt;Product Management&lt;/td&gt;
            &lt;td&gt;15000&lt;/td&gt;
		&lt;/tr&gt;
		&lt;tr&gt;
			&lt;td&gt;ZT-2001&lt;/td&gt;
			&lt;td&gt;Bruce Wayne&lt;/td&gt;
			&lt;td&gt;Sr. Management&lt;/td&gt;
            &lt;td&gt;85000&lt;/td&gt;
		&lt;/tr&gt;
		&lt;tr&gt;
			&lt;td&gt;ZT-239&lt;/td&gt;
			&lt;td&gt;Clark Kane&lt;/td&gt;
			&lt;td&gt;Media Relations&lt;/td&gt;
            &lt;td&gt;85000&lt;/td&gt;
		&lt;/tr&gt;
		&lt;tr&gt;
			&lt;td&gt;ZT-4289&lt;/td&gt;
			&lt;td&gt;Michelle Mascarenhas&lt;/td&gt;
			&lt;td&gt;Finance&lt;/td&gt;
            &lt;td&gt;89000&lt;/td&gt;
		&lt;/tr&gt;
	&lt;/tbody&gt;
&lt;/table&gt;

Lets, use the AVG() ZCQL function, with the HAVING clause in an example SELECT query. 
&lt;br /&gt;

SELECT Name, Department, Salary FROM Zylker_Employee_DB GROUP BY Department HAVING AVG(Salary) &gt; 50000

&lt;br /&gt;
&lt;table class=&#34;content-table&#34;&gt;
	&lt;thead&gt;
		&lt;tr&gt;
			&lt;th class=&#34;w30p&#34;&gt;Zylker_Employee_DB.Salary&lt;/th&gt;
			&lt;th class=&#34;w35p&#34;&gt;Zylker_Employee_DB.Department&lt;/th&gt;
			&lt;th class=&#34;w35p&#34;&gt;Zylker_Employee_DB.Name&lt;/th&gt;
		&lt;/tr&gt;
	&lt;/thead&gt;
	&lt;tbody&gt;
		&lt;tr&gt;
			&lt;td&gt;85000&lt;/td&gt;
			&lt;td&gt;Sr. Management&lt;/td&gt;
			&lt;td&gt;Bruce Wayne&lt;/td&gt;
		&lt;/tr&gt;
		&lt;tr&gt;
			&lt;td&gt;89000&lt;/td&gt;
			&lt;td&gt;Finance&lt;/td&gt;
			&lt;td&gt;Michelle Mascarenhas&lt;/td&gt;
		&lt;/tr&gt;
	&lt;/tbody&gt;
&lt;/table&gt;

Note: 

* This functionality is only available in ZCQL V2.

* From December 01st, 2024, all your current projects in all your Orgs present in the Development Environment will be automatically mapped to ZCQL V2 Parser.

* From April 01st, 2025, all the projects present in all Orgs that have already been mapped to ZCQL V2 Parser in Development Environment will be automatically mapped to ZCQL V2 Parser in the Production Environment, if and when production is enabled for the project.

--------------------------------------------------------------------------------
title: "JOIN Clause"
description: "ZCQL is Catalyst&#39;s own query language modelled after familiar query languages that you can use to query your app&#39;s database efficiently."
last_updated: "2026-07-02T09:34:09.984Z"
source: "https://docs.catalyst.zoho.com/en/cloud-scale/help/zcql/joins/"
service: "Cloud Scale"
--------------------------------------------------------------------------------



# JOIN Clause

### Introduction

The JOIN clause is used to combine rows from two or more tables in a SELECT query, based on a related column between them. The rows from all the tables are generated together with the common column merged.

Before we learn more about the JOIN clause, let&#39;s understand a few key terms related to joins:

1. Primary Key: A primary key is a unique identifier of a record in a table. A table can have one column as its primary key column, and the value for each record in this column must be unique, is mandatory, and cannot be duplicated.
2. Foreign Key: A foreign key column in one table uniquely identifies a row in another table or the same table. The foreign key of the second table refers to the primary key of the first table.
3. Parent Table: In the JOIN clause, the parent table is the base table that the join is performed based on.
4. Join Table: The join table is the secondary table or the child table which is being merged with the parent table in the JOIN clause.

Note: Joins between two tables are only possible if there is a relationship between them. One of the tables must refer to the other table&#39;s primary key column, so either the join table must have a foreign key column of the parent table, or the parent table must have a foreign key column of the join table.

In our example, the _MovieID_ column is the primary key of the _Movies_ table as it holds the unique identification number of a movie.

&lt;br /&gt;

Example Database:

Let&#39;s create a table named &#34;Theaters&#34; in the ticket booking application which specifies the locations of all the theaters that are registered with the application.

Sample records from the Theaters table are given below:
&lt;table class=&#34;content-table&#34;&gt;
&lt;thead&gt;
&lt;tr&gt;
&lt;th&gt;&lt;strong&gt;TheaterID&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;TheaterName&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;Location&lt;/strong&gt;&lt;/th&gt;
&lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
&lt;tr&gt;
&lt;td&gt;047&lt;/td&gt;
&lt;td&gt;The Express Cinemas&lt;/td&gt;
&lt;td&gt;New York City&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;048&lt;/td&gt;
&lt;td&gt;ANC Cinemas&lt;/td&gt;
&lt;td&gt;Rochester&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;052&lt;/td&gt;
&lt;td&gt;Cosmos Theater&lt;/td&gt;
&lt;td&gt;Albany&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;053&lt;/td&gt;
&lt;td&gt;FunTime Cinemas&lt;/td&gt;
&lt;td&gt;Buffalo&lt;/td&gt;
&lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;

The _TheaterID_ column is the primary key of the _Theaters_ table as it holds the unique identification numbers of the theaters. The _TheaterID_ column in the _Movies_ table is the foreign key to the _TheaterID_ column in the _Theaters_ table.

Note: When you use a JOIN clause, you must specify the column names and their table names for each column in the query as: &#39;_table\_name.column\_name_&#39;&#39;. For example: &#39;_Movies.MovieName_&#39;, &#39;_Theaters.Location_&#39;

If you don&#39;t specify the table name with the column name in a query, then by default it is considered to be a column in the base table.

&lt;br /&gt;

### Types of Joins

There are two types of Joins that can be performed in ZCQL.
&lt;br /&gt;
&lt;br /&gt;

#### INNER JOIN

The INNER JOIN returns the records that have matching values in both the parent table and the join table. When you use an inner join on two tables, only the records whose values match for the specified columns in both the tables are produced as the output.&lt;br /&gt; The syntax for using an INNER JOIN is:&lt;br /&gt;


SELECT column_name(s)
FROM parent_table_name
INNER JOIN join_table_name
ON parent_table_name.column_name = join_table_name.column_name


	
Example:&lt;br /&gt; 

To view a list of the movie names, show dates, and show times from the _Movies_ table along with the theater names from the _Theaters_ table, execute the following query:
&lt;br /&gt;


SELECT Movies.MovieName, Theatres.TheaterName, Movies.ShowDate, Movies.ShowTime, 
FROM Movies INNER JOIN Theatres ON Movies.TheaterID = Theatres.TheaterID
 

This will generate the following output:


&lt;table class=&#34;content-table&#34;&gt;
&lt;thead&gt;
&lt;tr&gt;
&lt;th&gt;&lt;strong&gt;MovieName&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;TheaterName&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;ShowDate&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;ShowTime&lt;/strong&gt;&lt;/th&gt;
&lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
&lt;tr&gt;
&lt;td&gt;Ant-Man and the Wasp&lt;/td&gt;
&lt;td&gt;The Express Cinemas&lt;/td&gt;
&lt;td&gt;2018-07-13&lt;/td&gt;
&lt;td&gt;13:30:00&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;Hotel Transylvania 3: Summer Vacation&lt;/td&gt;
&lt;td&gt;Cosmos Theater&lt;/td&gt;
&lt;td&gt;2018-07-13&lt;/td&gt;
&lt;td&gt;14:20:00&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;The First Purge&lt;/td&gt;
&lt;td&gt;Cosmos Theater&lt;/td&gt;
&lt;td&gt;2018-07-14&lt;/td&gt;
&lt;td&gt;17:00:00&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;The First Purge&lt;/td&gt;
&lt;td&gt;FunTime Cinemas&lt;/td&gt;
&lt;td&gt;2018-07-14&lt;/td&gt;
&lt;td&gt;21:30:00&lt;/td&gt;
&lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;

&lt;br /&gt;


#### LEFT JOIN 

The LEFT JOIN returns all the records from the parent table and the matched records from the join table. When you use a left join on two tables, all records from the parent table are returned, even if they do not have matches from the join table. The result is displayed as &#39;NULL&#39; for records that do not have a match in the join table.
&lt;br /&gt; 

The syntax for using a LEFT JOIN is:&lt;br /&gt;

SELECT column_name(s)
			FROM parent_table_name
			LEFT JOIN join_table_name
			ON parent_table_name.column_name = join_table_name.column_name

Example:&lt;br /&gt; 

To view a list of theaters and their locations from the _Theaters_ table along with the movies that are being screened in the theaters from the _Movies_ table, execute the following query:&lt;br /&gt;

SELECT Theaters.TheaterName, Theaters.Location, Movies.MovieName
FROM Theaters
LEFT JOIN Movies
ON Theaters.TheaterID = Movies.TheaterID

This will generate the following output:&lt;br /&gt;
&lt;table class=&#34;content-table&#34;&gt;
&lt;thead&gt;
&lt;tr&gt;
&lt;th&gt;&lt;strong&gt;TheaterName&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;Location&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;MovieName&lt;/strong&gt;&lt;/th&gt;
&lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
&lt;tr&gt;
&lt;td&gt;The Express Cinemas&lt;/td&gt;
&lt;td&gt;New York City&lt;/td&gt;
&lt;td&gt;The First Purge&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;ANC Cinemas&lt;/td&gt;
&lt;td&gt;Rochester&lt;/td&gt;
&lt;td&gt;&lt;strong&gt;NULL&lt;/strong&gt;&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;Cosmos Theater&lt;/td&gt;
&lt;td&gt;Albany&lt;/td&gt;
&lt;td&gt;Hotel Transylvania 3: Summer Vacation&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;FunTime Cinemas&lt;/td&gt;
&lt;td&gt;Buffalo&lt;/td&gt;
&lt;td&gt;Skyscraper&lt;/td&gt;
&lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;

Since there are no matching records for ANC Cinemas in the Movies table, the result is displayed as &#39;NULL&#39;.

&lt;br /&gt;
&lt;br /&gt;

### Multiple Joins

You can combine a maximum of **four** joins in a single ZCQL query. However, you can only write **one** JOIN condition for each join clause. This will display the results from four different tables, where one is linked to another using an INNER JOIN or a LEFT JOIN.

Example Database:

Let&#39;s create a table called &#39;Pricing&#39; in the ticket booking application which displays the ticket price in dollars of a single ticket for a particular movie and theater. This table references _TheaterID_ from the _Theaters_ table and _MovieID_ from the _Movies_ table as the foreign keys.

Sample records from the Pricing table are given below:

&lt;table class=&#34;content-table&#34;&gt;
&lt;thead&gt;
&lt;tr&gt;
&lt;th&gt;&lt;strong&gt;TheaterID&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;MovieID&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;Price&lt;/strong&gt;&lt;/th&gt;
&lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
&lt;tr&gt;
&lt;td&gt;047&lt;/td&gt;
&lt;td&gt;2056&lt;/td&gt;
&lt;td&gt;9.20&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;048&lt;/td&gt;
&lt;td&gt;NULL&lt;/td&gt;
&lt;td&gt;&lt;strong&gt;NULL&lt;/strong&gt;&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;052&lt;/td&gt;
&lt;td&gt;2057&lt;/td&gt;
&lt;td&gt;8.64&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;052&lt;/td&gt;
&lt;td&gt;2058&lt;/td&gt;
&lt;td&gt;11.50&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;053&lt;/td&gt;
&lt;td&gt;2059&lt;/td&gt;
&lt;td&gt;7.44&lt;/td&gt;
&lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;


You can execute a query to display the _TheaterName_ from the _Theaters_ table, _MovieName_, _ShowDate_, and _ShowTime_ from the _Movies_ table, and _Price_ from the _Pricing_ table, by executing the following query:

SELECT Theaters.TheaterName,Movies.MovieName, Movies.ShowDate, 
Movies.ShowTime, Pricing.Price
FROM Pricing
LEFT JOIN Movies
ON Theaters.TheaterID = Movies.TheaterID
INNER JOIN Theaters
ON Movies.MovieID = Pricing.MovieID


This will generate the following output:

&lt;table class=&#34;content-table&#34;&gt;
&lt;thead&gt;
&lt;tr&gt;
&lt;th&gt;&lt;strong&gt;TheaterName&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;MovieName&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;ShowDate&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;ShowTime&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;Price&lt;/strong&gt;&lt;/th&gt;
&lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
&lt;tr&gt;
&lt;td&gt;The Express Cinemas&lt;/td&gt;
&lt;td&gt;The First Purge&lt;/td&gt;
&lt;td&gt;2018-07-13&lt;/td&gt;
&lt;td&gt;13:00:00&lt;/td&gt;
&lt;td&gt;9.20&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;ANC Cinemas&lt;/td&gt;
&lt;td&gt;NULL&lt;/td&gt;
&lt;td&gt;NULL&lt;/td&gt;
&lt;td&gt;NULL&lt;/td&gt;
&lt;td&gt;NULL&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;Cosmos Theater&lt;/td&gt;
&lt;td&gt;Ant-Man and the Wasp&lt;/td&gt;
&lt;td&gt;2018-07-13&lt;/td&gt;
&lt;td&gt;14:20:00&lt;/td&gt;
&lt;td&gt;8.64&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;Cosmos Theater&lt;/td&gt;
&lt;td&gt;Hotel Transylvania 3: Summer Vacation&lt;/td&gt;
&lt;td&gt;2018-07-14&lt;/td&gt;
&lt;td&gt;17:00:00&lt;/td&gt;
&lt;td&gt;11.50&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;FunTime Cinemas&lt;/td&gt;
&lt;td&gt;Skyscraper&lt;/td&gt;
&lt;td&gt;2018-07-14&lt;/td&gt;
&lt;td&gt;21:30:00&lt;/td&gt;
&lt;td&gt;7.44&lt;/td&gt;
&lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;

Note: 

* To utilize all the features of the JOIN clause, we recommend you migrate your codebase from ZCQL V1 to ZCQL V2.

* From December 01st, 2024, all your current projects in all your Orgs present in the Development Environment will be automatically mapped to ZCQL V2 Parser.

* From April 01st, 2025, all the projects present in all Orgs that have already been mapped to ZCQL V2 Parser in Development Environment will be automatically mapped to ZCQL V2 Parser in the Production Environment, if and when production is enabled for the project.

* You can learn more on the enhancements and features of ZCQL V2 from this help document.

--------------------------------------------------------------------------------
title: "GROUP BY and ORDER BY"
description: "ZCQL is Catalyst&#39;s own query language modelled after familiar query languages that you can use to query your app&#39;s database efficiently"
last_updated: "2026-07-02T09:34:09.984Z"
source: "https://docs.catalyst.zoho.com/en/cloud-scale/help/zcql/groupby-orderby/"
service: "Cloud Scale"
--------------------------------------------------------------------------------


### GROUP BY Statement

The GROUP BY statement is used to group the records fetched in a search query results by one or more columns. GROUP BY enables identical data to be grouped together and displayed sequentially. When there are duplicate values in a column, the GROUP BY statement displays the duplicates together. The records are then ordered based on other columns.

The GROUP BY statement is associated with the SELECT statement and is often used with ZCQL functions. It is used towards the end of the query and should therefore satisfy the JOIN statements and follow the WHERE conditions.

The basic syntax for using a GROUP BY statement along with the SELECT statement is as follows:

SELECT column_name(s) FROM parent_table_name GROUP BY column_name(s)


&lt;br /&gt;

Example:

To view a list of theaters and their locations from the _Theaters_ table, grouped by the location of the theaters, execute the following query:
SELECT TheaterName, Location FROM Theaters GROUP BY Location 

&lt;br /&gt;

This will generate the following output:
&lt;table class=&#34;content-table&#34;&gt;
&lt;thead&gt;
&lt;tr&gt;
&lt;th&gt;&lt;strong&gt;TheaterName&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;Location&lt;/strong&gt;&lt;/th&gt;
&lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
&lt;tr&gt;
&lt;td&gt;Cosmos Theater&lt;/td&gt;
&lt;td&gt;Albany&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;FunTime Cinemas&lt;/td&gt;
&lt;td&gt;Buffalo&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;The Express Cinemas&lt;/td&gt;
&lt;td&gt;New York City&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;ANC Cinemas&lt;/td&gt;
&lt;td&gt;Rochester&lt;/td&gt;
&lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;


#### BINARYOF() Function

The BINARYOF() function can only be used in a GROUP BY statement. The function can be used in places where you wish to produce a output that is not case sensitive and considers all the values in a coulumn of a table.

The BINARYOF() function can only be used on columns with **VarChar** or **Text** datatype. 


For example, consider the following table *Zylker_EMP*:

&lt;table class=&#34;content-table&#34; style=&#34;width:30%&#34;&gt;
&lt;thead&gt;
    &lt;tr&gt;
        &lt;th&gt;Names&lt;/th&gt;
    &lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
    &lt;tr&gt;
        &lt;td&gt;AMELIA BURROWS&lt;/td&gt;
    &lt;/tr&gt;
    &lt;tr&gt;
        &lt;td&gt;amelia burrows&lt;/td&gt;
    &lt;/tr&gt;
    &lt;tr&gt;
        &lt;td&gt;amelia Burrows&lt;/td&gt;
    &lt;/tr&gt;
    &lt;tr&gt;
        &lt;td&gt;Amelia Burrows&lt;/td&gt;
    &lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;

An example ZCQL statement to illustrate the functionality of BINARYOF() and its possible output is given below:

SELECT Names FROM Zylker_EMP GROUP BY BINARYOF(Names)&lt;br /&gt;


&lt;table class=&#34;content-table&#34; style=&#34;width:30%&#34;&gt;
&lt;thead&gt;
    &lt;tr&gt;
        &lt;th&gt;Zylker_EMP.Names&lt;/th&gt;
    &lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
    &lt;tr&gt;
        &lt;td&gt;AMELIA BURROWS&lt;/td&gt;
    &lt;/tr&gt;
    &lt;tr&gt;
        &lt;td&gt;amelia burrows&lt;/td&gt;
    &lt;/tr&gt;
    &lt;tr&gt;
        &lt;td&gt;amelia Burrows&lt;/td&gt;
    &lt;/tr&gt;
    &lt;tr&gt;
        &lt;td&gt;Amelia Burrows&lt;/td&gt;
    &lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;

Note: 

* This functionality is only available in ZCQL V2.

* From December 01st, 2024, all your current projects in all your Orgs present in the Development Environment will be automatically mapped to ZCQL V2 Parser.

* From April 01st, 2025, all the projects present in all Orgs that have already been mapped to ZCQL V2 Parser in Development Environment will be automatically mapped to ZCQL V2 Parser in the Production Environment, if and when production is enabled for the project.


### ORDER BY Statement

The ORDER BY statement is used to sort the records fetched in a search query results in an ascending or a descending order, based on one or more columns. When the ORDER BY statement is used to sort textual data, it sorts the records in the alphabetical order.

Similar to the GROUP BY statement, the ORDER BY statement is associated with the SELECT statement and is often used after the GROUP BY statement. It is used towards the end of the query, after the JOIN clause statements or the WHERE conditions, if present, but before the LIMIT clause. The ORDER BY statement should then satisfy the JOIN statements and follow the WHERE conditions.

Note: If the ORDER BY statement follows a GROUP BY statement, the ORDER BY statement takes precedence and the results are ordered first based on the ORDER BY statement, and then grouped together based on the GROUP BY statement.

* If there are duplicate values in a column, the ORDER BY statement will display the duplicates together. The records are then ordered based on other columns.

* ZCQL Functions can also be used with ORDER BY statements.

Note: To utilize all the features of the ORDER BY statement, we recommend you migrate your codebase from ZCQL V1 to ZCQL V2. You can learn more on the enhancements and features of ZCQL V2 from this help document

The basic syntax for using a ORDER BY statement with the SELECT statement is as follows:

SELECT column_name(s) FROM parent_table_name ORDER BY column_name(s) [ASC | DESC]


Note:&lt;br /&gt;

* By default, the ORDER BY statement sorts the records in ascending order without using the keyword &#39;ASC&#39;. To sort the records in a descending order, you will have to use the keyword &#39;DESC&#39;.

* In all columns where you use the ORDER BY clause, the ASC and DESC functionality can now be applied. You can also apply ASC and DESC for individual columns.

&lt;br /&gt;

Example:

To view a list of the ticket prices from the Pricing table in descending order for each movie from the _Movies_ table execute the following query:

SELECT Movies.MovieName, Pricing.Price FROM Movies
INNER JOIN Pricing ON Movies.MovieID = Pricing.MovieID
ORDER BY Pricing.Price DESC 

&lt;br /&gt;

This will generate the following output:

&lt;table class=&#34;content-table&#34;&gt;
&lt;thead&gt;
&lt;tr&gt;
&lt;th&gt;&lt;strong&gt;MovieName&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;Price&lt;/strong&gt;&lt;/th&gt;
&lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
&lt;tr&gt;
&lt;td&gt;Hotel Transylvania 3: Summer Vacation&lt;/td&gt;
&lt;td&gt;11.50&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;The First Purge&lt;/td&gt;
&lt;td&gt;9.20&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;Ant-Man and the Wasp&lt;/td&gt;
&lt;td&gt;8.64&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;Skyscraper&lt;/td&gt;
&lt;td&gt;7.44&lt;/td&gt;
&lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;

--------------------------------------------------------------------------------
title: "LIMIT Clause"
description: "ZCQL is Catalyst&#39;s own query language modelled after familiar query languages that you can use to query your app&#39;s database efficiently."
last_updated: "2026-07-02T09:34:09.985Z"
source: "https://docs.catalyst.zoho.com/en/cloud-scale/help/zcql/limit/"
service: "Cloud Scale"
--------------------------------------------------------------------------------


### LIMIT Clause


The LIMIT clause limits the number of data records that are displayed in the result set of a search query. It contains the following properties:

1. OFFSET: OFFSET defines the starting index of the result, i.e., the first record&#39;s position that will be displayed in the result.
2. VALUE: VALUE defines the number of records to be retrieved from the starting index, i.e., the OFFSET.

The LIMIT clause identifies the OFFSET index and then displays the number of records as specified in the VALUE from the OFFSET index. You can also just specify the value without specifying the offset, when the starting index is the first record.

The LIMIT clause is only used when a specific number of records is to be displayed. It is used towards the end of the query after all the other clauses and statements.

The basic syntax for using the LIMIT clause with a SELECT statement is:

SELECT column_name(s) FROM parent_table_name LIMIT OFFSET, VALUE

&lt;br /&gt;

Example:

To view a list of the movies from the _Movies_ table consisting of up to three records from the second starting index execute the following query:

SELECT * FROM Movies LIMIT 1,3 


It will generate the following output:

&lt;table class=&#34;content-table&#34;&gt;
&lt;thead&gt;
&lt;tr&gt;
&lt;th&gt;&lt;strong&gt;MovieID&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;MovieName&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;ShowDate&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;ShowTime&lt;/strong&gt;&lt;/th&gt;
&lt;th&gt;&lt;strong&gt;TheaterID&lt;/strong&gt;&lt;/th&gt;
&lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
&lt;tr&gt;
&lt;td&gt;2057&lt;/td&gt;
&lt;td&gt;Ant-Man and the Wasp&lt;/td&gt;
&lt;td&gt;2018-07-13&lt;/td&gt;
&lt;td&gt;14:20:00&lt;/td&gt;
&lt;td&gt;052&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;2058&lt;/td&gt;
&lt;td&gt;Hotel Transylvania 3: Summer Vacation&lt;/td&gt;
&lt;td&gt;2018-07-14&lt;/td&gt;
&lt;td&gt;17:00:00&lt;/td&gt;
&lt;td&gt;052&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;2059&lt;/td&gt;
&lt;td&gt;Skyscraper&lt;/td&gt;
&lt;td&gt;2018-07-14&lt;/td&gt;
&lt;td&gt;21:30:00&lt;/td&gt;
&lt;td&gt;053&lt;/td&gt;
&lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;

--------------------------------------------------------------------------------
title: "ZCQL Functions"
description: "ZCQL is Catalyst&#39;s own query language modelled after familiar query languages that you can use to query your app&#39;s database efficiently."
last_updated: "2026-07-02T09:34:09.985Z"
source: "https://docs.catalyst.zoho.com/en/cloud-scale/help/zcql/zcql-functions/"
service: "Cloud Scale"
--------------------------------------------------------------------------------


# ZCQL Functions

ZCQL supports some mathematical and analytical built-in functions that help you perform quick arithmetic operations on the data and manipulate the result set of a search query to meet your requirements. These functions are used in the SELECT statement for the columns that are generated in the output.

### MIN()

&lt;br /&gt; The MIN() function returns the minimum value of the selected column. You can use it to return the smallest value of a column that contains numerical data or the record that comes first in the alphabetical order.&lt;br /&gt; The basic syntax for using a MIN() function along with the SELECT statement is:&lt;br /&gt;


SELECT MIN(column_name) FROM base_table_name 

Example:

To view the least expensive movie from the _Pricing_ table, execute the following query:&lt;br /&gt;


SELECT MIN(Price) FROM Pricing 

This will generate the following output:

&lt;table class=&#34;content-table&#34;&gt;
&lt;thead&gt;
&lt;tr&gt;
&lt;th&gt;&lt;strong&gt;MIN(Price)&lt;/strong&gt;&lt;/th&gt;
&lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
&lt;tr&gt;
&lt;td&gt;7.44&lt;/td&gt;
&lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;

&lt;br /&gt;

### MAX()

The MAX() function returns the maximum value of the selected column. You can use it to return the largest value of a column that contains numerical data or the record that comes last in the alphabetical order.&lt;br /&gt; The basic syntax for using a MAX() function with the SELECT statement is:&lt;br /&gt;
&lt;br /&gt;

SELECT MAX(column_name) FROM base_table_name 

Example:&lt;br /&gt; 

To view the most expensive movie from the _Pricing_ table, execute the following query:&lt;br /&gt;

SELECT MAX(Price) FROM Pricing 


This will generate the following output:&lt;br /&gt;

&lt;table class=&#34;content-table&#34;&gt;
&lt;thead&gt;
&lt;tr&gt;
&lt;th&gt;&lt;strong&gt;MAX(Price)&lt;/strong&gt;&lt;/th&gt;
&lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
&lt;tr&gt;
&lt;td&gt;11.50&lt;/td&gt;
&lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;

&lt;br /&gt;


### COUNT() 

The COUNT() function returns the value for the number of rows in the records that are returned for a particular column in the output. The COUNT function is also used with the SELECT statement.
The basic syntax for using a COUNT() function with the SELECT statement is:

SELECT COUNT(column_name) FROM base_table_name

**Example:**

To view the number of theaters in New York City and Albany, from the _Theaters_ table, execute the following query:&lt;br /&gt;

SELECT COUNT(TheaterName) FROM Theaters
WHERE Location=&#39;New York City&#39; OR Location=&#39;Albany&#39;

This will generate the following output:&lt;br /&gt;

&lt;table class=&#34;content-table&#34;&gt;
&lt;thead&gt;
&lt;tr&gt;
&lt;th&gt;&lt;strong&gt;COUNT(TheaterName)&lt;/strong&gt;&lt;/th&gt;
&lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
&lt;tr&gt;
&lt;td&gt;2&lt;/td&gt;
&lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;

&lt;br /&gt;

### SUM()

The SUM() function calculates and returns the total sum of a numeric column&#39;s records. This can only be used for a column that contains numerical data. The SUM() function can also be used with the SELECT statement for a singular column.&lt;br /&gt; 

The basic syntax for using a SUM() function with the SELECT statement is:&lt;br /&gt;

SELECT SUM(column_name) FROM base_table_name

Example:&lt;br /&gt;

To view the sum total of the ticket charges for &#39;The First Purge&#39; and &#39;Hotel Transylvania 3: Summer Vacation&#39; from the _Pricing_ table, execute the following query:&lt;br /&gt;


SELECT SUM(Price) FROM Pricing
WHERE MovieID=&#39;2056&#39; OR MovieID=&#39;2058&#39;

This will generate the following output:&lt;br /&gt;

&lt;table class=&#34;content-table&#34;&gt;
&lt;thead&gt;
&lt;tr&gt;
&lt;th&gt;&lt;strong&gt;SUM(Price)&lt;/strong&gt;&lt;/th&gt;
&lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
&lt;tr&gt;
&lt;td&gt;20.7&lt;/td&gt;
&lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;

&lt;br /&gt;

### AVG()

The AVG() function calculates and returns the average value for a numeric column&#39;s records. This can only be used for a column that contains numerical data. The AVG() function is used along with the SELECT statement for a particular column alone.

The AVG () ZCQL function can be applied on the following data types:
- **Date**
- **DateTime**
- **Boolean**

Note: 

* This functionality is only available in ZCQL V2.

* From December 01st, 2024, all your current projects in all your Orgs present in the Development Environment will be automatically mapped to ZCQL V2 Parser.

* From April 01st, 2025, all the projects present in all Orgs that have already been mapped to ZCQL V2 Parser in Development Environment will be automatically mapped to ZCQL V2 Parser in the Production Environment, if and when production is enabled for the project.

The basic syntax for using a AVG() function with the SELECT statement is:&lt;br /&gt;


SELECT AVG(column_name) FROM base_table_name


Example:&lt;br /&gt; 

To view the average ticket price for the movies in the _Pricing_ table, execute the following query:&lt;br /&gt;

SELECT AVG(Price) As AverageTicketPrice FROM Pricing 

This will generate the following output:

&lt;table class=&#34;content-table&#34;&gt;
&lt;thead&gt;
&lt;tr&gt;
&lt;th&gt;&lt;strong&gt;AVG(Price)&lt;/strong&gt;&lt;/th&gt;
&lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
&lt;tr&gt;
&lt;td&gt;9.19&lt;/td&gt;
&lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;

&lt;br /&gt;

### DISTINCT

The DISTINCT statement returns only the distinct record values for a column. If there are duplicate values in a column, this statement will not return the duplicates. The DISTINCT statement is used along with the SELECT statement in a query.

The basic syntax for using a SELECT DISTINCT statement is:&lt;br /&gt;

SELECT DISTINCT column_name(s) FROM base_table_name

Example:&lt;br /&gt; 

To view the distinct theaters the movies are being screened at, execute the following query:&lt;br /&gt;

SELECT DISTINCT Theaters.TheaterName FROM Movies
INNER JOIN Theaters ON Movies.TheaterID=Theaters.TheaterID


This will generate the following output:&lt;br /&gt;

&lt;table class=&#34;content-table&#34;&gt;
&lt;thead&gt;
&lt;tr&gt;
&lt;th&gt;&lt;strong&gt;TheaterName&lt;/strong&gt;&lt;/th&gt;
&lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
&lt;tr&gt;
&lt;td&gt;The Express Cinemas&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;Cosmos Theater&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;FunTime Cinemas&lt;/td&gt;
&lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;

### Use Multiple ZCQL Functions

You can use multiple ZCQL functions on the same column in a single ZCQL query statement.

**Example Database**:

The employee details of Zylker Technologies are being maintained in the Data Store in the *Zylker_Employee_DB* table. The table contains the following columns and rows:

&lt;table class=&#34;content-table&#34;&gt;
	&lt;thead&gt;
		&lt;tr&gt;
			&lt;th class=&#34;w15p&#34;&gt;ID&lt;/th&gt;
			&lt;th class=&#34;w30p&#34;&gt;Name&lt;/th&gt;
			&lt;th class=&#34;w30p&#34;&gt;Department&lt;/th&gt;
            &lt;th class=&#34;w25p&#34;&gt;Salary&lt;/th&gt;
		&lt;/tr&gt;
	&lt;/thead&gt;
	&lt;tbody&gt;
		&lt;tr&gt;
			&lt;td&gt;ZT-001&lt;/td&gt;
			&lt;td&gt;Amelia Burrows&lt;/td&gt;
			&lt;td&gt;Product Management&lt;/td&gt;
            &lt;td&gt;15000&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;ZT-2001&lt;/td&gt;
			&lt;td&gt;Bruce Wayne&lt;/td&gt;
			&lt;td&gt;Sr. Management&lt;/td&gt;
            &lt;td&gt;85000&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;ZT-239&lt;/td&gt;
			&lt;td&gt;Clark Kane&lt;/td&gt;
			&lt;td&gt;Media Relations&lt;/td&gt;
            &lt;td&gt;4500&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;ZT-4289&lt;/td&gt;
			&lt;td&gt;Michelle Mascarenhas&lt;/td&gt;
			&lt;td&gt;Finance&lt;/td&gt;
            &lt;td&gt;89000&lt;/td&gt;
		&lt;/tr&gt;
	&lt;/tbody&gt;
&lt;/table&gt;

Next, we apply multiple ZCQL functions together in the query, as shown below:

SELECT MIN (Salary), MAX (Salary), COUNT (Salary), SUM (Salary), AVG (Salary) FROM Zylker_Employee_DB

&lt;table class=&#34;content-table&#34;&gt;
	&lt;thead&gt;
		&lt;tr&gt;
			&lt;th class=&#34;w20p&#34;&gt;MAX(Salary)&lt;/th&gt;
			&lt;th class=&#34;w20p&#34;&gt;SUM(Salary)&lt;/th&gt;
			&lt;th class=&#34;w20p&#34;&gt;MIN(Salary)&lt;/th&gt;
            &lt;th class=&#34;w20p&#34;&gt;AVG(Salary)&lt;/th&gt;
            &lt;th class=&#34;w20p&#34;&gt;COUNT(Salary)&lt;/th&gt;
		&lt;/tr&gt;
	&lt;/thead&gt;
	&lt;tbody&gt;
		&lt;tr&gt;
			&lt;td&gt;89000&lt;/td&gt;
			&lt;td&gt;193500&lt;/td&gt;
			&lt;td&gt;4500&lt;/td&gt;
            &lt;td&gt;48975&lt;/td&gt;
            &lt;td&gt;4&lt;/td&gt;
		&lt;/tr&gt;
	&lt;/tbody&gt;
&lt;/table&gt;

Note: 

* This functionality is only available in ZCQL V2.

* From December 01st, 2024, all your current projects in all your Orgs present in the Development Environment will be automatically mapped to ZCQL V2 Parser.

* From April 01st, 2025, all the projects present in all Orgs that have already been mapped to ZCQL V2 Parser in Development Environment will be automatically mapped to ZCQL V2 Parser in the Production Environment, if and when production is enabled for the project.

--------------------------------------------------------------------------------
title: "ZCQL V2 Syntax and Exceptions"
description: "ZCQL is Catalyst&#39;s own query language modelled after familiar query languages that you can use to query your app&#39;s database efficiently."
last_updated: "2026-07-02T09:34:09.985Z"
source: "https://docs.catalyst.zoho.com/en/cloud-scale/help/zcql/syntax-exceptions/"
service: "Cloud Scale"
--------------------------------------------------------------------------------


# ZCQL V2 Syntax and Exceptions

Catalyst has added several syntax upgrades and enhancements to help you write ZCQL queries more effectively. These new syntax upgrades will provide additional functionalities and enable you to perform data related operations in the Data Store with much ease.

Note:&lt;br /&gt;

* To use these feature enhancements, you will need to migrate to the V2 version. The syntax upgrades will not be applicable if you implement them while executing ZCQL commands in V1.

* From December 01st, 2024, all your current projects in all your Orgs present in the Development Environment will be automatically mapped to ZCQL V2 Parser.

* From April 01st, 2025, all the projects present in all Orgs that have already been mapped to ZCQL V2 Parser in Development Environment will be automatically mapped to ZCQL V2 Parser in the Production Environment, if and when production is enabled for the project.

The following exception and syntax nuances need to be kept in mind when you execute a ZCQL query:

1. The AVG () ZCQL function can be applied on the following data types:
    - **Date**
    - **DateTime**
    - **Boolean**

2. When you are indicating a value in your ZCQL statement, indicate the value in single quotes.&lt;br /&gt;
    For example, if you have to fetch a particular name from an employee database, you will write the command in the following manner:

SELECT Name FROM Employee_DB WHERE name = &#39;Amelia&#39;


3. If a column is of Boolean data type:
    - No string values are permitted.
    - Boolean data type will only support the following values:
        - FALSE
        - TRUE
        - NULL

4. If you are using an **Encrypted datatype**, then the following ZCQL functions cannot be used on that column:
    - AVG()
    - SUM()
    - MAX()
    - MIN()

5. Appropriate exceptions have been added when you use comparative operators like Less Than, Greater Than, Less Than or Equal, and Greater Than or Equal, on Encrypted Text, and Boolean data type. These exceptions are not applicable for Equal and Not Equal operators.

6. Subqueries are now supported in WHERE clause statements. You can find out more about them from this help document.

7. ORDER BY clause now supports the use of ZCQL functions.

8. In all columns where you use the ORDER BY clause, the ASC and DESC functionality can now be applied. You can also apply ASC and DESC for individual columns.

**Example Database**:&lt;br /&gt;
Consider the following database - **ZylkerEmployeeCompensation**

&lt;table class=&#34;content-table&#34;&gt;
	&lt;thead&gt;
		&lt;tr&gt;
			&lt;th class=&#34;w50p&#34;&gt;Name&lt;/th&gt;
			&lt;th class=&#34;w25p&#34;&gt;Salary&lt;/th&gt;
            &lt;th class=&#34;w25p&#34;&gt;Reimbursement&lt;/th&gt;
		&lt;/tr&gt;
	&lt;/thead&gt;
	&lt;tbody&gt;
		&lt;tr&gt;
			&lt;td&gt;Michelle Mascarenhas&lt;/td&gt;
			&lt;td&gt;90000&lt;/td&gt;
            &lt;td&gt;10000&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;Bruce Kyle&lt;/td&gt;
			&lt;td&gt;3000000&lt;/td&gt;
            &lt;td&gt;45000&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;Clark Kane&lt;/td&gt;
			&lt;td&gt;3300&lt;/td&gt;
            &lt;td&gt;1500&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;Judith Bridges&lt;/td&gt;
			&lt;td&gt;4700&lt;/td&gt;
            &lt;td&gt;300&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;Devon Dreymond&lt;/td&gt;
			&lt;td&gt;80000&lt;/td&gt;
            &lt;td&gt;2300&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;Ashley Kim&lt;/td&gt;
			&lt;td&gt;6000&lt;/td&gt;
            &lt;td&gt;200&lt;/td&gt;
		&lt;/tr&gt;
	&lt;/tbody&gt;
&lt;/table&gt;

Execute the following command to list the table

SELECT Salary, Reimbursement FROM ZylkerEmployeeCompensation ORDER BY Salary ASC, Reimbursement DESC

**Output:** &lt;br /&gt;

&lt;table class=&#34;content-table&#34;&gt;
	&lt;thead&gt;
		&lt;tr&gt;
			&lt;th class=&#34;w50p&#34;&gt;ZylkerEmployeeCompensation.Salary&lt;/th&gt;
            &lt;th class=&#34;w50p&#34;&gt;ZylkerEmployeeCompensation.Reimbursement&lt;/th&gt;
		&lt;/tr&gt;
	&lt;/thead&gt;
	&lt;tbody&gt;
		&lt;tr&gt;
			&lt;td&gt;3300&lt;/td&gt;
            &lt;td&gt;45000&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;4700&lt;/td&gt;
            &lt;td&gt;10000&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;6000&lt;/td&gt;
            &lt;td&gt;2300&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;80000&lt;/td&gt;
            &lt;td&gt;1500&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;90000&lt;/td&gt;
            &lt;td&gt;300&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;3000000&lt;/td&gt;
            &lt;td&gt;200&lt;/td&gt;
		&lt;/tr&gt;
	&lt;/tbody&gt;
&lt;/table&gt;

9. Appropriate exceptions will be triggered in the following cases:
    - If the permitted max/min value has been exceeded in **Integer** datatype.
    - If the character length is longer than the value set by you in **VarChar** datatype.
    - If the value is beyond the supported range in **BIGINT** datatype.

10. You can write **four** JOIN clauses in a single ZCQL statement. However, you can only write **one** JOIN condition for each join clause.

11. **Table Alias** functionality is now supported in ZCQL. You can now invoke alias functionality in ZCQL using the AS ZCQL command. Using this command you can refer to your table with other names.

**Example Database**:&lt;br /&gt;
Consider the following databases:

**Table 1: ZylkerEmployeeCompensation**

&lt;table class=&#34;content-table&#34;&gt;
	&lt;thead&gt;
		&lt;tr&gt;
			&lt;th class=&#34;w50p&#34;&gt;Name&lt;/th&gt;
			&lt;th class=&#34;w25p&#34;&gt;Salary&lt;/th&gt;
            &lt;th class=&#34;w25p&#34;&gt;Reimbursement&lt;/th&gt;
		&lt;/tr&gt;
	&lt;/thead&gt;
	&lt;tbody&gt;
		&lt;tr&gt;
			&lt;td&gt;Michelle Mascarenhas&lt;/td&gt;
			&lt;td&gt;90000&lt;/td&gt;
            &lt;td&gt;10000&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;Bruce Kyle&lt;/td&gt;
			&lt;td&gt;3000000&lt;/td&gt;
            &lt;td&gt;45000&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;Clark Kane&lt;/td&gt;
			&lt;td&gt;3300&lt;/td&gt;
            &lt;td&gt;1500&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;Judith Bridges&lt;/td&gt;
			&lt;td&gt;4700&lt;/td&gt;
            &lt;td&gt;300&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;Devon Dreymond&lt;/td&gt;
			&lt;td&gt;80000&lt;/td&gt;
            &lt;td&gt;2300&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;Ashley Kim&lt;/td&gt;
			&lt;td&gt;6000&lt;/td&gt;
            &lt;td&gt;200&lt;/td&gt;
		&lt;/tr&gt;
	&lt;/tbody&gt;
&lt;/table&gt;

**Table 2: ZylkerEmployeeRelation**

&lt;table class=&#34;content-table&#34;&gt;
	&lt;thead&gt;
		&lt;tr&gt;
			&lt;th class=&#34;w50p&#34;&gt;Manager&lt;/th&gt;
			&lt;th class=&#34;w50p&#34;&gt;Member&lt;/th&gt;
		&lt;/tr&gt;
	&lt;/thead&gt;
	&lt;tbody&gt;
		&lt;tr&gt;
			&lt;td&gt;Michelle Mascarenhas&lt;/td&gt;
			&lt;td&gt;Bruce Kyle&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;Michelle Mascarenhas&lt;/td&gt;
			&lt;td&gt;Clark Kane&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;Judith Bridges&lt;/td&gt;
			&lt;td&gt;Michelle Mascarenhas&lt;/td&gt;
		&lt;/tr&gt;
	&lt;/tbody&gt;
&lt;/table&gt;

Execute the following command to list the table

SELECT Managers.Name, Members.Name FROM ZylkerEmployeeCompensation AS Managers
INNER JOIN ZylkerEmployeeRelation AS asso ON Managers.ROWID = asso.Manager
INNER JOIN ZylkerEmployeeCompensation AS Members ON Members.ROWID = asso.Member

**Output:** &lt;br/&gt;

&lt;table class=&#34;content-table&#34;&gt;
	&lt;thead&gt;
		&lt;tr&gt;
			&lt;th class=&#34;w50p&#34;&gt;Manager.Name&lt;/th&gt;
			&lt;th class=&#34;w50p&#34;&gt;Member.Name&lt;/th&gt;
		&lt;/tr&gt;
	&lt;/thead&gt;
	&lt;tbody&gt;
		&lt;tr&gt;
			&lt;td&gt;Michelle Mascarenhas&lt;/td&gt;
			&lt;td&gt;Bruce Kyle&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;Michelle Mascarenhas&lt;/td&gt;
			&lt;td&gt;Clark Kane&lt;/td&gt;
		&lt;/tr&gt;
        &lt;tr&gt;
			&lt;td&gt;Judith Bridges&lt;/td&gt;
			&lt;td&gt;Michelle Mascarenhas&lt;/td&gt;
		&lt;/tr&gt;
	&lt;/tbody&gt;
&lt;/table&gt;

Note: The table Alias operation is only supported for **SELECT** statements.

12. You can check if you have a NULL value by using the **IS/IS NOT** operator.The **IS/IS NOT** operator support is only available for NULL values.

13. When writing GROUP BY with Binaryof() statements, the following ZCQL rules need to be remembered:
    - The Binaryof() functionality can only be used in GROUP BY statements.
    - Binaryof() can only be used on columns with VarChar or Text datatype.
    - When Binaryof() is used in a GROUP BY statement, the returned values are case-sensitive. For example, consider you have the values &#39;AMELIA&#39;, &#39;amelia&#39;, &#39;Burrows&#39;, and &#39;burrows&#39; in a column called Name, in a table called Zylker_EMP. If you use the following command:&lt;br /&gt;
    
Select Name from Zylker_EMP group by binaryof(Name)
    
The result could be any of the following:&lt;br /&gt;
- AMELIA
- amelia
- burrows
- Burrows

14. Column names can now contain numerical values. You can signify such column names in the query using a backtick  (**`**) punctuation. 

For example, a SELECT query on a table called Numbers with a column named 01 can be written in the following manner:

SELECT `01` FROM Numbers&lt;br /&gt;

### List of ZCQL Exceptions

The following is a list of common exceptions and example query statements that can trigger these exceptions. Ensure that you go through the list, and follow ZCQL syntax strictly to avoid triggering these exceptions.

&lt;table class=&#34;content-table&#34;&gt;
&lt;thead&gt;
  &lt;tr&gt;
    &lt;th class=&#34;w15p&#34;&gt;Datatype&lt;/th&gt;
    &lt;th class=&#34;w20p&#34;&gt;Case&lt;/th&gt;
    &lt;th class=&#34;w25p&#34;&gt;Sample ZCQL Query&lt;/th&gt;
    &lt;th class=&#34;w40p&#34;&gt;Triggered Exception&lt;/th&gt;
  &lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
  &lt;tr&gt;
    &lt;td rowspan=&#34;5&#34;&gt;&lt;strong&gt;Encrypted Text&lt;/strong&gt;&lt;/td&gt;
    &lt;td&gt;Certain operators are not supported&lt;/td&gt;
    &lt;td&gt;SELECT * FROM temp WHERE enc &gt; &#39;temsp&#39;&lt;/td&gt;
    &lt;td&gt;Operator &gt; is not supported for&lt;br /&gt;ENCRYPTED TEXT

The same exception applies, but the exception message will be altered accordingly if you use these operators **&lt;**, **&lt;=**, **&gt;=** in the ZCQL statement&lt;/td&gt;
  &lt;/tr&gt;
  &lt;tr&gt;
    &lt;td&gt;LIKE is not supported&lt;/td&gt;
    &lt;td&gt;SELECT  * FROM temp WHERE enc LIKE &#39;*temsp&#39;&lt;/td&gt;
    &lt;td&gt;Operator LIKE is not supported for&lt;br /&gt;ENCRYPTED TEXT

The same exception applies, but the exception message will be altered accordingly if you use **NOT LIKE** in the ZCQL statement&lt;/td&gt;
  &lt;/tr&gt;
  &lt;tr&gt;
    &lt;td&gt;BETWEEN is not supported&lt;/td&gt;
    &lt;td&gt;SELECT * FROM temp WHERE enc BETWEEN &#39;one&#39; AND &#39;ten&#39;&lt;/td&gt;
    &lt;td&gt;Operator BETWEEN is not supported for&lt;br /&gt;ENCRYPTED TEXT

The same exception applies, but the exception message will be altered accordingly if you use **NOT BETWEEN** in the ZCQL statement&lt;/td&gt;
  &lt;/tr&gt;
  &lt;tr&gt;
    &lt;td&gt;IN is not supported&lt;/td&gt;
    &lt;td&gt;SELECT * FROM temp WHERE enc IN (&#39;one&#39;,&#39;three&#39;)&lt;/td&gt;
    &lt;td&gt;Operator IN is not supported for&lt;br /&gt;ENCRYPTED TEXT
    
The same exception applies if you use **NOT IN** in your query, but the exception message will be altered accordingly&lt;/td&gt;
  &lt;/tr&gt;
    &lt;tr&gt;
    &lt;td&gt;ZCQL functions is not supported&lt;/td&gt;
    &lt;td&gt;SELECT AVG(enc) FROM temp&lt;/td&gt;
    &lt;td&gt;AVG() function is not supported for&lt;br /&gt;ENCRYPTED_TEXT
    
ZCQL Functions are not supported in **Encrypted Text**.&lt;/td&gt;
  &lt;/tr&gt;
  &lt;tr&gt;
    &lt;td rowspan=&#34;4&#34;&gt;&lt;strong&gt;Boolean&lt;/strong&gt;&lt;/td&gt;
    &lt;td&gt;Certain operators are not supported&lt;/td&gt;
    &lt;td&gt;SELECT * FROM temp WHERE bools &gt; FALSE&lt;/td&gt;
    &lt;td&gt;Operator &gt; is not supported for BOOLEAN

The same exception applies, but the exception message will be altered accordingly if you use these operators **&lt;**, **&lt;=**, **&gt;=**  in the ZCQL statement&lt;/td&gt;
  &lt;/tr&gt;
  &lt;tr&gt;
    &lt;td&gt;LIKE is not supported&lt;/td&gt;
    &lt;td&gt;SELECT * FROM temp WHERE bools LIKE FALSE&lt;/td&gt;
    &lt;td&gt;Operator LIKE is not supported for BOOLEAN

The same exception applies if you use **NOT LIKE** in your query, but the exception message will be altered accordingly&lt;/td&gt;
    &lt;/tr&gt;
    &lt;tr&gt;
        &lt;td&gt;BETWEEN is not supported&lt;/td&gt;
        &lt;td&gt;SELECT * FROM temp WHERE bools BETWEEN TRUE and FALSE&lt;/td&gt;
        &lt;td&gt;Operator BETWEEN is not supported for&lt;br /&gt;BOOLEAN

The same exception applies if you use **NOT BETWEEN** in your query, but the exception message will be altered accordingly&lt;/td&gt;
    &lt;/tr&gt;
    &lt;tr&gt;
        &lt;td&gt;IN is not supported&lt;/td&gt;
        &lt;td&gt;SELECT * FROM temp WHERE bools IN (TRUE, FALSE)&lt;/td&gt;
        &lt;td&gt;Operator IN is not supported for BOOLEAN

The same exception applies if you use **NOT IN** in your query, but the exception message will be altered accordingly&lt;/td&gt;
    &lt;/tr&gt;
    &lt;tr&gt;
        &lt;td rowspan=&#34;1&#34;&gt;&lt;strong&gt;VarChar&lt;/strong&gt;&lt;/td&gt;
        &lt;td&gt;Maximum length exceeded&lt;/td&gt;
        &lt;td&gt;INSERT INTO temp (Fishes) value (&#39;salmon&#39;)&lt;/td&gt;
        &lt;td&gt;&#39;salmon&#39; data too long for column &#39;Fishes&#39;

The column Fishes was created as a **VarChar** and the **MaxLength** was set as 5. In this statement, &#39;Salmon&#39; exceeds the **MaxLength**&lt;/td&gt;
    &lt;/tr&gt;
    &lt;tr&gt;
        &lt;td rowspan=&#34;1&#34;&gt;&lt;strong&gt;Integer&lt;/strong&gt;&lt;/td&gt;
        &lt;td&gt;Maximum value exceeded&lt;/td&gt;
        &lt;td&gt;INSERT INTO temp (numbers) VALUE (546895326908)&lt;/td&gt;
        &lt;td&gt;For column &#39;ints&#39; INT value should be between&lt;br /&gt;-9999999999 and 9999999999

The column numbers was created as **INT**. The value of **INT** datatype should be between -9999999999 and 9999999999&lt;/td&gt;
    &lt;/tr&gt;
    &lt;tr&gt;
        &lt;td rowspan=&#34;1&#34;&gt;&lt;strong&gt;Big Integer&lt;/strong&gt;&lt;/td&gt;
        &lt;td&gt;Maximum value exceeded&lt;/td&gt;
        &lt;td&gt;INSERT INTO temp (numbers) VALUE (92343432412351&lt;br /&gt;435123453245)&lt;/td&gt;
        &lt;td&gt;Given numeric value 92343432412351&lt;br /&gt;435123453 is too large

The column numbers was created as **BIGINT**. The value of **BIGINT** datatype should be between -9223372036854775808 and 9223372036854775807&lt;/td&gt;
    &lt;/tr&gt;
    &lt;tr&gt;
        &lt;td rowspan=&#34;1&#34;&gt;&lt;strong&gt;Text&lt;/strong&gt;&lt;/td&gt;
        &lt;td&gt;Value not enclosed in single quotes&lt;/td&gt;
        &lt;td&gt;SELECT * FROM temp WHERE name = one&lt;/td&gt;
        &lt;td&gt;Unknown Table temp or Unknown Column&lt;br /&gt;one in WHERE

The value one will be considered as column if it is not enclosed in quotes-&#39;one&#39;&lt;/td&gt;
    &lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;

--------------------------------------------------------------------------------
title: "The ZCQL Console"
description: "ZCQL is Catalyst&#39;s own query language modelled after familiar query languages that you can use to query your app&#39;s database efficiently."
last_updated: "2026-07-02T09:34:09.985Z"
source: "https://docs.catalyst.zoho.com/en/cloud-scale/help/zcql/zcql-console/"
service: "Cloud Scale"
--------------------------------------------------------------------------------


# The ZCQL Console

The **ZCQL Console** is an intuitive tool that allows you to execute your required ZCQL queries, perform data manipulation operations on data stored in the Data Store, and save your required ZCQL queries directly in the Catalyst console.

### Feature Highlights

&lt;br /&gt;

You can use the *ZCQL Console* provides you with the following offerings:

* When you type in a query, you are provided with a relevant and meaningful code completion suggestion that allows you to form your queries easily and quickly.
* Execute any query in the console, and you can directly view the complete output.
* Copy the query using the *copy button* and apply it to your code with ease.
* Save any of your required ZCQL queries and reuse it when required.
* Using the **ZCQL Explorer**, you can easily search for and reuse the required saved query, view column information of all the tables created in the project, and also reuse previously executed queries from the *History* section.

Note:

* By default, only 50 ZCQL queries can be saved in a single Catalyst project. If you have a higher requirement, you can contact the Catalyst Support team to increase this threshold.

* Only the latest 100 ZCQL queries will be logged in the History section of the ZCQL Explorer. However, there is no time limit on how long the query will be available in the History.

### Access the ZCQL Console

To access the ZCQL Console:&lt;span&gt;&lt;/span&gt;

1. Navigate to the **Data Store** component present under the *STORAGE* section of the CloudScale service.
    &lt;br /&gt;

Note: You need to create a table in the Data Store to be access the ZCQL Console.

2. Click the **ZCQL Console** tab.
    &lt;br /&gt;

You can type your query in this console and perform the required operations.


### The ZCQL Explorer

The *ZCQL Explorer* is an expandable and collapsible feature of the ZCQL console. It contains the following sections:

* **Schema**: Schema contains information about the table that includes the list of columns present in the table, if the value for the columns is mandatory, and the datatype of the data that will be stored in these columns.
    &lt;br /&gt;

* **Saved Queries**: This section will contain a list of all the queries you have saved using the **Save Query** button. You can search for your required query using its name and reuse it.
    &lt;br /&gt;

Note: By default, only 50 ZCQL queries can be saved in a single Catalyst project. If you have a higher requirement, you can contact the Catalyst Support team to increase this threshold.

* **History**: The *History* section will contain the complete list of the **latest 100 queries** that have been executed in the console.
    &lt;br /&gt;
If you wish to save a query from the *History* section, click the **save-icon** next to the required query and follow the steps listed in this [section](#SaveaZCQLQuery).

Note: Only the latest 100 ZCQL queries will be present in the History section. However, there is no time limit on how long the query can be stored in History.


### Execute a ZCQL Query

To execute a ZCQL query in the ZCQL Console:

1. Enter your ZCQL query in the console.
    &lt;br /&gt;

2. Click the **Execute Query** button.
    &lt;br /&gt;

You will be able to view the output directly in the console.

The query will be executed and logged in the *History* section present in the **ZCQL Explorer**.

By default, you will be viewing the output in *Table View*. You also have the option to view the output as a JSON by clicking the **View** drop-down, and selecting the **JSON View** option.

&lt;br /&gt;

You also have the option to copy this JSON and use it as required.


### Save a ZCQL Query

In the ZCQL Console, you can execute your required queries and save them. Saving your queries allows you to retrieve them easily and use them whenever they are required instead of manually inputting them for each session.

Note: By default, only 50 ZCQL queries can be saved in a single Catalyst project. If you have a higher requirement, you can contact the Catalyst Support team to increase this threshold.

To save a ZCQL query:

1. Enter your required query, and click the **Save Query** button.
    &lt;br /&gt;

2. In the pop-up, go through the *Query Preview* section and provide a **Query Name** to refer your query by and click **Save**.
    &lt;br /&gt;


Your query will be saved.

You can view and manage your queries from the *ZCQL Explorer* section, under the **Saved Queries** tab.

&lt;br /&gt;

You can click the *Console* button to print the query into your console.

&lt;br /&gt;

You can also further edit this query and execute it as needed or save it under a different query name by repeating the steps mentioned above.


### Delete a Saved Query

To delete a saved query:

1. Click the **delete-icon** present next to the required query in the **Saved Queries** section of the *ZCQL Explorer*.
    &lt;br /&gt;

2. Click **Yes, Proceed** on the confirmation pop-up to delete the required query.
    &lt;br /&gt;

The query will be deleted.


### Using ZCQL V2 in Function Code

To use **ZCQL V2** code in your function, you will need to set an environment variable for it in the following manner:

1. Navigate to *Serverless* &gt; **Functions**.
&lt;br /&gt;
2. Click the function that contains your ZCQL V2 code.
3. Click the **Configuration** tab, then click **Create Variable** under *Environmental Variables*.
&lt;br /&gt;
4. Enter the following values in the respective fields:&lt;br /&gt;**Key**: ZOHO_CATALYST_ZCQL_PARSER&lt;br /&gt;**Development Value**: V2
&lt;br /&gt;
5. Click **Save**.
&lt;br /&gt;

You will now be able to use ZCQL V2 in your function code.

Note: 

* You do not have to reference the environment variable anywhere in your code. Once you have configured it in the console, you can use ZCQL V2 in your function code.

* From December 01st, 2024, all your current projects in all your Orgs present in the Development Environment will be automatically mapped to ZCQL V2 Parser.

* From April 01st, 2025, all the projects present in all Orgs that have already been mapped to ZCQL V2 Parser in Development Environment will be automatically mapped to ZCQL V2 Parser in the Production Environment, if and when production is enabled for the project.

---

## API Reference â€” ZCQL

--------------------------------------------------------------------------------
title: "Execute ZCQL Query"
description: "This API enables you to execute a ZCQL query to retrieve, insert, update, or delete data from the tables in the Data Store."
last_updated: "2026-07-02T09:34:09.987Z"
source: "https://docs.catalyst.zoho.com/en/api/code-reference/cloud-scale/zcql/execute-zcql-query/"
service: "Cloud Scale"
--------------------------------------------------------------------------------






# ZCQL

ZCQL is Catalyst&#39;s own query language that enables you to perform data retrieval, insertion, updating, and deletion operations on the tables in the Catalyst Data Store.

You can execute a variety of DML queries using ZCQL to obtain or manipulate data, and use various clauses and statements such as the SQL Join clauses, Groupby and OrderBy statements, and built-in SQL functions.

# Execute a ZCQL Query

### Description

This API enables you to execute a ZCQL query to retrieve, insert, update, or delete data from the tables in the Data Store. You can execute this API by passing a ZCQL query in the JSON request, as shown in the sample requests.

 Note: The API request format is the same for all ZCQL query execution operations.


### Request Details

#### Request URL
&lt;p&gt;{api-domain}/baas/v1/project/{project_id}/query&lt;/p&gt;

The DC-specific domain to access Catalyst API

The unique ID of the project


#### Request Headers
 **Authorization:** Zoho-oauthtoken {oauth_token} &lt;br&gt;
**Content-Type:** application/json


**Optional Headers** &lt;br&gt;
 **CATALYST-ORG:** {org_id}

 **Environment:** Development


#### Scope

ZohoCatalyst.zcql.CREATE



 Note: This operation can also be executed with Catalyst user authentication permissions using Catalyst SDKs. Refer to the [Catalyst API Prerequisites section](/en/api/introduction/overview-and-prerequisites/#prerequisites) for details.


#### Request JSON Properties

 The ZCQL query to be executed   


### Response Details

Data Retrieval Operations: The API returns the records that were fetched as a result of the query execution as the response.

Data Insertion and Updating Operations: The API returns the records that were inserted or updated through the query as the response.

Data Deletion Operations: The API returns the deleted row count.






curl -X POST \
  https://api.catalyst.zoho.com/baas/v1/project/4000000006007/query \
  -H &#34;Authorization: Zoho-oauthtoken 1000.910*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*16.2f*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*57&#34; \
  -H &#34;Content-Type: application/json&#34; \
  -d &#39;{
	&#34;query&#34;:&#34;SELECT EmpID, EmpName, Department, Address from EmpDetails ORDER BY EmpID ASC LIMIT 1000,5&#34;
       }&#39;



    {
    &#34;status&#34;: &#34;success&#34;,
    &#34;data&#34;: [
        {
            &#34;EmpDetails&#34;: {
                &#34;CREATORID&#34;: &#34;3376000000002003&#34;,
                &#34;MODIFIEDTIME&#34;: &#34;2023-06-05 15:09:33:881&#34;,
                &#34;CREATEDTIME&#34;: &#34;2023-06-05 15:09:33:881&#34;,
                &#34;ROWID&#34;: &#34;3376000001924975&#34;,
                &#34;EmpID&#34;: &#34;1001&#34;,
                &#34;EmpName&#34;: &#34;Allison Powell&#34;,
                &#34;Department&#34;:&#34;Marketing&#34;,
                &#34;Address&#34;: &#34;13, Winter Avenue, Philadelphia, PY&#34;
            }
        },
        {
            &#34;EmpDetails&#34;: {
                &#34;CREATORID&#34;: &#34;3376000000002003&#34;,
                &#34;MODIFIEDTIME&#34;: &#34;2023-06-05 15:09:33:881&#34;,
                &#34;CREATEDTIME&#34;: &#34;2023-06-05 15:09:33:881&#34;,
                &#34;ROWID&#34;: &#34;3376000001927682&#34;,
                &#34;EmpID&#34;: &#34;1002&#34;,
                &#34;EmpName&#34;: &#34;James Cortez&#34;,
                &#34;Department&#34;:&#34;HR&#34;,
                &#34;Address&#34;: &#34;25, Blossom Street, Austin, TX&#34;
            }
        },
        {
            &#34;EmpDetails&#34;: {
                &#34;CREATORID&#34;: &#34;3376000000002003&#34;,
                &#34;MODIFIEDTIME&#34;: &#34;2023-06-02 21:04:11:111&#34;,
                &#34;CREATEDTIME&#34;: &#34;2023-06-02 15:05:21:001&#34;,
                &#34;ROWID&#34;: &#34;3376000001224112&#34;,
                &#34;EmpID&#34;: &#34;1003&#34;,
                &#34;EmpName&#34;: &#34;Han Chan&#34;,
                &#34;Department&#34;:&#34;Sales&#34;,
                &#34;Address&#34;: &#34;112, St.Patrick&#39;s Road, Louisville, KY&#34;
            }
        },
        {
            &#34;EmpDetails&#34;: {
                &#34;CREATORID&#34;: &#34;337600000003111&#34;,
                &#34;MODIFIEDTIME&#34;: &#34;2023-06-02 21:04:11:111&#34;,
                &#34;CREATEDTIME&#34;: &#34;2023-06-02 15:05:21:001&#34;,
                &#34;ROWID&#34;: &#34;3376000001242012&#34;,
                &#34;EmpID&#34;: &#34;1004&#34;,
                &#34;EmpName&#34;: &#34;Rubella Miguel&#34;,
                &#34;Department&#34;:&#34;Accounts&#34;,
                &#34;Address&#34;: &#34;333, Marine Bay, Salt Lake City, UT&#34;
            }
        },
        {
            &#34;EmpDetails&#34;: {
                &#34;CREATORID&#34;: &#34;3376000000115254&#34;,
                &#34;MODIFIEDTIME&#34;: &#34;2023-04-12 21:04:10:521&#34;,
                &#34;CREATEDTIME&#34;: &#34;2023-06-11 15:05:02:541&#34;,
                &#34;ROWID&#34;: &#34;3376000001241341&#34;,
                &#34;EmpID&#34;: &#34;1005&#34;,
                &#34;EmpName&#34;: &#34;Ronwick Boseman&#34;,
                &#34;Department&#34;:&#34;Support&#34;,
                &#34;Address&#34;: &#34;61, Gringott&#39;s Avenue, Herfordshire, CO&#34;
            }
        }
    ]
}


curl -X POST \
  https://api.catalyst.zoho.com/baas/v1/project/4000000006007/query \
  -H &#34;Authorization: Zoho-oauthtoken 1000.910*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*16.2f*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*57 \
  -H &#34;Content-Type: application/json&#34; \
  -d &#39;{
	&#34;query&#34;:&#34;INSERT INTO EmpDetails VALUES (1007,&#39;Randy Marsh&#39;,&#39;Sales&#39;,&#39;42, Tenth Street, Jacksonville, FL&#39;, &#39;14 MAR 2017&#39;)&#34;
       }&#39;



    {
    &#34;status&#34;: &#34;success&#34;,
    &#34;data&#34;: [
      {
        &#34;EmpDetails&#34;: {
          &#34;CREATORID&#34;: &#34;3813000000002003&#34;,
          &#34;EmpID&#34;: &#34;1007&#34;,
          &#34;EmpName&#34;: &#34;Randy Marsh&#34;,
          &#34;Department&#34;:&#34;Sales&#34;,
          &#34;Address&#34;: &#34;42, Tenth Street, Jacksonville, FL&#34;,
          &#34;DOJ&#34;: &#34;14 MAR 2017&#34;,
          &#34;MODIFIEDTIME&#34;: &#34;2021-08-04 09:10:14:752&#34;,
          &#34;CREATEDTIME&#34;: &#34;2021-08-04 09:10:14:752&#34;,
          &#34;ROWID&#34;: &#34;3813000000214001&#34;
        }
      }
    ]
}


curl -X POST \
  https://api.catalyst.zoho.com/baas/v1/project/4000000006007/query \
  -H &#34;Authorization: Zoho-oauthtoken 1000.910*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*16.2f*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*57 \
  -H &#34;Content-Type: application/json&#34; \
  -d &#39;{
	&#34;query&#34;:&#34;UPDATE EmpDetails SET Department=&#39;Operations&#39; WHERE EmpID=1007&#34;
       }&#39;



    {
    &#34;status&#34;: &#34;success&#34;,
    &#34;data&#34;: [
      {
        &#34;EmpDetails&#34;: {
          &#34;CREATORID&#34;: &#34;3813000000002003&#34;,
          &#34;EmpID&#34;: &#34;1007&#34;,
          &#34;EmpName&#34;: &#34;Randy Marsh&#34;,
          &#34;Department&#34;:&#34;Operations&#34;,
          &#34;Address&#34;: &#34;42, Tenth Street, Jacksonville, FL&#34;,
          &#34;DOJ&#34;: &#34;14 MAR 2017&#34;,
          &#34;MODIFIEDTIME&#34;: &#34;2021-08-04 09:11:54:318&#34;,
          &#34;CREATEDTIME&#34;: &#34;2021-08-04 09:10:14:752&#34;,
          &#34;ROWID&#34;: &#34;3813000000214001&#34;
        }
      }
    ]
}


curl -X POST \
  https://api.catalyst.zoho.com/baas/v1/project/4000000006007/query \
  -H &#34;Authorization: Zoho-oauthtoken 1000.910*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*16.2f*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*57 \
  -H &#34;Content-Type: application/json&#34; \
  -d &#39;{
	&#34;query&#34;:&#34;DELETE FROM EmpDetails WHERE EmpID=1007&#34;
       }&#39;



    {
    &#34;status&#34;: &#34;success&#34;,
    &#34;data&#34;: [
      {
        &#34;EmpDetails&#34;: {
          &#34;DELETED_ROWS_COUNT&#34;: 1
        }
      }
    ]
  }


   

Execute ZCQL Query- Java SDK&lt;/br&gt;&lt;/br&gt;
Execute ZCQL Query- Node.js SDK&lt;/br&gt;&lt;/br&gt;
Execute ZCQL Query- Python SDK&lt;/br&gt;&lt;/br&gt;
Execute ZCQL Query- Web SDK








---

## SDK â€” Android â€” ZCQL

--------------------------------------------------------------------------------
title: "Execute ZCQL Query"
description: "ZCQL is Catalyst&#39;s own query language that enables you to perform data creation, retrieval, and modification operations in the Data Store."
last_updated: "2026-07-02T09:34:10.010Z"
source: "https://docs.catalyst.zoho.com/en/sdk/android/v2/cloud-scale/zcql/execute-zcql-query/"
service: "Cloud Scale"
related:
- Data Store (/en/cloud-scale/help/data-store/introduction)
- ZCQL (/en/cloud-scale/help/zcql/introduction/)
- Execute ZCQL - API (/en/api/code-reference/cloud-scale/zcql/execute-zcql-query/#ExecuteZCQLQuery)

--------------------------------------------------------------------------------


# ZCQL

ZCQL is Catalyst&#39;s own query language that enables you to perform data creation, retrieval, and modification operations in the Data Store. It supports queries with built-in functions, SQL Join clauses, and other statements and conditions.

### Execute a ZCQL Query

Before you execute a ZCQL query to fetch the required data set, you must construct the query to pass it to the **execute()** method. You can learn about the ZCQL syntax from the ZCQL help page.

You must pass an instance of **ZCatalystSelectQuery** to the execute() method, as shown in the code syntax of a ZCQL query execution below.

The &amp;lt;DATA_STORE_INSTANCE&amp;gt; used here is the instance defined in the Data Store Instance page.

ZCatalystApp.getInstance().getDataStoreInstance().execute(
    selectQuery: ZCatalystSelectQuery,
    success: (List&amp;lt;Map&amp;lt;String, Map&amp;lt;String, Any?&amp;gt;&amp;gt;&amp;gt;) â†’ Unit,
    failure: ((ZCatalystException) â†’ Unit)?
): ZCatalystRequest&amp;lt;ZCatalystResponse&amp;lt;List&amp;lt;Map&amp;lt;String, Any?&amp;gt;&amp;gt;&amp;gt;&amp;gt;&amp;gt;?


**Parameters**:

* **selectQuery**: The instance of the type ZCatalystSelectQuery to be passed

You can create a selectQuery instance for ZCatalystSelectQuery for the statements supported by ZCQL, in the following way:

ZCatalystSelectQuery.Builder()
   .select(columns: Set&amp;lt;Column&amp;gt;): ZCatalystSelectQuery.Builder
   .selectAll(): ZCatalystSelectQuery.Builder
   .where(column: String, comparator: ZCatalystUtil.Comparator, value: String): ZCatalystSelectQuery.Builder
   .from(tableName: String): ZCatalystSelectQuery.Builder
   .and(column: String, comparator: ZCatalystUtil.Comparator, value: String): ZCatalystSelectQuery.Builder
   .groupBy(columns: Set&amp;lt;Column&amp;gt;): ZCatalystSelectQuery.Builder
   .orderBy(columns: Set&amp;lt;Column&amp;gt;, sortOrder: ZCatalystUtil.SortOrder): ZCatalystSelectQuery.Builder
   .innerJoin(tableName: String): ZCatalystSelectQuery.Builder
   .leftJoin(tableName: String): ZCatalystSelectQuery.Builder
   .on(joinColumn1: String, comparator: ZCatalystUtil.Comparator, joinColumn2: String): ZCatalystSelectQuery.Builder
   .or(column: String, comparator: ZCatalystUtil.Comparator, value: String): ZCatalystSelectQuery.Builder
   .limit(offset: Int, value: Int?): ZCatalystSelectQuery.Builder
   .build(): ZCatalystSelectQuery


A sample code snippet of a ZCQL query execution is shown below:

val query = ZCatalystSelectQuery.Builder()
    .selectAll()
    .from(&#34;EmployeeDetails&#34;) //Replace this with your table name
    .where(&#34;Location&#34;, ZCatalystUtil.Comparator.EQUAL_TO, &#34;Austin&#34;)
    .and(&#34;Department&#34;, ZCatalystUtil.Comparator.EQUAL_TO, &#34;Marketing&#34;)
    .or(&#34;isActive&#34;, ZCatalystUtil.Comparator.EQUAL_TO, &#34;true&#34;)
    .limit(5)
    .build()

ZCatalystApp.getInstance().getDataStoreInstance().execute(query,
    {
        println(&#34;Query executed successfully. $it&#34;)
    },
    {
        exception -&gt; println(&#34;Exception occured $exception&#34;)
    })


---

## SDK â€” Flutter â€” ZCQL

--------------------------------------------------------------------------------
title: "Execute ZCQL Query"
description: "ZCQL is Catalyst&#39;s own query language that enables you to perform data creation, retrieval, and modification operations in the Data Store."
last_updated: "2026-07-02T09:34:10.010Z"
source: "https://docs.catalyst.zoho.com/en/sdk/flutter/v2/cloud-scale/zcql/execute-zcql-query/"
service: "Cloud Scale"
related:
- Data Store (/en/cloud-scale/help/data-store/introduction)
- ZCQL (/en/cloud-scale/help/zcql/introduction/)
- Execute ZCQL - API (/en/api/code-reference/cloud-scale/zcql/execute-zcql-query/#ExecuteZCQLQuery)

--------------------------------------------------------------------------------


# ZCQL

ZCQL is Catalyst&#39;s own query language that enables you to perform data creation, retrieval, and modification operations in the Data Store. It supports queries with built-in functions, SQL Join clauses, and other statements and conditions.

### Execute a ZCQL Query

Flutter enables you to perform data retrieval operations using ZCQL. Before you execute a ZCQL query to fetch the required data set, you must construct the query to pass it to the **getData()** method. You can learn about the ZCQL syntax from the ZCQL help page.

You must pass an instance of **ZCatalystSelectQuery** to the getData() method, as shown in the code syntax of a ZCQL query execution below.

The &amp;lt;DATA_STORE_INSTANCE&amp;gt; used here is the instance defined in the Data Store Instance page.

Future&lt;(APIResponse, List&amp;lt;dynamic&amp;gt;?)&gt; ZCatalystApp.getInstance().getDataStoreInstance().getData(
ZCatalystSelectQuery selectQuery)

**Parameters**:

* **selectQuery**: The instance of the type ZCatalystSelectQuery to be passed

You can create a selectQuery instance for ZCatalystSelectQuery for the statements supported by ZCQL, in the following way:

ZCatalystSelectQuery.Builder()
   .select(columns: Set&amp;lt;Column&amp;gt;): ZCatalystSelectQuery.Builder
   .selectAll(): ZCatalystSelectQuery.Builder
   .where(column: String, comparator: ZCatalystUtil.Comparator,        	  
   value: String): ZCatalystSelectQuery.Builder
   .from(tableName: String): ZCatalystSelectQuery.Builder
   .and(column: String, comparator: ZCatalystUtil.Comparator, 		  
   value: String): ZCatalystSelectQuery.Builder
   .groupBy(columns: Set&amp;lt;Column&amp;gt;): ZCatalystSelectQuery.Builder
   .orderBy(columns: Set&amp;lt;Column&amp;gt;, sortOrder: 					  
   ZCatalystUtil.SortOrder): ZCatalystSelectQuery.Builder
   .innerJoin(tableName: String): ZCatalystSelectQuery.Builder
   .leftJoin(tableName: String): ZCatalystSelectQuery.Builder
   .on(joinColumn1: String, comparator: ZCatalystUtil.Comparator, 	  
   joinColumn2: String): ZCatalystSelectQuery.Builder
   .or(column: String, comparator: ZCatalystUtil.Comparator, value:String): ZCatalystSelectQuery.Builder
   .limit(offset: Int, value: Int?): ZCatalystSelectQuery.Builder
   .build(): ZCatalystSelectQuery

A sample code snippet of a ZCQL query execution is shown below:

try {
      ZCQLColumn column1 = ZCQLColumn(&#39;Title&#39;);
      ZCQLColumn column2 = ZCQLColumn(&#39;Category&#39;);
      Set&amp;lt;ZCQLColumn&amp;gt; columns = Set();
      columns.add(column1);
      columns.add(column2);
      ZCatalystSelectQuery query = ZCatalystQueryBuilder()
          .select(columns)
          .from(&#39;Projects&#39;)
          .where(&#39;Category&#39;, Comparator.EQUAL_TO, &#39;Official&#39;)
          .build();
      var (_, result) = await app.getDataStoreInstance().getData(query);
      print(&#34;Query Result: $result&#34;);
 } on ZCatalystException catch (ex) {
      print(ex.toString());
 }

---

## SDK â€” iOS â€” ZCQL

--------------------------------------------------------------------------------
title: "Execute ZCQL Query"
description: "ZCQL is Catalyst&#39;s own query language that enables you to perform data creation, retrieval, and modification operations in the Data Store."
last_updated: "2026-07-02T09:34:10.011Z"
source: "https://docs.catalyst.zoho.com/en/sdk/ios/v2/cloud-scale/zcql/execute-zcql-query/"
service: "Cloud Scale"
related:
- Data Store (/en/cloud-scale/help/data-store/introduction)
- ZCQL (/en/cloud-scale/help/zcql/introduction/)
- Execute ZCQL - API (/en/api/code-reference/cloud-scale/zcql/execute-zcql-query/#ExecuteZCQLQuery)

--------------------------------------------------------------------------------


# ZCQL

ZCQL is Catalyst&#39;s own query language that enables you to perform data retrieval operations in the Data Store.  It supports SELECT queries with built-in functions, SQL Join clauses, and other statements and conditions.

### Execute a ZCQL Query

Before you execute a ZCQL query to fetch the required data set, you must construct the query to pass it to the **execute()** method. You can learn about the ZCQL syntax from the ZCQL help page.

You must pass an instance of **ZCatalystSelectQuery** to the execute() method, as shown in the code syntax of a ZCQL query execution below.

&amp;lt;ZCatalystApp&amp;gt;.execute( query : ZCatalystSelectQuery, completion: @escaping (Result&amp;lt;[ [ String : Any ] ], ZCatalystError&amp;gt;) -&gt; Void)

**Parameters**:

* **query**: The instance of the type ZCatalystSelectQuery to be passed
* **completion**: If the query execution call is successful, the completion block will return with the records that match the criteria of the query. Else, it will return an error.

You can create a query instance for the ZCatalystSelectQuery for the statements supported by ZCQL, in the following way:

ZCatalystSelectQuery.Builder()
   .select(columns: Set&amp;lt;Column&amp;gt;) -&gt; ZCatalystSelectQuery.Builder
   .selectAll() -&gt; ZCatalystSelectQuery.Builder
   .where(column: String, comparator: Comparator,  value: String) -&gt; ZCatalystSelectQuery.Builder
   .from(tableName: String)  -&gt; ZCatalystSelectQuery.Builder
   .and(column: String, comparator: Comparator,  value: String) -&gt; ZCatalystSelectQuery.Builder
   .groupBy(columns: Set&amp;lt;Column&amp;gt;) -&gt; ZCatalystSelectQuery.Builder
   .orderBy(columns: Set&amp;lt;Column&amp;gt;, sortOrder: SortOrder) -&gt; ZCatalystSelectQuery.Builder
   .innerJoin(tableName: String) -&gt; ZCatalystSelectQuery.Builder
   .leftJoin(tableName: String) -&gt; ZCatalystSelectQuery.Builder
   .on(joinColumn1: String, comparator: Comparator, joinColumn2: String) -&gt; ZCatalystSelectQuery.Builder
   .or(column: String, comparator: Comparator, value:  String) -&gt; ZCatalystSelectQuery.Builder
   .limit(offset: Int, value: Int? = nil) -&gt; ZCatalystSelectQuery.Builder
  .build() -&gt; ZCatalystSelectQuery


A sample code snippet of a ZCQL query execution is shown below:

func testExecuteZCQL(){
	  var builder = ZCatalystSelectQuery.Builder()
	  var query = builder.selectAll().from( tableName : &#34;Bio-data&#34; ).build() //replace your table name here
			ZCatalystApp.shared.getDataStoreInstance(tableIdentifier: &#34;1096000000002071&#34;).execute( query : query) { ( result ) in
						switch result{
	  case .success( let response ) :
   	print(&#34;Response : \( response )&#34;)
  	case .error( let error ) :
   print( &#34;Error occurred &amp;gt;&amp;gt;&amp;gt; \( error )&#34; )
  	}
 	}
	}


---

## SDK â€” Java â€” ZCQL

--------------------------------------------------------------------------------
title: "Execute ZCQL queries"
description: "This page describes the method to execute ZCQL queries on a table in the Data Store in your Java application with sample code snippets."
last_updated: "2026-07-02T09:34:10.011Z"
source: "https://docs.catalyst.zoho.com/en/sdk/java/v1/cloud-scale/zcql/execute-zcql-query/"
service: "Cloud Scale"
related:
- Execute ZCQL queries - API (/en/api/code-reference/cloud-scale/zcql/execute-zcql-query/#ExecuteZCQLQuery)
- Execute ZCQL queries (/en/cloud-scale/help/zcql/introduction)
- Data Store (/en/cloud-scale/help/data-store/introduction)

--------------------------------------------------------------------------------


# ZCQL

ZCQL is Catalyst&#39;s own query language that enables
you to perform data retrieval, insertion, updating, and deletion operations on the tables in the
Catalyst Data Store. You can execute a
variety of DML queries using ZCQL to obtain or manipulate data, and use various clauses and statements such as the SQL
Join clauses, Groupby and OrderBy statements, and built-in SQL functions.

### Execute ZCQL Queries

Catalyst also provides an **OLAP database**, in addition to the primary Data Store that is suited for analytical data retrieval queries. You can choose to execute simple transactional queries on the primary Data Store, and complex analytical queries that involve ZCQL functions on the OLAP database. 

The queries that you execute on the primary Data Store can include SELECT, INSERT, UPDATE, or DELETE statements. The queries that you execute on the OLAP database must only include the SELECT statement, as direct write operations on it are not allowed.
You must construct a ZCQL query and pass it to the executeQuery() method for execution as shown in the sample code below. 

The executeQuery() method supports these three parameters:

* The String variable containing the constructed query statement
* isV2?: A boolean value (true or false) indicating if it is a ZCQL v2 query
* isOLAP?: A boolean value (true or false) indicating if the query needs to be executed on the OLAP database

executeQuery(query: string, isV2?: boolean , isOLAP?:boolean) 

A sample SELECT query is shown below. The response will contain the records you fetch using the SELECT query, or the response generated for the other operations.



#### Sample Code Snippet 
&lt;br&gt;
import com.zc.component.object.ZCRowObject; 
import com.zc.component.zcql.ZCQL;

//Construct the query to be executed 
String query = &#34;SELECT * from empDetails limit 10&#34;;
//Get the ZCQL instance and execute query using the query string
ArrayList &lt;ZCRowObject&gt; rowList = ZCQL.getInstance().executeQuery(query, true , false)
 


---

## SDK â€” Node JS â€” ZCQL

--------------------------------------------------------------------------------
title: "Get ZCQL Instance"
description: "This page describes the method to execute ZCQL queries on a table in the Data Store in your NodeJS application with sample code snippets."
last_updated: "2026-07-02T09:34:10.012Z"
source: "https://docs.catalyst.zoho.com/en/sdk/nodejs/v2/cloud-scale/zcql/get-component-instance/"
service: "Cloud Scale"
related:
- ZCQL (/en/cloud-scale/help/zcql/introduction)
- Data Store (/en/cloud-scale/help/data-store/introduction)

--------------------------------------------------------------------------------


# ZCQL

ZCQL is Catalyst&#39;s own query language that enables
you to perform data retrieval, insertion, updating, and deletion operations on the tables in the
Catalyst Data Store. You can execute a
variety of DML queries using ZCQL to obtain or manipulate data, and use various clauses and statements such as the SQL
Join clauses, Groupby and OrderBy statements, and built-in SQL functions.

Catalyst also provides an **OLAP database**, in addition to the primary Data Store that is suited for analytical data retrieval queries. You can choose to execute simple transactional queries on the primary Data Store, and complex analytical queries that involve ZCQL functions on the OLAP database. 


### Get Component Instance

You must first create a component instance for ZCQL. The zcql instance can be created as shown below.

//Get a ZCQL instance 
let zcql = app.zcql(); 


--------------------------------------------------------------------------------
title: "Execute Query"
description: "This page describes the method to execute ZCQL queries on a table in the Data Store in your NodeJS application with sample code snippets."
last_updated: "2026-07-02T09:34:10.012Z"
source: "https://docs.catalyst.zoho.com/en/sdk/nodejs/v2/cloud-scale/zcql/execute-zcql-query/"
service: "Cloud Scale"
related:
- Execute query - API (/en/api/code-reference/cloud-scale/zcql/execute-zcql-query/#ExecuteZCQLQuery)
- ZCQL (/en/cloud-scale/help/zcql/introduction)
- Data Store (/en/cloud-scale/help/data-store/introduction)

--------------------------------------------------------------------------------


# Execute Query

zcql refers to the component instance defined here. This will return a promise which will be resolved to an object. The content key will contain the
array of row objects.

### Construct and Execute the Query on the Primary Data Store

For the ZCQL queries to be executed on the primary Data Store, you can construct the query and pass it to the executeZCQLQuery() method as shown below. These queries can include SELECT, INSERT, UPDATE, or DELETE statements.

A sample INSERT query is shown below:

//Construct the query to execute 
let query = &#39;INSERT into ShipmentData (productID, productName, region) VALUES (3782, A4 Reams, India)&#39;;
let result = await zcql.executeZCQLQuery(query); 


&lt;br&gt;

### Construct and Execute the Query on the OLAP Database

The queries that you execute on the OLAP database must only include the SELECT statement, as direct write operations on it are not allowed. You can construct the query object and pass it to the executeOLAPQuery() method. A sample analytical SELECT query is shown below.

//Construct the query to execute 
let query = &#39;SELECT SUM(price) FROM ShipmentData&#39;;
let result = await zcql.executeOLAPQuery(query); 

 


---

## SDK â€” Python â€” ZCQL

--------------------------------------------------------------------------------
title: "Get ZCQL Instance"
description: "This page describes the method to execute ZCQL queries on a table in the Data Store in your Python application with sample code snippets."
last_updated: "2026-07-02T09:34:10.012Z"
source: "https://docs.catalyst.zoho.com/en/sdk/python/v1/cloud-scale/zcql/get-component-instance/"
service: "Cloud Scale"
related:
- ZCQL Help (/en/cloud-scale/help/zcql/introduction)
- Data Store Help (/en/cloud-scale/help/data-store/introduction)

--------------------------------------------------------------------------------


# ZCQL

Catalyst Cloud Scale ZCQL is Catalyst&#39;s own query language that enables you to perform data retrieval, insertion, updation, and deletion operations on the tables in the Catalyst Cloud Scale Data Store. You can execute a variety of DML queries using ZCQL to obtain or manipulate data, and use various clauses and statements such as the SQL Join clauses, Groupby and OrderBy statements, and built-in SQL functions.

Catalyst also provides an **OLAP database**, in addition to the primary Data Store that is suited for analytical data retrieval queries. You can choose to execute simple transactional queries on the primary Data Store, and complex analytical queries that involve ZCQL functions on the OLAP database. 

### Get a Component Instance

A component instance is an object that can be used to access the predefined configurations specific to a particular component. This process will not fire a server-side call.

The app reference used in the code below is the Python object returned as a response during SDK initialization. Also note that this instance will be used in multiple scenarios while performing retrieval, insertion, updating, or deleting operations in the Catalyst Data Store.

#Get a ZCQL component instance
zcql_service = app.zcql()
 


--------------------------------------------------------------------------------
title: "Execute Query"
description: "This page describes the method to execute ZCQL queries on a table in the Data Store in your Python application with sample code snippets."
last_updated: "2026-07-02T09:34:10.012Z"
source: "https://docs.catalyst.zoho.com/en/sdk/python/v1/cloud-scale/zcql/execute-zcql-query/"
service: "Cloud Scale"
related:
- Execute query - API (/en/api/code-reference/cloud-scale/zcql/execute-zcql-query/#ExecuteZCQLQuery)
- ZCQL Help (/en/cloud-scale/help/zcql/introduction)
- Data Store Help (/en/cloud-scale/help/data-store/introduction)
- SDK Scopes (/en/sdk/python/v1/sdk-scopes)

--------------------------------------------------------------------------------


# Execute Query

The zcql_service reference used in the code snippet below is the component instance created earlier. Based on the query object being passed, the response returns a row object or an array of row objects.

### Construct and Execute the Query on the Primary Data Store

For the ZCQL queries to be executed on the primary Data Store, you can construct the query object and pass it to the execute_query() method as shown below. These queries can include SELECT, INSERT, UPDATE, or DELETE statements.

A sample INSERT query is shown below:

#Construct the ZCQL query
query = &#39;INSERT into ShipmentData (productID, productName, region) VALUES (3782, A4 Reams, India)&#39;
result = zcql_service.execute_query(query)


### Construct and Execute the Query on the OLAP Database

The queries that you execute on the OLAP database must only include the SELECT statement, as direct write operations on it are not allowed. You can construct the query object and pass it to the execute_olap_query() method. A sample analytical SELECT query is shown below.

//Construct the query to execute 
query = &#39;SELECT SUM(price) FROM ShipmentData&#39;;
result = zcql_service.execute_olap_query(query);


**Parameters Used**

&lt;table class=&#34;content-table&#34;&gt;
	&lt;thead&gt;
		&lt;tr&gt;
			&lt;th class=&#34;w20p&#34;&gt;Parameter Name&lt;/th&gt;
			&lt;th class=&#34;w20p&#34;&gt;Data Type&lt;/th&gt;
      &lt;th class=&#34;w60p&#34;&gt;Definition&lt;/th&gt;
		&lt;/tr&gt;
	&lt;/thead&gt;
	&lt;tbody&gt;
		&lt;tr&gt;
			&lt;td&gt;query&lt;/td&gt;
			&lt;td&gt;String&lt;/td&gt;
			&lt;td&gt;A Mandatory parameter. Will store the query to be executed.&lt;/td&gt;
		&lt;/tr&gt;
	&lt;/tbody&gt;
&lt;/table&gt;

Info : Refer to the SDK Scopes table to determine the required permission level for performing the above operation. 


---

## SDK â€” Web â€” ZCQL

--------------------------------------------------------------------------------
title: "Get a Component Instance"
description: "ZCQL is Catalyst&#39;s own query language that enables you to perform data retrieval operations in the Data Store."
last_updated: "2026-07-02T09:34:10.013Z"
source: "https://docs.catalyst.zoho.com/en/sdk/web/v4/cloud-scale/zcql/get-component-instance/"
service: "Cloud Scale"
related:
- Data Store (/en/cloud-scale/help/data-store/introduction)
- ZCQL (/en/cloud-scale/help/zcql/introduction/)
- Execute ZCQL - API (/en/api/code-reference/cloud-scale/zcql/execute-zcql-query/#ExecuteZCQLQuery)

--------------------------------------------------------------------------------


# ZCQL

ZCQL is Catalyst&#39;s own query language that enables you to perform data retrieval, insertion, updating, and deletion operations on the tables in the  Catalyst Data Store. You can execute a variety of DML queries using ZCQL to obtain or manipulate data, and use various clauses and statements such as the SQL Join clauses, Groupby and OrderBy statements, and built-in SQL functions.

### Get a Component Instance

The zcql reference can be created as shown below. This does not a fire server-side call.

//Get a ZCQL instance
var zcql = catalyst.ZCatalystQL;


--------------------------------------------------------------------------------
title: "Execute ZCQL Query"
description: "ZCQL is Catalyst&#39;s own query language that enables you to perform data retrieval operations in the Data Store."
last_updated: "2026-07-02T09:34:10.013Z"
source: "https://docs.catalyst.zoho.com/en/sdk/web/v4/cloud-scale/zcql/execute-zcql-query/"
service: "Cloud Scale"
related:
- Data Store (/en/cloud-scale/help/data-store/introduction)
- ZCQL (/en/cloud-scale/help/zcql/introduction/)
- Execute ZCQL - API (/en/api/code-reference/cloud-scale/zcql/execute-zcql-query/#ExecuteZCQLQuery)

--------------------------------------------------------------------------------


# Execute ZCQL Query

### Construct the Query

You must construct a ZCQL query on the required data set before you execute it. A sample SELECT query is shown below:

//Create a query to execute
var query = &#39;SELECT * FROM ShipmentData&#39;;


### Execute the Query

The query object created in the step above is passed to the executeZCQLQuery() method. The zcql reference used here is the component instance defined earlier.

This will return a promise which will be resolved to an object. The content key will contain the array of row objects.

//Execute the query by passing it
var zcql = catalyst.ZCatalystQL;
 var zcqlPromise  = zcql.executeQuery(query);
zcqlPromise
        .then((response) =&gt; {
            console.log(response.content);
        })
        .catch((err) =&gt; {
            console.log(err);
        });


Note: To use ZCQL V2 commands in your code, use the Catalyst methods listed here with the values listed below to set the appropriate environment variable:&lt;br /&gt;

* Key: ZOHO_CATALYST_ZCQL_PARSER

* Value: V2

A sample response that you will receive is shown below. The response is the same for both versions of Web SDK.

[
  {
    AlienCity: {
      CREATORID: &#34;2136000000006003&#34;,
      MODIFIEDTIME: &#34;2021-08-13 13:49:19:475&#34;,
      CREATEDTIME: &#34;2021-08-13 13:49:19:475&#34;,
      CityName: &#34;Dallas&#34;,
      ROWID: &#34;2136000000008508&#34;
    }
  },
  {
    AlienCity: {
      CREATORID: &#34;2136000000006003&#34;,
      MODIFIEDTIME: &#34;2021-08-16 15:55:32:969&#34;,
      CREATEDTIME: &#34;2021-08-16 15:55:32:969&#34;,
      CityName: &#34;Houston&#34;,
      ROWID: &#34;2136000000011002&#34;
    }
  },
  {
    AlienCity: {
      CREATORID: &#34;2136000000006003&#34;,
      MODIFIEDTIME: &#34;2021-08-16 17:03:01:507&#34;,
      CREATEDTIME: &#34;2021-08-16 16:29:10:499&#34;,
      CityName: &#34;Austin&#34;,
      ROWID: &#34;2136000000011011&#34;
    }
  }
]