import xml.etree.cElementTree as ET
import sys
import codecs
import re
import json
from collections import defaultdict


CREATED = ['version','changeset','timestamp','user','uid']

POS = ['lat','lon']

RE_ADDR = re.compile('(?<=addr\:).*')


def buildChildren(elem, entity):
	for child in elem.iter():
		if child.tag == 'tag':
			k = child.attrib['k']
			v = child.attrib['v']
			match = RE_ADDR.search(k)
			if match:
				entity['address'][match.group(0)] = v
			elif k == 'amenity':
				entity[k] = v.split(';')
			else:
				entity[k] = v
		elif child.tag == 'nd':
			if not entity['node_refs']:
				entity['node_refs'] = []
			entity['node_refs'].append(child.attrib['ref'])



def buildEntity(elem):
	if elem.tag in ('node', 'way'):
		entity = defaultdict(dict)
		entity['entity_type'] = elem.tag
		for k in elem.attrib:
			if k in CREATED:
				entity['created'][k] = elem.attrib[k]
			elif k in POS:
				entity['pos'] = [float(elem.attrib['lat']), float(elem.attrib['lon'])]
			else:
				entity[k] = elem.attrib[k]

			buildChildren(elem, entity)

		return dict(entity)


		


	return None

def main(filename, pretty=False):
	with codecs.open('{0}.json'.format(filename), 'w') as f:
		for event, elem in ET.iterparse(filename, events=('start', )):
			entity = buildEntity(elem)
			if entity is not None:
				if pretty:
					f.write(json.dumps(entity, indent = 2) + '\n')
				else:
					f.write(json.dumps(entity) + '\n')

		elem.clear()

if __name__ == '__main__':
	main(sys.argv[1], False)