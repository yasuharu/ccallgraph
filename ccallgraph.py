#! /usr/bin/python

# @author Yasuharu Shibata <admin@mail.yasuharu.net>

import sys

# @brief search function name
# @note this function search backward from "(".
#       first we search isalnum, next we have been push at ret varable while all_text[i] == isalnum.
# @ret function name
def search_function_name(all_text, text_num):
	ret = "";
	push_status = False;
	for i in range(text_num - 1, 0, -1):
		if push_status == True:
			# end of function name
			if all_text[i].isalnum() == False and all_text[i] != "_":
				return ret;
			else:
				ret = all_text[i] + ret;

		# search start pos
		else:
			if all_text[i].isalnum() or all_text[i] == "_":
				ret = all_text[i];
				push_status = True;

	# it's Bug...
	raise Exception()

# @brief search ; or {.
# @note if find ;, this is callee. if find {, this is function decleration.
# @ret 1 find ; (callee).
# @ret 2 find { (function).
def search_end_code(all_text, text_num):
	for i in range(text_num, len(all_text)):
		if all_text[i] == ";":
			return 1;
		if all_text[i] == "{":
			return 2;

	# it's Bug...
	raise Exception();

# @brief search end of function.
# @note we search { and } block.
def search_end_function(all_text, text_num):
	depth = 1;
	find_first_term = False;
	for i in range(text_num, len(all_text)):
		if all_text[i] == "{":
			if find_first_term:
				depth = depth + 1;
			else:
				# if you already find {, it's maybe if or for statement blocks.
				find_first_term = True;

		if all_text[i] == "}":
			if find_first_term:
				if depth == 1:
					return i;
				else:
					depth = depth - 1;
			else:
				# it's Bug...
				raise Exception();

# @brief save input file name.
input_file_list = [];

for i in range(len(sys.argv)):
	if i == 0:
		continue;

	input_file_list.append(sys.argv[i]);

print "# Analyze C source";
print "# [Warning] This software is not support i18n";

function_list = [];
callee_list   = [];

# analyze C language files.
for file in input_file_list:
	input_file_text_list = [];
	input_file_all_text  = "";
	function_hint        = [];

	try:
		f = open(file, "r");
	except IOError:
		print "Can't open " + file;
		continue;

	# gather all line and make function hint
	line_num = 0;
	for line in f:
		# search function hint
		try:
			i = line.index("(");
		except ValueError:
			i = None;
		else:
#			print "find hint at " + str(line_num) + ":" + str(i);
#			print line;
			function_hint.append(
				# save (number of line, index of line, position of all text) tuple
				(line_num, i, i + len(input_file_all_text))
			);

		input_file_all_text += line;
		input_file_text_list.append(line);
		line_num = line_num + 1;

	# search function decleration
	temp_function_list = [];	# [name, text_num, end_function_num, line_num, file_name]
	temp_callee_list   = [];	# [name, text_num, line_num, file_name]

	for hint in function_hint:
		hint_line_num      = hint[0];
		hint_line_text_num = hint[1];
		hint_text_num      = hint[2];

		name = search_function_name(input_file_all_text, hint_text_num);
		type = search_end_code(input_file_all_text, hint_text_num);

		if name == "if" or name == "for" or name == "switch" or name == "while":
			continue;

		if(type == 1):
			temp_callee_list.append([name, hint_text_num, hint_line_num, file]);
#			print "callee : " + name + " at " + str(hint_text_num);
		elif(type == 2):
			end_function_num   = search_end_function(input_file_all_text, hint_text_num);

			is_not_function = False;
			# if we find same end_function_num item, maybe before find item is invalid.
			for i in range(len(temp_function_list)):
				if end_function_num == temp_function_list[i][2]:
					# find same end_function_num
					temp_function_list.pop(i);
					break;

				if end_function_num < temp_function_list[i][2]:
					# if this is inner function block, maybe this is ivalid.
					is_not_function = True;
					break;

			if is_not_function:
				continue;

			temp_function_list.append([name, hint_text_num, end_function_num, hint_line_num, file]);

	# callee eliminate not inner function block.
	temp_callee_list2 = [];	# [name, text_num, line_num, file_name, caller]
	for function in temp_function_list:
		function_name      = function[0];
		function_begin_num = function[1];
		function_end_num   = function[2];

		for callee in temp_callee_list:
			callee_name = callee[0];
			callee_num  = callee[1];
	
			# print "function : " + function[0] + " at " + str(function_begin_num) + " - " + str(function_end_num);
			# print "callee : " + callee_name + " at " + str(callee_num);
	
			if function_begin_num < callee_num and callee_num < function_end_num:
				callee.append(function_name);
				temp_callee_list2.append(callee);

	function_list.extend(temp_function_list);
	callee_list.extend(temp_callee_list2);

print "digraph output {";

for function in function_list:
	function_name      = function[0];
	function_begin_num = function[1];
	function_end_num   = function[2];
	file               = function[4];

	for callee in callee_list:
		callee_name   = callee[0];
		callee_caller = callee[4];

		if function_name != callee_caller:
			continue;

		# eliminate not function list item
		for f in function_list:
			if(callee[0] == f[0]):
				print function_name + " -> " + str(callee[0]) + " [label=\"" + file + " line at " + str(callee[2]) + "\"]";

print "}";

