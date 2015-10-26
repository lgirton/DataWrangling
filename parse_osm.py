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

# Compiled regular expression to match 'tag' element 'key' attribute.
RE_ADDR = re.compile('(?<=addr\:).*')


# Iterates over the child elements and adds dictionary representations
# to the parent 'entity' object.
def parse_children(elem, entity):
	for child in elem.iter():

		# Process 'tag' elements
		if child.tag == 'tag':
			k = child.attrib['k']
			v = child.attrib['v']
			
			match = RE_ADDR.search(k)
			if match:
				entity['address'][match.group(0)] = v
			elif k in ('amenity', 'cuisine'):
				entity[k] = v.split(';')
			else:
				entity[k] = v

		# Process node references
		elif child.tag == 'nd':
			if not entity['node_refs']:
				entity['node_refs'] = []
			entity['node_refs'].append(child.attrib['ref'])


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