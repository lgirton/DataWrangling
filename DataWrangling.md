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
Below are 5 areas of problem encountered during the processing of the OSM file:

* Over-abbreviated street type names
* Inconsistent postal codes
* Incorrect postal codes
* Inconsistent city names
* Cleaning cuisines and amenity tags


#### Over-abbreviated street type names
During the analysis of the OSM file, we encountered an inconsistency of street type abbreviations (e.g 'Av.' instead of Avenue).  Below is a subroutine that is a part of the [_parse\_osm.py_][parse_osm] script. This function will parse the last word of the `addr:street` tag element value and match that to a reverse-lookup dictionary in _R\_STREET\_TYPE\_MAP_ (using regular expressions)of the common abbreviation and transform to it's proper name.

```python

RE_STRT = re.compile(r'\b\S+\.?$')

def parse_street(key, val, entity):
    suffix = RE_STRT.search(val, re.IGNORECASE)
    if suffix:
        suffix = suffix.group()
        if suffix in R_STREET_TYPE_MAP.keys():
            val = val.replace(suffix, R_STREET_TYPE_MAP[suffix])
    entity['address'][key] = val
...

```

#### Inconsistent postal codes
In auditing the dataset, we also encounted inconsistent postal code entries.  For example, some postal codes could have the state code prefix the 5 digit zip and in other cases, postal codes were in the [ZIP+4](https://en.wikipedia.org/wiki/ZIP_code#ZIP.2B4) format.  This was addressed in the _pre-processing_ [python][parse_osm] script to match the first 5 digits from the tag attribute value with the `addr:postcode` key.  Below is a snippet from the code that matches the pattern and adds it to the `address` entry in the JSON dictionary.

```python
RE_POST = re.compile(r'\d{5}')

# Parse postcode (e.g. <node><tag k='addr:postcode' v='92121')
def parse_postcode(key, val, entity):
    match = RE_POST.search(val)
    if match:
        val = match.group()
    entity['address'][key] = val
```

#### Incorrect postal codes
A list of the valid San Diego County zip codes can be found [here](http://www.sdcourt.ca.gov/pls/portal/docs/PAGE/SDCOURT/GENERALINFORMATION/FORMS/ADMINFORMS/ADM254.PDF).  From this list, we can see that all San Diego postal codes follow the format of 9XXXX.  After loading these into MongoDB, I audited to determine if any of the zip codes are are outside of this pattern.

```
> db.sandiego.find({'address.postcode': {$exists: 1}, 'address.postcode': /^[0-8]/}).count()
41
```

From query above we see that there are 41 cases where the postal codes don't match the 9XXXX pattern.  Below are the top 5 out of range zip codes and cities along with their respective count.

```
> db.sandiego.aggregate([
... {$match: {'address.postcode': /^[0-8]/}},
... {$group: {_id: {
... 'postcode': '$address.postcode', 
... 'city': '$address.city'
... }, count: {$sum: 1}}},
... {$sort: {count: -1}},
... {$limit: 5}
... ])
{ "_id" : { "postcode" : "22710", "city" : "Playas de Rosarito" }, "count" : 5 }
{ "_id" : { "postcode" : "22626", "city" : "Tijuana" }, "count" : 5 }
{ "_id" : { "postcode" : "22290" }, "count" : 4 }
{ "_id" : { "postcode" : "22207" }, "count" : 3 }
{ "_id" : { "postcode" : "22000", "city" : "Tijuana" }, "count" : 2 }
```

From the output, the zip codes belong to cities in Mexico, primarily Tijuana which is a border town to San Diego.  This is primarily due to how the extract was obtained, as the bounding box for the metro extract included parts of Mexico.  Some options here would be to find the lowest latitude of nodes and ways in San Diego and exclude documents that were lower (south) than this.  I've decided to leave the records intacts.

#### Inconsistent city names
Below is an excerpt from the San Diego OSM extract:

```xml
<node id="3611791159" lat="32.7007996" lon="-117.0971943" version="1" timestamp="2015-06-
23T01:10:37Z" changeset="32151159" uid="2944514" user="adahman">
        <tag k="name" v="Ocean View Growing Grounds"/>
        <tag k="shop" v="garden_centre"/>
        <tag k="website" v="https://www.facebook.com/OceanViewCommunityGarden/timeline"/>
        <tag k="addr:city" v="San Diego, CA"/>
        <tag k="addr:street" v="Ocean View Boulevard"/>
```
The _tag_ element with `addr:city` as the key has a value of 'San Diego, CA' and unnecessarily qualifies the city name with the state.  The following snippet from the [parse_osm.py][parse_osm] removes any trailing state information and also reformats the string in _proper_ case (e.g. 'SAN DIEGO', becomes 'San Diego') using the python _title_ string function.

```python
RE_RTRM = re.compile(r'^[^,]*')

# Parse city, will strip city name of following state, 
# e.g. 'CHICAGO, IL' => 'Chicago'
def parse_city(key, val, entity):
    entity['address'][key] = RE_RTRM.search(val).group().title()

```

#### Cleaning cuisines and amenity tags
The _cuisine_ and _amenity_ tags were initially stored as strings during the transformation process.  But upon inspection of some of the values, this element was best represented as an _array_, because nodes could be classified as having multiple cuisine and amenity types (e.g. 'mexican;irish,steak_house')

The following subroutine addresses these issues:

```python
RE_WORD = re.compile(r'\W+')

# Parse amenity and cuisine tags.  Allows for multiple values
# in a list. e.g. amenity='mexican,Mexican;Irish' => ['mexican', 'irish']
# Also makes them lowercase and strips any leading and trailing whitespace
def parse_amenity_cuisine(key, val, entity):
    # There can be multiple amenity and cuisine designations
    # Split and add unique items as list
    items = list(set(RE_WORD.split(val.lower().strip())))

    # Replace leading underscores
    items = [RE_UNDR.sub('', item) for item in items]

    entity[key] = items
```

The above code converts the string to lowercase and then tokenizes using _non-words_ as the delimiter.  Finally, there were instances were there were leading underscore characters and these were stripped.  

### Data Overview
Below are some statistics on the extract and processed information.

#### File Sizes

```
# RAW OSM Extract
san-diego-county.osm ........ 516.38 MB

# Transformed JSON output
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

[repo]: https://github.com/lgirton/DataWrangling
[parse_osm]: https://github.com/lgirton/DataWrangling/blob/master/parse_osm.py
[data]: https://www.udacity.com/course/viewer#!/c-ud032-nd