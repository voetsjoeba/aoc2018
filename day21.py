#!/usr/bin/env python
from __future__ import print_function, absolute_import
import sys, os, re
from collections import namedtuple, defaultdict
from math import floor, ceil
from pprint import pprint
from copy import copy
from getpass import getpass

MULI = 0
BORR = 1
GTRI = 2
EQRI = 3
GTRR = 4
EQIR = 5
ADDI = 6
SETR = 7
MULR = 8
ADDR = 9
BORI = 10
BANI = 11
SETI = 12
EQRR = 13
BANR = 14
GTIR = 15

def yellow(s):
	return "\033[33;1m%s\033[0;m" % (s,)

class Instruction(object):
	opnames = ["muli", "borr", "gtri", "eqri", "gtrr", "eqir", "addi", "setr", "mulr", "addr", "bori", "bani", "seti", "eqrr", "banr", "gtir"]
	opcodes = dict((name, code) for code, name in enumerate(opnames))

	@classmethod
	def parse(cls, line):
		parts = line.split(" ")
		opcode = cls.opcodes[parts[0]]
		op1 = int(parts[1])
		op2 = int(parts[2])
		op3 = int(parts[3])
		return Instruction(opcode, op1, op2, op3)

	def __init__(self, opcode, op1, op2, op3):
		self.opcode = opcode
		self.op1 = op1
		self.op2 = op2
		self.op3 = op3

	@property
	def name(self):
		return self.opnames[self.opcode]

	def __str__(self):
		return "%s %d %d %d" % (self.name, self.op1, self.op2, self.op3)

class MiniCpu(object):
	def __init__(self):
		self.reg = [0]*6
		self.pc = 0
		self.program = None
		self._pc_reg = None

	def set_pc_reg(self, reg_idx):
		self._pc_reg = reg_idx

	def set_program(self, program):
		self.program = program

	def visualize(self):
		reg_format = yellow("%4d")
		result  = "PC = %4d      Next instruction:   %s\n" % (self.pc, self.program[self.pc])
		result += ("R0 = "+reg_format+", R1 = "+reg_format+", R2 = "+reg_format+", R3 = "+reg_format+", R4 = "+reg_format+", R5 = "+reg_format+"") % (self.reg[0], self.reg[1], self.reg[2], self.reg[3], self.reg[4], self.reg[5])
		return result

	def run(self):
		self.pc = 0

		while self.pc >= 0 and self.pc < len(self.program):
			if self.pc == 28:
				print(self.visualize())
				raw_input()
			self._tick()
			self.pc += 1


	def _tick(self):
		if self._pc_reg is not None:
			self.reg[self._pc_reg] = self.pc

		inx = self.program[self.pc]

		if   inx.opcode == ADDR:   self.reg[inx.op3] = self.reg[inx.op1] + self.reg[inx.op2]
		elif inx.opcode == ADDI:   self.reg[inx.op3] = self.reg[inx.op1] + inx.op2
		elif inx.opcode == MULR:   self.reg[inx.op3] = self.reg[inx.op1] * self.reg[inx.op2]
		elif inx.opcode == MULI:   self.reg[inx.op3] = self.reg[inx.op1] * inx.op2
		elif inx.opcode == BANR:   self.reg[inx.op3] = self.reg[inx.op1] & self.reg[inx.op2]
		elif inx.opcode == BANI:   self.reg[inx.op3] = self.reg[inx.op1] & inx.op2
		elif inx.opcode == BORR:   self.reg[inx.op3] = self.reg[inx.op1] | self.reg[inx.op2]
		elif inx.opcode == BORI:   self.reg[inx.op3] = self.reg[inx.op1] | inx.op2
		elif inx.opcode == SETR:   self.reg[inx.op3] = self.reg[inx.op1]
		elif inx.opcode == SETI:   self.reg[inx.op3] = inx.op1
		elif inx.opcode == GTIR:   self.reg[inx.op3] = (1 if inx.op1 > self.reg[inx.op2] else 0)
		elif inx.opcode == GTRI:   self.reg[inx.op3] = (1 if self.reg[inx.op1] > inx.op2 else 0)
		elif inx.opcode == GTRR:   self.reg[inx.op3] = (1 if self.reg[inx.op1] > self.reg[inx.op2] else 0)
		elif inx.opcode == EQIR:   self.reg[inx.op3] = (1 if inx.op1 == self.reg[inx.op2] else 0)
		elif inx.opcode == EQRI:   self.reg[inx.op3] = (1 if self.reg[inx.op1] == inx.op2 else 0)
		elif inx.opcode == EQRR:   self.reg[inx.op3] = (1 if self.reg[inx.op1] == self.reg[inx.op2] else 0)
		else:
			raise NotImplementedError()

		if self._pc_reg is not None:
			self.pc = self.reg[self._pc_reg]

class Day21(object):
	def __init__(self, filename):
		with open(filename, "r") as f:
			self.lines = map(str.strip, f.readlines())

		pc_reg = None
		inxs = []

		for line in self.lines:
			if not line: continue
			if line.startswith("#ip "):
				pc_reg = int(line[len("#ip "):])
				continue

			inxs.append(Instruction.parse(line))

		self.program = inxs
		self.pc_reg = pc_reg

	def part1(self):
		return self.reverse_engineered(return_solution_part_1=True, r0=0)

	def part2(self):
		return

	def reverse_engineered(self, return_solution_part_1=False, r0=0):
		r1, r2, r3, r4, r5 = 0, 0, 0, 0, 0
		while True:
			r5 = r2 | 0x10000
			r2 = 0x49E737

			while True:
				r2 = ((r2 + (r5 & 0xFF)) & 0xFFFFFF)
				r2 =  (r2 * 65899)       & 0xFFFFFF
				if r5 < 256:
					break

				# find largest multiple of 256 that doesn't exceed r5 and write it back to r5
				#r4 = 0
				#while (r4+1)*256 <= r5:
				#	r4 += 1
				#r5 = r4

				r5 = int(floor(r5/256.0))

			if return_solution_part_1:
				return r2
			if r2 != r0:
				break


if __name__ == "__main__":
	day = Day21("day21.txt")
	print(day.part1())
	print(day.part2())