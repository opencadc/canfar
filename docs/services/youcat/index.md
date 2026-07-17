# YouCat

YouCat is a database service that lets users create and share tables. It is separate from the CANFAR Science Platform.

## Overview

YouCat (=Your Catalog) allows users to upload tables. The tables are then acessible via the [Table Access Protocol (TAP)](https://ws-uv.canfar.net/youcat). YouCat was built after several requests from users who needed to publish a database, but did not have the resources to publish it at their home institutions. Note that YouCat is not optimal for a database use cases requiring frequent updates, modifications or deletions. The permissions can be set so that the database access is restricted to the owner, or shared with a group, or made world-public.

TAP is an IVOA (International Virtual Observatory Alliance) protocol. While loading the table is best done with the CADC python client, querying can be down with the CADC client, but also a large number of other tools, e.g. [topcat](https://www.star.bris.ac.uk/~mbt/topcat/). The TAP handle for youcat is currently: https://ws-uv.canfar.net/youcat

## Creating a table

### Step 0.

#### Get write permission for a schema
If you don't already have a schema, send a short e-mail to support@canfar.net indicating describing the project and size estimates. Turn around is typically 1-2 working days. If there is an existing schema, but you are not the owner, the owner will have to give you write permission.

#### Install the cadc-tap client
This can be installed with pip
```bash
pip install cadctap cadcutils
```
#### Get a certificate
This is used to authenticate and authorise the puts
```bash
cadc-get-cert --user <CADCusername> 
```

### Step 1. Create the table

The table columns are specified with a file in VOTable format,
with a command like:
```bash
cadc-tap create -f VOTable <tablename> <tabledefinition>
```
eg.
```bash
cadc-tap create -f VOTable unions.gaapcatalog gaap.vot
```
The VOTable can have a few rows of content, but they won't be read at creation
You can get a sample VOTable by querying an existing table, for example:
```
cadc-tap query -f votable 'select top 0 * from pgm.ps_gaia_merged' > sample.vot
```
which will create a VOTable with the header, but no rows.

Each column is specified with a <FIELD>, specifying:

- name (mandatory)
- datatype (mandatory)
- description (optional, but highly recommended)
- UCD and utype (optional, but recommended)
- The descriptions typically can end up as tool tips on a webpage, and let users know what they are getting.

The ucds let tools like topcat do some clever things.

so for example:
```xml
      <FIELD name="raPS" datatype="double" ucd="pos.eq.ra" unit="deg" utype="stc:AstroCoords.Position3D.Value3.C1">
        <DESCRIPTION>Right ascension from Pan-STARRS</DESCRIPTION>
      </FIELD>
```

Optional: positional searches can be optimized by addin position column, which combines RA and Dec
```
      <FIELD name="pos" datatype="double" arraysize="2" xtype="point">
        <DESCRIPTION>Position</DESCRIPTION>
      </FIELD>
```
this column can be indexed simultaneously in RA,Dec and make positional queries MUCH faster

Also, there should be one column that uniquely identifies an object
across the whole catalog. In addition to making the user's life a lot
easier, it will make loading the table in the next step easier.

Once you've got the VOTable sorted out, you can create the table with
the cadc-tap create command above. If you make a mistake, you can
delete the table with cadc-tap delete. Unfortunately, there is (currently)
no way to alter the table once created.

### Step 2. Create indexes

Indexes are a way of accelerating queries. Take the example of a table
with a million rows and you are only interested in a 10 of them, where
the value of column_A is in a narrow if there is no index, the
database has to look at every row, look at the value of column_A, and
skip if it isn't in that range. This is called a "table scan" and it
is to be avoided. If column_A is indexed, then the database will jump
to the rows of the table where column_A is in the correct range. The
other use of an index is to avoid having duplicate rows. A have a
unique index on a column mean that you can't accidentally insert the
same row twice into a table.  In astronomy catalogs, tables will have
unique indexes on a column with the source_ID or source_name, or
something similar.


For any columns you think might be searched on regularly do:
```bash
cadc-tap index <tablename> <column>
```
e.g.:
```
cadc-tap index unions.ngvsnewtable principleRA
cadc-tap index unions.ngvsnewtable principleDec
```
for any columns that you want to be unique do:
```bash
cadc-tap index -U <tablename> <column>
```
e.g.:
```bash
cadc-tap index -U unions.ngvsnewtable Official_name
```

For large tables, it is much, much, much easier to have a unique index
for object_id (or something). For large catalogs, it will probably be a long
integer. You definitely want to index RA, Dec and pos to make those queries
faster.

This step is optional and might also be done after step 3. Indexing
after loading the table makes insertions faster, but having a unique index
**before** loading the table avoids the risk of duplicate rows.

### Step 3: Load the table

While table creation is done only using VOTable format, table
loading is done using FITS, .csv (comma separated values) and
.tsv (tab separated values). Convert your table to one of those
formats.

You should probably break the table up into smaller chunks of about
10000 rows. Smaller than that, the overhead of each call to the service
will slow things down. Larger than that, the possibility of an error
taking out a large transfer becomes a challenge.

Tables are loaded with commands like:
```bash
cadc-tap load <schemaname.tablename> <filename>
```
e.g.:
```
cadc-tap load unions.ngvsnewtable newtable.tsv
```
Note the schema and table names both need to be specified. 

Do that for each file. Note that if you have created a unique index,
and you try to reload the same row a second time, it will fail. This
avoids duplicate rows. Remember there is no way to edit an existing
table.

The biggest challenge here is that, as with anything involving the
network, there is a chance each a load operation may fail. For small
tables, this is not an issue. For large tables with many load
operations, there is the chance of failure.  So make sure you keep a
log of each load operation. Then you can use the unique index you
created to keep track of what was succesfully loaded and load the
difference.

### Step 4: Check the table

Run a few queries:
```bash
cadc-tap query <tablename> 'query'
```
e.g.
```bash
cadc-tap query 'select top 10 * from unions.ngvsnewtable'
```
(this should show you the same columns as you think should be in the table)
```bash
cadc-tap query 'select count(*) from unions.ngvsnewtable'
```
(this should give you the same number of rows you think should be in the table)
queries on the indexed columns should also show a suitable
amount of acceleration

## Permissions and sharing

A newly created table will not generally be readable by others. The general syntax is:
```bash
cadc-tap permission <mode> <tablename> [<groups ...>]
```
For example, to grant read permission to a group, do
```bash
cadc-tap permission g+r unions.ngvsnewtable unions-read-group
```
To make a table readable by everybody do:
```bash
cadc-tap permission o+r unions.ngvsnewtable
```

## API reference

While the cadc-tap client should provide enough functionality, you can also read the [YouCAT API documentation](https://ws-uv.canfar.net/youcat/) for the OpenAPI specification.
