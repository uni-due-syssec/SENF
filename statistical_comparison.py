import sqlite3
import os
import subprocess
import re
import evaldata
import argparse

class Result():
	def __init__(self, e_id, fuzzer, target, seed, crashes_found=0, runs=[]):
		self.e_id = e_id
		self.fuzzer = fuzzer
		self.target = target
		self.seed = seed
		self.crashes_found = crashes_found
		self.runs = runs

	def print_result(self):
		print("e_id:", self.e_id)
		print("fuzzer:", self.fuzzer)
		print("target:", self.target)
		print("seed:", self.seed)
		print("crashes_found:", self.crashes_found)
		print("runs ("+str(len(self.runs))+"):", self.runs)

def parse_values(string, value):
	result = None

	if "= " in string:
		result = string[2:]
	elif "< " in string:
		result = string[2:]
	else:
		raise ValueError

	if value == "p" and "NA" in string:
		result = "1"

	result = float(result)

	if value in ["p", "p_f"] and result > 1.0:
		raise ValueError

	return result


def get_R_stats(runs_a, runs_b, crashes_found_a, crashes_found_b):
	r_base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "R")
	r_template_path = os.path.join(r_base_path, "template.r")
	
	with open(r_template_path, "r") as fp:
		r_template = fp.read()

	r_template = r_template.replace("RUNTIMES_A", str(runs_a)[1:-1])
	r_template = r_template.replace("RUNTIMES_B", str(runs_b)[1:-1])
	r_template = r_template.replace("NUMBER_OF_RUNS", str(len(runs_a)))
	r_template = r_template.replace("NUMBER_OF_CRASHES_A", str(crashes_found_a))
	r_template = r_template.replace("NUMBER_OF_CRASHES_B", str(crashes_found_b))

	temp_path = os.path.join(r_base_path, "temp.r")
	with open(temp_path, "w") as fp:
		fp.write(r_template)

	command = ["Rscript", temp_path]
	process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=5)

	p = None
	p_f = None
	a12 = None
	or_ab = None

	try:
		p = re.findall(r"W = .*?, p-value ([=<] .*?)\n", process.stdout)[0]
		p = parse_values(p, "p")
	except (ValueError, IndexError, TypeError):
		raise ValueError
	try:
		p_f = re.findall(r"m\np-value ([=<] .*?)\n", process.stdout)[0]
		p_f = parse_values(p_f, "p_f")
	except (ValueError, IndexError, TypeError):
		raise ValueError
	try:
		a12 = re.findall(r"A12 (= .*?)\"\n", process.stdout)[0]
		a12 = parse_values(a12, "a12")
	except (ValueError, IndexError, TypeError):
		raise ValueError
	try:
		or_ab = re.findall(r"Odds ratio (= .*?)\"\n", process.stdout)[0]
		or_ab = parse_values(or_ab, "or_ab")
	except (ValueError, IndexError, TypeError):
		raise ValueError

	if (p is None or p_f is None or a12 is None or or_ab is None):
		raise ValueError

	return p, p_f, a12, or_ab

