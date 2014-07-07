import sublime, sublime_plugin
import re

def readline(view, point):
	if (point >= view.size()):
		return

	line = view.line(point)
	return view.substr(line)

class XmldocCommand(sublime_plugin.TextCommand):
	def write(self, view, string):
		view.run_command("insert_snippet", {"contents": string })

	def regularSnippet(self, identifier):
		return "/ <summary>\n/// ${1:" + re.sub("([a-z])([A-Z])","\g<1> \g<2>", identifier).capitalize() + "}\n/// </summary>"

	def functionSnippet(self, identifier, args=None, returnType=None):
		snippet = "/ <summary>\n/// ${1:%s}\n/// </summary>" % identifier
		n = 2
		if args and len(args):
			for a in args.split(","):
				a = a.strip();
				v = a.split(" ")
				if len(v) > 1:
					snippet += "\n/// <param name=\"%s\">${%d:param}</param>" % (v[1].strip(), n)
				n = n + 1
		if returnType and len(returnType) and returnType.find('void') == -1:
			snippet += "\n/// <returns>${%d:returns %s}</returns>" % (n, returnType)
		return snippet

	def createSnippet(self, view):
		point = view.sel()[0].begin()
		currentLine = readline(self.view, point)

		nextPoint = point + len(currentLine) + 1
		nextLine = readline(view, nextPoint)

		m = re.search(self.regexp["class"], nextLine)
		if m:
			return self.regularSnippet(m.group(1))

		m = re.search(self.regexp["function"], nextLine)
		if m and re.search(self.regexp["modifiers"], m.group('return')) is None:
			return self.functionSnippet(m.group('name'), m.group('args'), m.group('return'))

		m = re.search(self.regexp["constructor"], nextLine)
		if m:
			return self.functionSnippet(m.group('name'), m.group('args'))
		
		return "/"

	def init(self):
		identifier = r"([a-zA-Z_]\w*)"
		modifiers = r"\s*(?:(?:public|protected|private|static|virtual|abstract|override)\s+)*"
		returnType = r"(?P<return>[\w:<>]+)\s+"
		functionName = r"(?P<name>[a-zA-Z_]\w*)\s*"
		args = r"\((?P<args>[:<>\[\]\(\),.*&\w\s]*)\).*"
		returnType = r"(?P<return>[\w<>]+)\s+"

		self.regexp = {
			"modifiers": r"\s*(public|protected|private|static|virtual|abstract|override)\s*",
			"class": r"\s*(?:class|struct)\s*" + identifier + r"\s*{?",
			"constructor": modifiers + functionName + args,
			"function": modifiers + returnType + functionName + args,
			"property": modifiers + returnType + functionName + r".*",
		}

	def run(self, edit, key=None):
		if key is None:
			return

		self.init()

		if key == "enter":	
			point = self.view.sel()[0].begin()
			currentLine = readline(self.view, point)

			m = re.match(r"^(\s*)\/{3}.*$", currentLine)
			if m is not None:
				nextLine = "\n" + m.group(1) + "/// "
				currentRegion = self.view.sel()[0]

				if self.view.sel()[0].size() > 0:
					pos = currentRegion.begin() + len(nextLine)
					self.view.replace(edit, currentRegion, nextLine)

					self.view.sel().clear()
					self.view.sel().add(sublime.Region(pos))
				else:
					self.view.insert(edit, currentRegion.end(), nextLine)


		else:
			snippet = self.createSnippet(self.view)
			if snippet and len(snippet) > 0:
				self.write(self.view, snippet)
