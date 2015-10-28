<font size='7' color='steelblue'>Wrangling Tacos in San Diego</font>

### Table of Contents
[TOC]

### Overview
[San Diego County](https://en.wikipedia.org/wiki/San_Diego_County,_California) is the 2nd most populated county in Southern California and home to an estimated 3.1 million residents and in which I'm glad to call home.  Located in the southwest region of California and bordering Mexico, San Diego'has been heavily influenced by it's neighboring country and has some of the best tacos short of Mexico itself.  This paper will explore an extract of crowd-sourced geographical information on San Diego County from [OpenStreetMap](http://openstreetmap.org).  More specifically, we'll parse the XML map file using _Python_ and wrangle the data into MongoDB for reporting and analysis, and most importantly insights into places to grab an authentic taco.

The OSM file was obtained via Overpass API:
http://overpass-api.de/api/map?bbox=-117.9163,32.4599,-115.7780,33.5757

### Problems Encountered

* Inconsisent naming of streets
* Inconsisent postal codes
* Incorrect postal codes
* Inconsistent cuisines and amenity tags
* Multiple cuisine and amenity tags

#### Inconsisent naming of streets
#### Inconsisent postal codes
#### Incorrect postal codes
#### Inconsistent cuisines and amenity tags
#### Multiple cuisine and amenity tags

### Data Overview

#### File Sizes

```
san-diego-county.osm ........ 1.39 GB
san-diego-county.osm.json ... 1.61 GB 
```

#### Number of documents
```
> db.sd.find().count()
5500546
```

#### Number of nodes
```
> db.sd.find({entity_type: 'node'}).count()
5127000
```

#### Number of ways
```
> db.sd.find({entity_type: 'way'}).count()
373546
```

#### Number of unique contributors
```
> db.sd.distinct('created.user').length
2494
```

#### Top 5 contributors
```
> db.sd.aggregate([
... {$group: {_id: '$created.user', count: {$sum: 1}}},
... {$sort: {count: -1}},
... {$limit: 5}
... ])
{ "_id" : "Adam Geitgey", "count" : 859643 }
{ "_id" : "The Temecula Mapper", "count" : 504591 }
{ "_id" : "woodpeck_fixbot", "count" : 494059 }
{ "_id" : "AM909", "count" : 343277 }
{ "_id" : "Sat", "count" : 262743 }
```

### Additional Ideas
```
> db.sandiego.aggregate([
... {$match: {cuisine: {$exists: 1}, amenity: 'fast_food'}},
... {$group: {_id: '$cuisine', count: {$sum: 1}}},
... {$sort: {count: -1}}
... ])

{ "_id" : [ "burger" ], "count" : 238 }
{ "_id" : [ "sandwich" ], "count" : 115 }
{ "_id" : [ "mexican" ], "count" : 102 }
{ "_id" : [ "pizza" ], "count" : 54 }
{ "_id" : [ "chicken" ], "count" : 25 }
{ "_id" : [ "bagel" ], "count" : 18 }
{ "_id" : [ "ice_cream" ], "count" : 9 }

```

### Conclusion