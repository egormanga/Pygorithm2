#!/usr/bin/python3
# Pygorithm2

import tkinter.messagebox, tkinter as tk
from utils import *; logstart('Pygorithm2')

class AlgFile(metaclass=SlotsMeta):
	class AlgFileObject(metaclass=SlotsMeta):
		typecode: str
		properties: dict
		node: list

		def __init__(self, typecode):
			self.typecode = typecode

	lang: str
	objects: list
	params: dict

	@classmethod
	def open(cls, file):
		if (isinstance(file, str)): file = open(file, 'r')

		f = cls()

		def _getline():
			line = file.readline()
			if (not line): raise EOFError()
			return line.rstrip(os.linesep)

		f.lang = re.fullmatch('Language = (\w+)', _getline())[1]

		while (True):
			try: typecode = _getline()
			except EOFError: break
			if (not typecode): continue
			if (typecode == '#ProjectParams'):
				while (True):
					line = _getline()
					if (line == '#EndProjectParams'): break
					f.params[k.lstrip('#')] = line
				break
			obj = cls.AlgFileObject(typecode)

			while (True):
				k = _getline()
				if (k == '#TreeNode'): break
				obj.properties[k] = _getline()

			while (True):
				line = _getline()
				obj.node.append(line)
				if (line == '#End'): break

			f.objects.append(obj)

		return f

	def save(self, file):
		if (isinstance(file, str)): file = open(file, 'w')

		file.write(f"Language = {self.lang}\r\n")

		for obj in self.objects:
			file.write('\r\n'+obj.typecode+'\r\n')
			for k, v in obj.properties.items():
				file.write(k+'\r\n'+v+'\r\n')
			file.write('#TreeNode\r\n'+'\r\n'.join(obj.node)+'\r\n')

		if (self.params):
			file.write('\r\n#ProjectParams\r\n')
			for k, v in self.params.items():
				file.write('#'+k+'\r\n'+v+'\r\n')
			file.write('#EndProjectParams\r\n')

		file.close()

class PGObject:
	Tag = ''
	X = ...
	Y = ...

	def __init__(self, name):
		self.name = name
		self.container = None
		self.history_level = None
		self.node = None

	def __repr__(self):
		return f"<PGObject {self.__class__.__name__[2:]}({self.typecode}) '{self.name}'>"

	def __str__(self):
		return str(self.node)

	def __getitem__(self, x):
		return getattr(self, x)

	def __setitem__(self, x, v):
		setattr(self, x, v)

	def __setattr__(self, x, v):
		super().__setattr__(x, v)
		try:
			if (not self.node.created): return
		except AttributeError: pass
		else: self.node.sync(x)

	@property
	def id(self):
		return self.node.id

	@property
	def index(self):
		try: return self.Index
		except AttributeError: return 0

	@classmethod
	def build(cls, fobj):
		obj = first(i for i in allsubclasses(cls) if getattr(i, 'typecode', None) == fobj.typecode)(...)

		for k, v in fobj.properties.items():
			if (k == '#Conteiner'):
				obj.container = v
			elif (k == '#HistoryLevel'):
				obj.history_level = int(v)
			elif (k == '#TreeNode'):
				break
			elif (k.startswith('#')):
				raise WTFException(k)
			obj[k.replace(' ', '_')] = v

		parent_ = f"{(obj.container or obj.name).partition('.')[0]}(0)"
		if (fobj.node[0] == '#Parent'):
			del fobj.node[0]
			parent = fobj.node.pop(0)
		else: parent = parent_
		assert (parent == parent_)

		if (fobj.node[0] == '#Index'):
			del fobj.node[0]
			index = int(fobj.node.pop(0))
		else: index = None

		obj.node = TreeNode.build(fobj.node, parent=obj, index=index)
		assert (fobj.node.pop(0) == '#End' and not fobj.node)

		return obj

	def Create(self):
		self.node.create()

	@property
	def Name(self):
		return self.name

	@Name.setter
	def Name(self, Name):
		self.name = Name

	@property
	def Type(self):
		return type(self).__name__[2:]

class PGForm(PGObject):
	typecode = 'F'

	Height = 320
	Visible = 'Yes'
	Width = 500
	X = 0
	Y = 0

	def Create(self):
		super().Create()
		if (self.Visible == 'No'):
			self.Hide()

	def Close(self):
		self.node.close()

	def Show(self):
		self.Visible = 'Yes'

	def Hide(self):
		self.Visible = 'No'

	def Focus(self):
		self.node.lift()

class PGWidget(PGObject):
	Visible = 'Yes'

	def Create(self):
		super().Create()
		if (self.X is ...): self.X = (self.container.Width-self.Width)//2
		if (self.Y is ...): self.Y = (self.container.Height-self.Height)//2
		self.node.sync_all()

	def Click(self):
		self.node.click()

