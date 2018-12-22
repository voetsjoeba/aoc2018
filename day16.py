#!/usr/bin/env python
from __future__ import print_function, absolute_import
import sys, os, re
from collections import namedtuple, defaultdict
from math import floor
from pprint import pprint
from copy import copy

class Instruction(object):
	def __init__(self, name, op1, op2, op3):
		self.name = name
		self.op1 = op1
		self.op2 = op2
		self.op3 = op3

class MiniCpu(object):
	opnames = set(["addr", "addi", "mulr", "muli", "banr", "bani", "borr", "bori", "setr", "seti", "gtir", "gtri", "gtrr", "eqir", "eqri", "eqrr"])
	def __init__(self):
		self.reg = [0]*4

	def run_instruction(self, inx):
		if inx.name == "addr":
			self.reg[inx.op3] = self.reg[inx.op1] + self.reg[inx.op2]
		elif inx.name == "addi":
			self.reg[inx.op3] = self.reg[inx.op1] + inx.op2
		elif inx.name == "mulr":
			self.reg[inx.op3] = self.reg[inx.op1] * self.reg[inx.op2]
		elif inx.name == "muli":
			self.reg[inx.op3] = self.reg[inx.op1] * inx.op2
		elif inx.name == "banr":
			self.reg[inx.op3] = self.reg[inx.op1] & self.reg[inx.op2]
		elif inx.name == "bani":
			self.reg[inx.op3] = self.reg[inx.op1] & inx.op2
		elif inx.name == "borr":
			self.reg[inx.op3] = self.reg[inx.op1] | self.reg[inx.op2]
		elif inx.name == "bori":
			self.reg[inx.op3] = self.reg[inx.op1] | inx.op2
		elif inx.name == "setr":
			self.reg[inx.op3] = self.reg[inx.op1]
		elif inx.name == "seti":
			self.reg[inx.op3] = inx.op1
		elif inx.name == "gtir":
			self.reg[inx.op3] = (1 if inx.op1 > self.reg[inx.op2] else 0)
		elif inx.name == "gtri":
			self.reg[inx.op3] = (1 if self.reg[inx.op1] > inx.op2 else 0)
		elif inx.name == "gtrr":
			self.reg[inx.op3] = (1 if self.reg[inx.op1] > self.reg[inx.op2] else 0)
		elif inx.name == "eqir":
			self.reg[inx.op3] = (1 if inx.op1 == self.reg[inx.op2] else 0)
		elif inx.name == "eqri":
			self.reg[inx.op3] = (1 if self.reg[inx.op1] == inx.op2 else 0)
		elif inx.name == "eqrr":
			self.reg[inx.op3] = (1 if self.reg[inx.op1] == self.reg[inx.op2] else 0)
		else:
			raise NotImplementedError()

class Sample(object):
	cpu = MiniCpu()

	@classmethod
	def parse(cls, line1, line2, line3):
		m1 = re.match("^Before: \[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]$", line1)
		m2 = re.match("^(\d+) (\d+) (\d+) (\d+)$", line2)
		m3 = re.match("^After:  \[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]$", line3)
		before = map(int, [m1.group(1), m1.group(2), m1.group(3), m1.group(4)])
		inx    = map(int, [m2.group(1), m2.group(2), m2.group(3), m2.group(4)])
		after  = map(int, [m3.group(1), m3.group(2), m3.group(3), m3.group(4)])

		return Sample(before, inx, after)

	def __init__(self, reg_before, instruction, reg_after):
		self.reg_before = reg_before
		self.instruction = instruction
		self.reg_after = reg_after

	def possible_opnames(self, candidates=None):
		candidates = candidates or MiniCpu.opnames
		result = set()
		for opname in candidates:
			self.cpu.reg[:] = self.reg_before
			self.cpu.run_instruction(Instruction(opname, self.instruction[1], self.instruction[2], self.instruction[3]))
			if self.cpu.reg == self.reg_after:
				result.add(opname)

		return result

class Day16(object):
	def __init__(self, filename):
		with open(filename, "r") as f:
			self.lines = [line.strip() for line in f.readlines()]
			self.lines = [line for line in self.lines if line]

		samples = []
		program = []

		i = 0
		while i < len(self.lines):
			line1 = self.lines[i]
			if line1.startswith("Before: "):
				line2 = self.lines[i+1]
				line3 = self.lines[i+2]
				i += 3
				samples.append(Sample.parse(line1, line2, line3))
			else:
				m = re.match("^(\d+) (\d+) (\d+) (\d+)$", line1)
				inx = map(int, [m.group(1), m.group(2), m.group(3), m.group(4)])
				program.append(inx)
				i += 1

		self.samples = samples
		self.program = program

	def part1(self):
		result = 0
		for sample in self.samples:
			possible_opnames = sample.possible_opnames()
			if len(possible_opnames) >= 3:
				result += 1
		return result

	def part2(self):
		possibilities = dict((opcode, set(MiniCpu.opnames)) for opcode in range(0,16)) # opcode -> set of remaining possible opcode names
		known_opcodes = {}

		# run through all the samples, and progressively eliminate impossibilities from opcode_map from the result
		# of each sample evaluation
		while len(known_opcodes) < 16:
			for sample in self.samples:
				opcode = sample.instruction[0]
				if opcode in known_opcodes: continue

				possible_opnames = sample.possible_opnames(possibilities[opcode])
				possibilities[opcode].intersection_update(possible_opnames)

				if len(possible_opnames) == 1:
					opname = list(possible_opnames)[0]
					known_opcodes[opcode] = opname
					for c in range(0,16):
						if c != opcode:
							possibilities[c].discard(opname)

		cpu = MiniCpu()
		for inx in self.program:
			cpu.run_instruction(Instruction(known_opcodes[inx[0]], inx[1], inx[2], inx[3]))
		return cpu.reg[0]

if __name__ == "__main__":
	day = Day16("day16.txt")
	print(day.part1())
	print(day.part2())