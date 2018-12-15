from __future__ import print_function,absolute_import
import sys, os, re
from pprint import pprint

class Day5(object):
	def __init__(self, input_file):
		with open(input_file, "r") as f:
			data = f.read().strip()
		self.data = data

	def reduce(self, s):
		rex = re.compile(r"(aA|Aa|bB|Bb|cC|Cc|dD|Dd|eE|Ee|fF|Ff|gG|Gg|hH|Hh|iI|Ii|jJ|Jj|kK|Kk|lL|Ll|mM|Mm|nN|Nn|oO|Oo|pP|Pp|qQ|Qq|rR|Rr|sS|Ss|tT|Tt|uU|Uu|vV|Vv|wW|Ww|xX|Xx|yY|Yy|zZ|Zz)")
		
		current = s
		while True:
			reduced = rex.sub("", current)
			if len(current) == len(reduced):
				break
			current = reduced
		return current

	def part1(self):
		reduced = self.reduce(self.data)
		return len(reduced)

	def part2(self):
		min = None
		for i in range(0, 26):
			sys.stdout.write("testing letter %s ... " % chr(ord('a')+i))
			sys.stdout.flush()
			customized_data = re.sub(chr(ord('a')+i), "", self.data, flags=re.IGNORECASE)
			reduced_size = len(self.reduce(customized_data))
			sys.stdout.write("%5d units" % (reduced_size,))
			if (min is None) or reduced_size < min:
				min = reduced_size
				sys.stdout.write(" (new best)")
			sys.stdout.write("\n")
			sys.stdout.flush()

		return min

if __name__ == "__main__":
	day = Day5("day5.txt")
	print(day.part1())
	print(day.part2())