class PGButton(PGWidget):
	typecode = 'B'

	Height = 23
	Width = 75

class PGMemory(PGObject):
	typecode = 'M'

	Value = ''

class TreeNode(abc.ABC):
	def __init__(self, value, *, id=None, parent, index=0):
		self.value, self.id, self.parent, self.index = value, id or hashlib.md5(hex(hash(self))[2:].encode()).hexdigest(), parent, index # TODO FIXME id
		self.nodes = list()

	def __repr__(self):
		return f"<{self.type} #{self.id}>"

	def __str__(self):
		return f"{self.value} {self.__fblock__()}"

	def __fblock__(self):
		return '{\n'+S('\n').join(self.nodes).indent()+'\n}'

	def _alg_repr(self):
		res = [self.value, self.id, self.type, self.type, first(i.__name__ for i in type(self).mro()[1:] if i.__base__ is TreeNode)]
		for i in self.nodes:
			res += [' '+j for j in i._alg_repr()]
		return res

	@property
	def type(self):
		return self.__class__.__name__.rstrip('_')

	@classmethod
	def build(cls, lines, parent, index, *, l=0):
		def getval():
			if (not lines or not lines[0].startswith(' '*l)): raise IndentationError()
			return lines.pop(0).lstrip(' ')

		value = getval()
		id = getval()
		type = getval()
		assert (getval() == type)
		class_ = getval()

		if (type in ('if', 'else', 'while')): type += '_'

		cls = allsubclassdict(cls)[class_]
		cls = allsubclassdict(cls)[type]
		obj = cls(value, id=id, parent=parent, index=index)

		ii = int()
		while (True):
			try: obj.nodes.append(TreeNode.build(lines, parent=obj, index=ii, l=l+1))
			except IndentationError: break
			ii += 1

		#dlog(repr(obj), obj)
		return obj

class Obj(TreeNode, metaclass=ABCSlotsMeta):
	class_: abc.abstractproperty
	_sync_all = ()
	parent: ...
	nosync: lambda: threading.Lock()
	created: bool

	def __str__(self):
		return f"{self.class_.__name__[2:]} {self.value} {self.__fblock__()}"

	def __fblock__(self):
		return '{\n'+S(S('\n').join((*(' = '.join((k.replace('_', ' '), v)) for k, v in self.parent.__dict__.items() if k[0].isupper()), '', *self.nodes)).strip('\n')).indent()+'\n}'

	def create(self):
		self.created = True

	def sync(self, param):
		if (self.nosync.locked()): return
		raise WTFException(param)

	def sync_all(self):
		if (self.nosync.locked()): return
		for i in self._sync_all:
			self.sync(i)

	def fire_event(self, type):
		for i in self.nodes:
			if (isinstance(i, Click)):
				i.fire()

	@property
	def scope(self):
		return self.parent.container.node.scope

class window(Obj, tk.Toplevel):
	class_ = PGForm
	_sync_all = ('_position', 'Visible', 'Text')
	scope = None
	root: ...

	def create(self):
		super().create()
		tk.Toplevel.__init__(self, self.root)
		self.protocol('WM_DELETE_WINDOW', self.parent.Close)
		self.bind('<Configure>', self.onresize)
		self.sync('_position')
		self.title(self.parent.Text)
		self.fire_event(Created)

	def close(self):
		self.destroy()
		self.root.destroy() # TODO FIXME

	def show(self):
		self.deiconify()
		self.focus_force()
		self.fire_event(Visible_changed)

	def hide(self):
		self.withdraw()
		self.fire_event(Visible_changed)

	def onresize(self, event):
		with self.nosync:
			self.parent.X = self.winfo_rootx()
			self.parent.Y = self.winfo_rooty()
			self.parent.Width = self.winfo_width()
			self.parent.Height = self.winfo_height()

	def sync(self, param):
		if (self.nosync.locked()): return
		if (param in ('X', 'Y', 'Width', 'Height', '_position')):
			self.geometry(f"{self.parent.Width}x{self.parent.Height}+{self.parent.X}+{self.parent.Y}")
		elif (param == 'Visible'):
			if (self.parent.Visible == 'Yes'): self.show()
			else: self.hide()
		elif (param == 'Text'):
			self.title(self.parent.Text)
		else: raise WTFException(param)

class WidgetObj(Obj, tk.Widget):
	class_ = PGWidget

	def create(self):
		super().create()
		self.fire_event(Created)

	def bring_to_front(self):
		self.lift()

	def sync(self, param): # TODO FIXME dup
		if (self.nosync.locked()): return
		if (param in ('X', 'Y', 'Width', 'Height', '_position')):
			self.size(f"{self.parent.Width}x{self.parent.Height}+{self.parent.X}+{self.parent.Y}")
		elif (param == 'Visible'):
			if (self.parent.Visible == 'Yes'): self.show()
			else: self.hide()
		else: raise WTFException(param)

