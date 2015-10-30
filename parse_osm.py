import xml.etree.cElementTree as ET
import sys
import codecs
import re
import json
from collections import defaultdict

# List of tags that should be put into a nested 'created' dictionary.
CREATED = ['version','changeset','timestamp','user','uid']

# List of tags that should be put into a nested 'pos' dictionary.
POS = ['lat','lon']

# Compiled regular expressions used to match and wrangle data for faster processing.
RE_ADDR = re.compile(r'(?<=addr\:).*')
RE_WORD = re.compile(r'\W+')
RE_UNDR = re.compile(r'^_')
RE_RTRM = re.compile(r'^[^,]*')
RE_POST = re.compile(r'\d{5}')
RE_STRT = re.compile(r'\b\S+\.?$')

# Proper street type name to common abbreviations map
STREET_TYPE_MAP = {
	"Avenue": ('Av', 'Av.', 'Ave', 'Ave.'),
	"Boulevard": ('Blvd', "Blvd.", 'Boul', 'Boulv'),
	"Court": ('Ct', 'Ct.'),
	"Drive": ('Dr', 'Dr.'),
	'Lane': ('Ln', 'Ln.'),
	'Parkway': ('Parkwy','Pkway','Pkwy', 'Pkwy.')
}

# Placeholder for reverse lookup street type map
R_STREET_TYPE_MAP = {}

# Condition wrapper
def is_city(key):
	return key == 'city'

# Parse city, will strip city name of following state, 
# e.g. 'Chicago, IL' => 'Chicago'
def parse_city(key, val, entity):
	entity['address'][key] = RE_RTRM.search(val).group().title()

# Condition wrapper
def is_street(key):
	return key == 'street'

# Parse street (e.g. <node><tag k='addr:street'), will replace
# common street abbreviations to full name, e.g Ave => Avenue
def parse_street(key, val, entity):
	suffix = RE_STRT.search(val, re.IGNORECASE)
	if suffix:
		suffix = suffix.group()
		if suffix in R_STREET_TYPE_MAP.keys():
			val = val.replace(suffix, R_STREET_TYPE_MAP[suffix])
	entity['address'][key] = val

# condition wrapper
def is_postcode(key):
	return key == 'postcode'

# Parse postcode (e.g. <node><tag k='addr:postcode' v='92121')
def parse_postcode(key, val, entity):
	match = RE_POST.search(val)
	if match:
		val = match.group()
	entity['address'][key] = val

# Determine if key is of addr subtype 
def is_address(key):
	return key.startswith('addr:')

# Parse address tags
def parse_address(key, val, entity):
	match = RE_ADDR.search(key)
	key = match.group()

	# Strip overqualification of city name 
	# (e.g. 'Chicago, IL' in the city field should just be 'Chicago')
	if is_city(key):
		parse_city(key, val, entity)
	elif is_street(key):
		parse_street(key, val, entity)
	elif is_postcode(key):
		parse_postcode(key, val, entity)
	else:
		entity['address'][key] = val

# Condition wrapper
def is_amenity_cuisine(key):
	return key in ('amenity', 'cuisine')

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

# Parse child 'nd' elements into a list of node references.
def parse_node_refs(child, entity):
	if not entity['node_refs']:
		entity['node_refs'] = []
	entity['node_refs'].append(child.attrib['ref'])



# Iterates over the child elements and adds dictionary representations
# to the parent 'entity' object.
def parse_children(elem, entity):
	for child in elem.iter():

		tag = child.tag

		# Process 'tag' elements
		if tag == 'tag':
			key = child.attrib['k']
			val = child.attrib['v']			
			
			if is_address(key):
				parse_address(key, val, entity)				
			elif is_amenity_cuisine(key):
				parse_amenity_cuisine(key, val, entity)
			else:
				entity[key] = val

		# Process node references
		elif tag == 'nd':
			parse_node_refs(child, entity)


# Checks if XML element is either a 'node' or a 'way' element.
# Returns a dictionary representation of the XML element
def parse_entity(elem):
	if elem.tag in ('node', 'way'):
		entity = defaultdict(dict)
		entity['entity_type'] = elem.tag
		for k in elem.attrib:

			# put attributes with CREATED keywords into nested dict
			if k in CREATED:
				entity['created'][k] = elem.attrib[k]

			# put position attributes in nested 'pos' dict
			elif k in POS:
				entity['pos'] = [float(elem.attrib['lat']), float(elem.attrib['lon'])]

			# Otherwise, add attribute key, value to entity
			else:
				entity[k] = elem.attrib[k]

			# Iterate and add child elements
			parse_children(elem, entity)

		# widen to dict type from defaultdict
		return dict(entity)

	return None

def main(filename, pretty=False):

	# Build reverse lookup street_type_map dictionary
	for key, values in STREET_TYPE_MAP.iteritems():
		for value in values:
			R_STREET_TYPE_MAP[value] = key


	# Open file with .json extension for writing the transformed entities from the .osm file.
	with codecs.open('{0}.json'.format(filename), 'w') as f:

		#Iterate start element events
		for event, elem in ET.iterparse(filename, events=('start', )):
			entity = parse_entity(elem)

			# Write entity to disk
			if entity is not None:
				if pretty:
					f.write(json.dumps(entity, indent = 2) + '\n')
				else:
					f.write(json.dumps(entity) + '\n')

		# Clear elem variable to release memory
		elem.clear()

if __name__ == '__main__':
	main(sys.argv[1], False)
