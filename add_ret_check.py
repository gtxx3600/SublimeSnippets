import sublime, sublime_plugin
import re

func_call_re_exp = "^\\s*(\\w+\\s+)?(\\w+)\\s*=\\s*(\\w+)\\((.*)\\)"

arg_replacement = {
	'ret' : ('<%d>', '%s'),
	'user_id' : ('<%u>', '%s'),
	'uin' : ('<%u>', '%s'),
	'mid' : ('<%llu>', '%s'),
	'user' : ('<%u>', '%s->user_id'),
	'actor' : ('<%u>', '%s->uin'),
	'addr' : ('<%x>', '%s'),
}

def get_arg_replacement(arg_name):
	for k in arg_replacement:
		if arg_name.endswith(k):
			return arg_replacement[k]
	return None

def get_arg_replacement_list(arg_list):
	ret = []

	for arg in arg_list:
		tup = get_arg_replacement(arg)
		if tup:
			#print(tup)
			replacement, arg_rep = tup
			ret.append((arg_rep % arg, replacement))

	return ret

def build_ret_check(prefix, ret_name, func_name, arg_list):
	code_lines = ['']
	code_lines.append(prefix + "if(%s != 0)" % ret_name)
	code_lines.append(prefix + "{")

	arg_list = [ret_name] + arg_list
	rep_list = get_arg_replacement_list(arg_list)
	error_tlog_line = prefix + '\terror_tlog("%s failed' % func_name
	for rep in rep_list:
		arg_name, rep_name = rep
		error_tlog_line += ", " + arg_name + " %s" % rep_name

	error_tlog_line += '"'
	if len(rep_list) > 2:
		error_tlog_line += '\n' + prefix + '\t\t'
	for rep in rep_list:
		arg_name, rep_name = rep
		error_tlog_line += ", " + arg_name
	error_tlog_line += ');'

	code_lines.append(error_tlog_line)
	code_lines.append(prefix + "\treturn -1;")
	code_lines.append(prefix + "}")

	return '\n'.join(code_lines)

class AddRetCheckCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		sel = self.view.sel()
		#print(sel)
		for region in sel:
			#print(region)
			if region.empty():
				line = self.view.line(region)
				lineContent = self.view.substr(line)

				prefix = ''
				tmp_list = re.findall("^(\\s*)\\w+", lineContent)
				if tmp_list:
					prefix = tmp_list[0]

				tmp_list = re.findall(func_call_re_exp, lineContent)

				if not tmp_list:
					continue
					
				tup = tmp_list[0]
				if not tup or len(tup) != 4:
					print("wrong tup len <%d>" % len(tup))
					print(tup)
					return

				ret_type = tup[0]
				ret_name = tup[1]
				func_name = tup[2]
				arg_list = tup[3].split(',')
				for i in range(len(arg_list)):
					arg_list[i] = arg_list[i].strip()

				code_lines = build_ret_check(prefix, ret_name, func_name, arg_list)
				#print(code_lines)
				self.view.insert(edit, line.end(), code_lines)
