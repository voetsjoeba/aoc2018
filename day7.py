from __future__ import print_function,absolute_import
import sys, os, re
from collections import namedtuple, defaultdict
from pprint import pprint

class Node(object):
	def __init__(self, name, work=1):
		self.name = name
		self.work_remaining = work
		self.followed_by = []
		self.prerequisites = []
	
	def __str__(self):
		return "%s(work=%d)" % (self.name, self.work_remaining)
	
	def follow_by(self, node):
		self.followed_by.append(node)
		node.prerequisites.append(self)
	
	def ready(self):
		return (len(self.prerequisites) == 0 and (self.work_remaining > 0))
		
	def is_finished(self):
		return self.work_remaining == 0
	
	def tick_work(self, amount=1):
		assert (self.work_remaining > 0 and amount <= self.work_remaining) # we don't expect to call this if it's not needed
		self.work_remaining -= amount
		if self.is_finished():
			for f in self.followed_by:
				f.prerequisites.remove(self)
	
	def complete_work(self):
		return self.tick_work(self.work_remaining)

class WorkerPool(object):
	def __init__(self, size):
		self.slots = [None]*size
		self.ticks_taken = 0
	
	def tick(self):
		finished = []
		for i, node in enumerate(self.slots):
			if node is None: continue
			node.tick_work()
			if node.is_finished():
				finished.append(node)
				self.slots[i] = None
		self.ticks_taken += 1
		return finished
	
	def fill(self, nodes):
		remaining = nodes[:]
		while self.slot_available() and len(remaining) > 0:
			node = remaining[0]
			remaining = remaining[1:]
			self.assign(node)
		return remaining

	def _next_available_slot(self):
		for i in range(0, len(self.slots)):
			if self.slots[i] is None:
				return i
		return None
		
	def slot_available(self):
		return (self._next_available_slot() is not None)
	
	def is_empty(self):
		return all(s is None for s in self.slots)
	
	def assign(self, node):
		i = self._next_available_slot()
		assert (i is not None)
		self.slots[i] = node
		
class Day7(object):
	def __init__(self, input_file):
		with open(input_file, "r") as f:
			lines = map(lambda L: L.strip(), f.readlines())
		self.lines = lines
	
	def build_nodes(self, work_offset=0):
		nodes = {} # name -> node
		for line in self.lines:
			match = re.match(r"^Step (\w+) must be finished before step (\w+) can begin.$", line)
			if not match: raise ValueError("bad input line")
			
			# predecessor -> successor
			pred_name = match.group(1)
			succ_name = match.group(2)
			pred = nodes.get(pred_name, Node(pred_name, work=(work_offset + (ord(pred_name)-ord("A")) + 1)))
			succ = nodes.get(succ_name, Node(succ_name, work=(work_offset + (ord(succ_name)-ord("A")) + 1)))
			
			pred.follow_by(succ)
			
			nodes[pred.name] = pred
			nodes[succ.name] = succ
			
		return nodes

	def part1(self):
		# maintain a stack of nodes that are available for processing, starting with
		# nodes that have no prerequisites. prior to handling each one,
		# sort the available stack alphabetically by node name.
		
		# find and append root nodes
		nodes = self.build_nodes()
		stack = [n for n in nodes.values() if n.ready()]
		print("found %d root node(s): %s" % (len(stack), ", ".join(n.name for n in stack)))
		
		result = ""
		while len(stack) > 0:
			# pop an item from the stack, process it, and add any successors that became ready
			stack = sorted(stack, key=lambda n: n.name)
			node = stack[0]
			stack = stack[1:]
			
			node.complete_work()
			result += node.name
			
			for succ in node.followed_by:
				if succ.ready():
					stack.append(succ)
		
		return result
	
	def part2(self):
		# maintain a stack of nodes that are available for processing, starting with
		# nodes that have no prerequisites. prior to assigning available nodes to workers,
		# sort them alphabetically first.
		# also maintain a pool of workers, and associate an amount of work (in seconds) with
		# each nodes.
		
		# find and append root nodes
		nodes = self.build_nodes(work_offset=60)
		worker_pool = WorkerPool(5)
		
		input_queue = [n for n in nodes.values() if n.ready()]
		print("found %d root node(s): %s" % (len(input_queue), ", ".join(str(n) for n in input_queue)))
		
		result = ""
		while len(input_queue) > 0 or (not worker_pool.is_empty()):
			input_queue = sorted(input_queue, key=lambda n: n.name)
			input_queue = worker_pool.fill(input_queue)
			
			finished_nodes = worker_pool.tick()
			
			for finished_node in finished_nodes:
				result += finished_node.name
				for succ in finished_node.followed_by:
					if succ.ready():
						input_queue.append(succ)
		
		print("pool took %d ticks to complete all nodes" % worker_pool.ticks_taken)
		return result

if __name__ == "__main__":
	day = Day7("day7.txt")
	print(day.part1())
	print(day.part2())