def calculate_statistics(base_fuzzer, max_runs, max_time, seed, targets, identifier=""):
	db_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), "result_data.db")
	conn = sqlite3.connect(db_name)
	c = conn.cursor()

	all_base_fuzzer_results = []

	temp_base_fuzzer_results = c.execute("SELECT * FROM results WHERE fuzzer = ? AND seed = ?", (base_fuzzer, seed)).fetchall()
	temp_base_fuzzer_results = [Result(entry[0], entry[1], entry[2], entry[3], runs=[x for x in entry[4:] if x is not None]) for entry in temp_base_fuzzer_results]

	for temp_result in temp_base_fuzzer_results:
		if temp_result.target in targets:
			all_base_fuzzer_results.append(temp_result)

	db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stat_dbs_"+identifier)
	if not os.path.isdir(db_dir):
		os.mkdir(db_dir)

	db_path_stats = os.path.join(db_dir, "stat_db_r_"+str(max_runs)+"_ta_"+str(len(targets))+"_ti_"+str(max_time)+"_"+seed+".db")

	conn_db_output = sqlite3.connect(db_path_stats)
	c_db_output = conn_db_output.cursor()
	c_db_output.execute("CREATE TABLE IF NOT EXISTS 'stats' ([id] INTEGER PRIMARY KEY,\
	[base_fuzzer] TEXT,\
	[compare_fuzzer] TEXT,\
	[target] TEXT,\
	[seed] TEXT,\
	[p_fet] TEXT,\
	[p_mwu] TEXT,\
	[odds_ratio] TEXT,\
	[a12] TEXT)")
	conn_db_output.commit()

	for base_fuzzer_result in all_base_fuzzer_results:
		temp_runs_a = []
		base_fuzzer_result.crashes_found = 0
		for run in base_fuzzer_result.runs:
			if run < max_time:
				base_fuzzer_result.crashes_found += 1
				temp_runs_a.append(run)
			else:
				temp_runs_a.append(max_time)
		base_fuzzer_result.runs = temp_runs_a

		compare_fuzzer_results = c.execute("SELECT * FROM results WHERE target = ? AND seed = ? AND NOT fuzzer = ? ORDER BY fuzzer",
									(base_fuzzer_result.target, base_fuzzer_result.seed, base_fuzzer_result.fuzzer)).fetchall()
		compare_fuzzer_results = [Result(entry[0], entry[1], entry[2], entry[3], runs=[x for x in entry[4:] if x is not None]) for entry in compare_fuzzer_results]

		for compare_fuzzer_result in compare_fuzzer_results:
			temp_runs_b = []
			compare_fuzzer_result.crashes_found = 0
			for run in compare_fuzzer_result.runs:
				if run < max_time:
					compare_fuzzer_result.crashes_found += 1
					temp_runs_b.append(run)
				else:
					temp_runs_b.append(max_time)
			compare_fuzzer_result.runs = temp_runs_b

			p_mwu, p_fet, a12, or_ab = get_R_stats(base_fuzzer_result.runs, compare_fuzzer_result.runs, base_fuzzer_result.crashes_found, compare_fuzzer_result.crashes_found)

			temp = c_db_output.execute("SELECT * FROM stats WHERE base_fuzzer = ? AND compare_fuzzer = ? AND target = ? AND seed = ?",
									   (base_fuzzer_result.fuzzer, compare_fuzzer_result.fuzzer, base_fuzzer_result.target, base_fuzzer_result.seed)).fetchall()
			if len(temp) < 1:
				c_db_output.execute("INSERT INTO stats VALUES (?,?,?,?,?,?,?,?,?)", (None, base_fuzzer_result.fuzzer, compare_fuzzer_result.fuzzer, base_fuzzer_result.target, base_fuzzer_result.seed, p_fet, p_mwu, or_ab, a12))
				conn_db_output.commit()

	conn.commit()
	c.close()
	conn.close()
	conn_db_output.commit()
	c_db_output.close()
	conn_db_output.close()
	print("Results stored in:", db_path_stats)


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("-m", "--max_runs", type = int, help="Set maximum number of runs used.")
	parser.add_argument("-t", "--max_time", type = int, help="Set maximum time.")
	parser.add_argument("-i", "--identifier", type = str, help="Set abitrary identifier.")
	args = parser.parse_args()
	
	fuzzers = evaldata.fuzzers

	max_runs = args.max_runs if args.max_runs else 30
	max_time = args.max_time if args.max_time else 86400
	identifier = args.identifier if args.identifier else ""
	seeds = evaldata.seeds
	db_path_stats = ""
	
	for fuzzer in fuzzers:
		for seed in seeds:
			print("Calculate stats for:\nfuzzer:", fuzzer, "\nseed:", seed)
			db_path_stats = calculate_statistics(fuzzer, max_runs, max_time, seed = seed, targets = evaldata.targets, identifier = identifier)

if __name__ == "__main__":
	main()