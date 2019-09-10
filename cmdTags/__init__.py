import imp,os

def __load_all__(tags, dir="cmdTags"):
	modules = os.listdir(dir)
	modules.remove('__init__.py')
	for module in modules:
		if module.split('.')[-1]=='py' and module != 'tags.py':
			print("Loading module: ", module)
			#cmdTag = imp.load_module(module
			cmdTag = imp.load_source('module', dir+os.sep+module)
			tag = cmdTag.tag
			tags[tag.getTag()] = tag
			