class button(WidgetObj, tk.Button):
	class_ = PGButton

	def create(self):
		super().create()
		tk.Button.__init__(self, self.parent.container.node)
		self.configure(text=self.parent.Text, command=self.parent.Click)
		self.pack()

	def click(self):
		self.fire_event(Click)

class memory(Obj):
	class_ = PGMemory

class Sobyt(TreeNode):
	def fire(self):
		for i in self.nodes:
			if (isinstance(i, Deist)):
				i.run()

	@property
	def scope(self):
		return self.parent.scope
class Created(Sobyt): pass
class Click(Sobyt): pass
class Form_closing(Sobyt): pass
class Size_changed(Sobyt): pass
class Visible_changed(Sobyt): pass

class Deist(TreeNode):
	def __str__(self):
		return self.value

	@abc.abstractmethod
	def run(self): pass

	@property
	def scope(self):
		return self.parent.scope
class deist(Deist):
	def run(self):
		m = re.fullmatch(r'([\w\ ]+)\.([\w\ ]+)\.([\w\ ]+)\ ?=\ ?(.*)', self.value)
		if (m is not None): self.scope[m[1]][m[2]][m[3].rstrip(' ')] = m[4]; return

		m = re.fullmatch(r'([\w\ ]+)\.([\w\ ]+)\.([\w\ ]+)(?:\((.*)\))?', self.value)
		self.scope[m[1]][m[2]][m[3]](*filter(None, (i.strip(',"\'') for i in shlex.split(m[4], posix=False)) if (m[4] is not None) else ()))

class If(TreeNode): pass
class if_(If):
	TODO

class ElseIf(TreeNode): pass
class elseif(ElseIf):
	TODO

class Else(TreeNode): pass
class else_(Else):
	TODO

class EndIf(TreeNode):
	def __str__(self):
		return self.value
class endif(EndIf):
	TODO

class While(TreeNode): pass
class while_(While):
	TODO

class EndWhile(TreeNode):
	def __str__(self):
		return self.value
class endwhile(EndWhile):
	TODO

class EmptyIf(TreeNode): pass
class EmptyCycle(TreeNode): pass
class Nothing(EmptyIf, EmptyCycle): pass

class Comm(TreeNode):
	def __str__(self):
		return self.value
class comm(Comm): pass

class Algorithm2:
	scope = {
		'_Useful objects': {
			'_Show messange': {
				'_Show message': lambda message, buttons, type, title: tk.messagebox.Message(type=buttons.lower().replace(' ', ''), icon={'critical': 'error', 'exclamation': 'warning', 'information': 'info', 'default': 'info'}.get(*(type.lower(),)*2), title=title, message=message).show(),
			}
		}
	}

	def __init__(self, lang):
		self.lang = lang
		self.objects = dict()
		self.params = dict()
		self.tk = tk.Tk()
		self.scope = Sdict(dict, copy.deepcopy(self.scope))

	@classmethod
	def open(cls, file):
		file = AlgFile.open(file)
		alg = cls(file.lang)
		alg.params = file.params.copy()

		for obj in file.objects:
			obj = PGObject.build(obj)
			alg.objects[obj.id] = obj
			if (obj.container):
				obj.container = alg.objects[obj.container.partition('.')[0]]
			else:
				obj.node.root = alg.tk
				obj.node.scope = alg.scope
				obj.container = obj
			alg.scope[obj.container.Name][obj.Name] = obj

			#dplog(alg.scope)

		return alg

	def save(self, file):
		f = AlgFile()

		f.lang = self.lang
		f.params = self.params.copy()

		for obj in self.objects.values():
			o = AlgFile.AlgFileObject(obj.typecode)
			for k in sorted((*obj.__dict__.keys(), 'Name')):
				if (k[0].isupper()): o.properties[k.replace('_', ' ')] = obj[k]
			o.properties['#Conteiner'] = f"{obj.container.id}.{obj.container.name}[{obj.container.index}]" if (obj.container is not obj) else ''
			if (obj.history_level is not None): o.properties['#HistoryLevel'] = str(obj.history_level)
			o.node = obj.node._alg_repr()+['#End']
			f.objects.append(o)

		f.save(file)

	def run(self):
		print(self.lang)
		for i in self.objects.values():
			i.Create()
		self.tk.overrideredirect(1)
		self.tk.withdraw()
		self.tk.mainloop()

@apmain
@aparg('file', type=argparse.FileType('r'))
def main(cargs):
	alg = Algorithm2.open(cargs.file)
	alg.run()

if (__name__ == '__main__'): exit(main())
else: logimported()

# by Sdore, 2020
