#!/usr/bin/python3
# Pygorithm2 .pg2 script compiler

from Pygorithm2 import *
from utils.nolog import *

class PG2File(metaclass=SlotsMeta):
	lang: str
	objects: Sdict(list)

	@classmethod
	def open(cls, file):
		if (isinstance(file, str)): file = open(file, 'r')

		f = cls()

		def _getline():
			line = file.readline()
			if (not line): raise EOFError()
			return line.rstrip(os.linesep)

		def parse_code(*, parent):
			nodes = list()

			for ii in itertools.count():
				line = _getline().strip()
				if (not line): continue
				if (line == '}'): break
				m = re.fullmatch(r'(.*?)\s*({)?', line)
				if (m is None): raise SyntaxError(line)
				value, block = m.groups()

				for e, cls, b in (
					(r'IF\s+.*\s+THEN', if_, True),
					(r'ELSEIF\s+.*\s+THEN', elseif, True),
					(r'Else', else_, True),
					(r'End\ ?If', endif, False),
					(r'WHILE\s+.*', while_, True),
					(r'End\ ?While', endwhile, False),
					(r'#.*', comm, False),
					(r'.*', deist, False),
				):
					if (re.fullmatch(e, value, re.I)):
						assert (bool(block) == b)
						break
				else: raise SyntaxError(line)

				obj = cls(value, parent=parent, index=ii)
				if (block): obj.nodes += parse_code(parent=parent)
				nodes.append(obj)

			return nodes

		f.lang = re.fullmatch('Language = (\w+)', _getline())[1]

		while (True):
			try: line = _getline().strip()
			except EOFError: break
			if (not line): continue

			m = re.fullmatch(r'([\w\ ]+?)\s*{', line)
			if (m is None): raise SyntaxError(line)
			form, = m.groups()

			while (True):
				line = _getline().strip()
				if (not line): continue
				if (line == '}'): break

				m = re.fullmatch(r'(\w+)\s+([\w\ ]+?)\s*{', line)
				if (m is None): raise SyntaxError(line)
				class_, name = m.groups()

				try: cls = allsubclassdict(PGObject)['PG'+class_]
				except KeyError: raise NameError(line)
				obj = cls(name)

				cls = first(i for i in allsubclasses(Obj) if i.class_ is cls)
				obj.node = cls(obj.Name, id=obj.Name, parent=obj, index=0)

				while (True):
					line = _getline().strip()
					if (not line): continue
					if (line == '}'): break

					m = re.fullmatch(r'([\w ]+?)\s*{', line)
					if (m is not None):
						type, = m.groups()
						cls = allsubclassdict(Sobyt)[type]
						node = cls(type, parent=obj.node)
						node.nodes = parse_code(parent=node)
						obj.node.nodes.append(node)
						continue

					m = re.fullmatch(r'''([\w\ ]+?)\s*=\s*['"]?(.*?)['"]?''', line)
					if (m is None): raise SyntaxError(line)
					k, v = m.groups()
					obj[k.replace(' ', '_')] = v

				obj.container = f"{form}.{form}[0]" if (not isinstance(obj, PGForm)) else '' # TODO?

				f.objects[form].append(obj)

		return f

	def save(self, file):
		if (isinstance(file, str)): file = open(file, 'w')

		file.write(f"Language = {self.lang}\n")

		for k, v in f.objects.items():
			file.write(k+' {\n'+'\n\n'.join(Sstr(i).indent() for i in v)+'\n}\n')

		file.close()

@apmain
@aparg('file', metavar='file.pg2', type=argparse.FileType('r'))
@aparg('out', metavar='out.alg', type=argparse.FileType('w'))
def main(cargs):
	pg2 = PG2File.open(cargs.file)
	f = AlgFile()

	f.lang = pg2.lang
	#f.params # TODO

	for i in pg2.objects.values():
		for obj in i:
			o = AlgFile.AlgFileObject(obj.typecode)
			for k in sorted((*obj.__dict__.keys(), 'Name')):
				if (k[0].isupper()): o.properties[k.replace('_', ' ')] = obj[k]
			o.properties['#Conteiner'] = obj.container
			o.node = obj.node._alg_repr()+['#End']
			f.objects.append(o)

	f.save(cargs.out)

if (__name__ == '__main__'): exit(main(nolog=True))
else: logimported()

# by Sdore, 2020
