from __future__ import print_function,absolute_import
import sys, os, re
import arrow
from pprint import pprint

class Event(object):
	rex = re.compile(r"^\[([^\]]+)\] (.*)$")
	STARTS_SHIFT = 0
	FALLS_ASLEEP = 1
	WAKES_UP = 2
	
	def __init__(self, timestamp, event_type, guard_id=None):
		self.timestamp = timestamp
		self.event_type = event_type
		self.guard_id = guard_id
	
	def __str__(self):
		typestr = ("STARTS_SHIFT" if self.event_type == self.STARTS_SHIFT else \
		          ("FALLS_ASLEEP" if self.event_type == self.FALLS_ASLEEP else \
		          ("WAKES_UP"     if self.event_type == self.WAKES_UP     else "<INVALID>")))
		return "[%s] %s (guard=%s)" % (self.timestamp.format("YYYY-MM-DD HH:mm:ss ZZ"), typestr, self.guard_id)
	
	@classmethod
	def parse(cls, line):
		match = cls.rex.match(line)
		if not match: raise ValueError("bad input line: " + line)
		timestamp_str = match.group(1).strip()
		event_str = match.group(2).strip()
		
		ts = arrow.get(timestamp_str, "YYYY-MM-DD HH:mm")
		if event_str == "wakes up":
			return Event(ts, cls.WAKES_UP) # we don't know which guard yet, need to sort by timestamp first
		elif event_str == "falls asleep":
			return Event(ts, cls.FALLS_ASLEEP)
		else:
			prefix = "Guard #"
			assert event_str.startswith(prefix)
			event_str = event_str[len(prefix):]
			guard_id = int(event_str.split(" ")[0])
			
			return Event(ts, cls.STARTS_SHIFT, guard_id=guard_id)

class Guard(object):
	def __init__(self, id):
		self.id = id
		self.timelines = {} # date -> array of 60 ints, one for each minute (1 = awake, 0 = asleep)
	def record_event(self, event):
		assert event.event_type in [Event.FALLS_ASLEEP, Event.WAKES_UP]
		date_key = event.timestamp.format("MM-DD")
		minutes = int(event.timestamp.format("m"))
		
		timeline = self.timelines.get(date_key, [1]*60)
		if event.event_type == Event.FALLS_ASLEEP:
			timeline[minutes:] = [0]*(60-minutes)
		elif event.event_type == Event.WAKES_UP:
			timeline[minutes:] = [1]*(60-minutes)
		self.timelines[date_key] = timeline
	
	def __str__(self):
		result = "Guard #%d:\n" % (self.id,)
		for date_key, timeline in sorted(self.timelines.items(), key=lambda kv: kv[0]):
			result += "%s: %s\n" % (date_key, "".join(map(lambda b: ("." if b else "#"), timeline)))
		return result
	
	def __repr__(self):
		return str(self)
	
	def minutes_asleep(self):
		result = 0
		for timeline in self.timelines.values():
			result += sum([1-b for b in timeline])
		return result
	
	def sleepiest_minute(self):
		max = (None, 0)
		for m in range(0,60):
			days_asleep = len([TL for TL in self.timelines.values() if TL[m] == 0])
			if days_asleep > max[1]: max = (m, days_asleep)
		return max
		
class Day4(object):
	def __init__(self, input_file):
		events = []
		with open(input_file, "r") as f:
			for line in f.readlines():
				events.append(Event.parse(line.strip()))
		
		events = sorted(events, key=lambda e: e.timestamp)
		assert events[0].event_type == Event.STARTS_SHIFT
		
		guards = {}
		current = None
		for e in events:
			if e.event_type == Event.STARTS_SHIFT:
				current = guards.get(e.guard_id)
				if not current:
					current = Guard(e.guard_id)
					guards[e.guard_id] = current
				continue
			current.record_event(e)
		
		self.guards = guards

	def part1(self):
		sleepiest_guard = max(self.guards.values(), key=lambda g: g.minutes_asleep())
		sleepiest_minute = sleepiest_guard.sleepiest_minute()[0]
		return sleepiest_guard.id * sleepiest_minute
		
	def part2(self):
		max = (None, 0, 0)
		for guard in self.guards.values():
			sleepiest_minute, num_days = guard.sleepiest_minute()
			if num_days > max[1]: max = (guard, num_days, sleepiest_minute)
		return max[0].id * max[2]
		
if __name__ == "__main__":
	day = Day4("day4.txt")
	print(day.part1())
	print(day.part2())