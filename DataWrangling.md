<font size='7' color='steelblue'>Wrangling Tacos in San Diego</font>
<font size='5'>Udacity: Data Wrangling with MongoDB</font>
<font size='4' color='grey'>Lamont Girton</font>
<font size='4' color='grey'>October 23, 2015</font>
---

### Table of Contents
[TOC]

### Overview
[San Diego](https://en.wikipedia.org/wiki/San_Diego) is the 2nd largest city in Southern California and home to over 1.38 million residents and is where I have resided for last 38 years.  Located in the southwest region of California and bordering Mexico, San Diego has been heavily influenced by it's neighboring country and has some of the best tacos short of Mexico itself.  This paper will explore an extract of crowd-sourced geographical information on San Diego County from [OpenStreetMap](http://openstreetmap.org).  More specifically, we'll parse the XML map file using _Python_ and wrangle the data into MongoDB for reporting and analysis, and most importantly insights into places to grab an authentic taco.

The OSM file was obtained via [Map Zen Metro Extracts](https://mapzen.com/data/metro-extracts/):
https://s3.amazonaws.com/metro-extracts.mapzen.com/san-diego-tijuana_mexico.osm.bz2

All of the code and content for this project is accessible in my [DataWrangling](https://github.com/lgirton/DataWrangling) respository on [Github](https://github.com).

### Problems Encountered

* Over-abbreviated street type names
* Inconsisent postal codes
* Incorrect postal codes
* Inconsistent city names
* Missing city names
* Inconsistent cuisines and amenity tags
* Multiple cuisine and amenity tags
* Missing cuisine identifiers

#### Over-abbreviated street type names
During the analysis of the OSM file, we encountered an inconsistency of street type abbreviations (e.g 'Av.' instead of Avenue).  Below is a subroutine that is a part of the [_parse\_osm.py_][parse_osm] script. This function will parse the last word of the `addr:street` tag element value and match that to a reverse-lookup dictionary in _R\_STREET\_TYPE\_MAP_ (using regular expressions)of the common abbreviation and transform to it's proper name.

```python
def parse_street(key, val, entity):
    suffix = RE_STRT.search(val, re.IGNORECASE)
    if suffix:
        suffix = suffix.group()
        if suffix in R_STREET_TYPE_MAP.keys():
            val = val.replace(suffix, R_STREET_TYPE_MAP[suffix])
    entity['address'][key] = val
...

```

#### Inconsisent postal codes
#### Incorrect postal codes
#### Inconsistent city names
#### Missing city names
#### Inconsistent cuisines and amenity tags
#### Multiple cuisine and amenity tags
#### Missing cuisine identifiers

### Data Overview

#### File Sizes

```
san-diego-county.osm ........ 516.38 MB
san-diego-county.osm.json ... 583.01 MB 
```

#### Number of documents
```
> db.sandiego.find().count()
1645464
```

#### Number of nodes
```
> db.sandiego.find({entity_type: 'node'}).count()
1526148
```

#### Number of ways
```
> db.sandiego.find({entity_type: 'way'}).count()
119316
```

#### Number of unique contributors
```
> db.sandiego.distinct('created.user').length
1144
```

#### Top 5 contributors
```
> db.sandiego.aggregate([
...   {$group: {_id: '$created.user', count: {$sum: 1}}},
...   {$sort: {count: -1}},
...   {$limit: 5}
... ])

{ "_id" : "Adam Geitgey", "count" : 680725 }
{ "_id" : "Sat", "count" : 203592 }
{ "_id" : "woodpeck_fixbot", "count" : 193483 }
{ "_id" : "Zian Choy", "count" : 27019 }
{ "_id" : "chdr", "count" : 24300 }
```

### Additional Ideas
```
> db.sandiego.aggregate([
...   {$match: {cuisine: {$exists: 1}, amenity: 'fast_food'}},
...   {$group: {_id: '$cuisine', count: {$sum: 1}}},
...   {$sort: {count: -1}}
... ])

{ "_id" : [ "burger" ], "count" : 238 }
{ "_id" : [ "sandwich" ], "count" : 114 }
{ "_id" : [ "mexican" ], "count" : 102 }
{ "_id" : [ "pizza" ], "count" : 55 }
{ "_id" : [ "chicken" ], "count" : 25 }

```

### Conclusion

[parse_osm]: https://github.com/lgirton/DataWrangling/blob/master/parse_osm.py