import sublime, sublime_plugin
import math

# Sections to parse
test_markers = ('Scenario 1', 'Scenario 2', 'Scenario 3', 'Scenario 4', 'Scenario 5')
quality_markers = ('i.', 'ii.', 'iii.', 'iv.', 'v.', 'vi.', 'vii.')
grade_markers = ('Testing:', 'Usability:', 'Quality:')


def calc_overall_test(tests):
	''' Calculate the overall test grade
	'''
	return sum(tests)


def calc_overall_quality(quality):
	''' Calculate the overall quality grade
	'''
	raw =  sum(quality[:-1]) * quality[-1]
	return math.ceil(raw * 2)/(2.0)


def find_marks_a12(text):
	''' Parse the text to retrieve testing and quality marks for Assignment 1/2
	'''
	lines = text.split('\n')
	quality = [-1] * len(quality_markers)

	for line in lines:
		for marker in quality_markers:
			if line.startswith(marker):
				if len(line.split(':')) <= 1:
					sublime.error_message("Missing colon on quality section " + marker)
				else:
					try:
						quality[quality_markers.index(marker)] = float(line.split(':')[1].strip())
					except ValueError:
						sublime.error_message("No mark for quality section " + marker)

	if -1 in quality:
		sublime.error_message("Missing quality section " + quality_markers[quality.index(-1)])

	return quality


def find_marks_a3(text):
	''' Parse the text to retrieve testing and quality marks for Assignment 3
	'''
	lines = text.split('\n')

	quality = [-1] * len(quality_markers[:-1])
	tests = [-1] * len(test_markers)

	for line in lines:
		# Find quality grades
		for marker in quality_markers[:-1]:
			if line.startswith(marker):
				if len(line.split(':')) <= 1:
					sublime.error_message("Missing colon on quality section " + marker)
				else:
					try:
						quality[quality_markers.index(marker)] = float(line.split(':')[1].strip())
					except ValueError:
						sublime.error_message("No mark for quality section " + marker)
		
		# Find testing grades
		for marker in test_markers:
			if line.startswith(marker):
				if len(line.split(':')) <= 1:
					sublime.error_message("Missing colon on testing section " + marker)
				else:
					try:
						tests[test_markers.index(marker)] = float(line.split(':')[1].strip())
					except ValueError:
						sublime.error_message("No mark for testing section " + marker)

	# Check for missing sections
	if -1 in quality:
		sublime.error_message("Missing quality section " + quality_markers[quality.index(-1)])
	if -1 in tests:
		sublime.error_message("Missing testing section " + test_markers[tests.index(-1)])

	return [tests, quality]


def find_max_marks_per_section(text, markers):
	lines = text.split('\n')
	max_marks = [-1] * len(markers)

	for line in lines:
		for marker in markers:
			if line.startswith(marker):
				if len(line.split(']')) <= 1:
					sublime.error_message("Missing ] on marker " + marker)
				# Get the max marks for the section, from the part of the line in the form [poor=0, fair=0.5, good=1]
				try:
					max_marks[markers.index(marker)] = float((line.split(']')[-2]).split('=')[-1])
				except ValueError:
					sublime.error_message("Invalid max marks on marker " + marker)
				except Exception as e:
					sublime.error_message("Could not retrieve max marks for marker " + marker + " due to exception: " + str(e))

	return max_marks


def check_marks_in_range(marks, max_marks, markers):
	if -1 in max_marks:
		sublime.error_message("Missing max marks on marker " + markers[max_marks.index(-1)])
		return False

	for i in range(0, len(markers)):
		if marks[i] > max_marks[i]:
			sublime.error_message("Mark greater than maximum on marker {} ({} > {})".format(markers[i], marks[i], max_marks[i]))
			return False
		elif marks[i] < 0:
			sublime.error_message("Mark less than 0 on marker {} ({} < 0)".format(markers[i], marks[i]))
	return True


def set_overall_grade_a12(view, edit, grade):
	''' Modify the open text file to set the testing and quality grades for Assignment 1/2
	'''
	text = view.substr(sublime.Region(0, view.size()))

	lines = text.split('\n')
	qualRow = -1
	qualCol = -1

	for line in lines:
		if qualRow >= 0 and qualCol >= 0:
			break

		if line.startswith(grade_markers[2]):
			# Quality grade line
			qualRow = lines.index(line)
			try:
				qualCol = line.index(':')
			except ValueError:
				sublime.error_message("Missing colon on overall quality grade line")

	if qualRow == -1:
		sublime.error_message("Invalid overall quality grade line")
	else:
		# Insert the grades
		qualPoint = view.text_point(qualRow, qualCol+1)
		view.insert(edit, qualPoint, " {0}".format(grade))


def set_overall_grade_a3(view, edit, testing_grade, quality_grade):
	''' Modify the open text file to set the testing and quality grades for Assignment 3
	'''
	text = view.substr(sublime.Region(0, view.size()))

	# Find the overall grade positions in the text file
	lines = text.split('\n')
	testRow = -1
	testCol = -1
	qualRow = -1
	qualCol = -1
	
	for line in lines:
		if testRow >= 0 and testCol >= 0 and qualRow >= 0 and qualCol >= 0:
			break

		if line.startswith(grade_markers[0]):
			# Testing grade line
			testRow = lines.index(line)
			try:
				testCol = line.index(':')
			except ValueError:
				sublime.error_message("Missing colon on overall testing grade line")
		elif line.startswith(grade_markers[2]):
			# Quality grade line
			qualRow = lines.index(line)
			try:
				qualCol = line.index(':')
			except ValueError:
				sublime.error_message("Missing colon on overall quality grade line")

	# Check if an overall grade line was missing
	if testRow == -1:
		sublime.error_message("Invalid overall testing grade line")
	elif qualRow == -1:
		sublime.error_message("Invalid overall quality grade line")
	else:
		# Insert the grades
		testPoint = view.text_point(testRow, testCol+1)
		view.insert(edit, testPoint, " {0}".format(testing_grade))
		qualPoint = view.text_point(qualRow, qualCol+1)
		view.insert(edit, qualPoint, " {0}".format(quality_grade))


class CalcMarksAssignment3Command(sublime_plugin.TextCommand):
	def run(self, edit):
		text = self.view.substr(sublime.Region(0, self.view.size()))

		# Get the grades
		marks = find_marks_a3(text)
		
		testing_grade = calc_overall_test(marks[0])
		quality_grade = calc_overall_quality(marks[1])

		# Set the overall grades
		set_overall_grade_a3(self.view, edit, testing_grade, quality_grade)


class CalcMarksAssignment1Command(sublime_plugin.TextCommand):
	def run(self, edit):
		text = self.view.substr(sublime.Region(0, self.view.size()))

		# Get the grades
		marks = find_marks_a12(text)
		
		# Get the quality grade from those marks
		grade = calc_overall_quality(marks)

		if check_marks_in_range(marks, find_max_marks_per_section(text, quality_markers), quality_markers):
			# Set the overall grades
			set_overall_grade_a12(self.view, edit, grade)


class CalcMarksAssignment2Command(sublime_plugin.TextCommand):
	def run(self, edit):
		text = self.view.substr(sublime.Region(0, self.view.size()))

		# Get the grades
		marks = find_marks_a12(text)
		
		# Get the quality grade from those marks
		grade = calc_overall_quality(marks)

		if check_marks_in_range(marks, find_max_marks_per_section(text, quality_markers), quality_markers):
			# Set the overall grades
			set_overall_grade_a12(self.view, edit, grade)


