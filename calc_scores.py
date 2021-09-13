import os
import sqlite3
import argparse
from scipy.stats import rankdata
from copy import deepcopy
from itertools import combinations
from statistics import mean

def float_conversion(string):
	if string == "-":
		return -1
	else:
		return float(string)

class TargetResult:
	def __init__(self, base_fuzzer, compare_fuzzer, target, seed, p_fet, p_mwu, odds_ratio, a12):
		self.base_fuzzer = base_fuzzer
		self.compare_fuzzer = compare_fuzzer
		self.target = target
		self.seed = seed
		self.p_mwu = float_conversion(p_mwu)
		self.p_fet = float_conversion(p_fet)
		self.odds_ratio = float_conversion(odds_ratio)
		self.a12 = float_conversion(a12)

	def print_result(self):
		print("base_fuzzer", self.base_fuzzer)
		print("compare_fuzzer", self.compare_fuzzer)
		print("target", self.target)
		print("seed", self.seed)
		print("p_mwu", self.p_mwu)
		print("p_fet", self.p_fet)
		print("odds_ratio", self.odds_ratio)
		print("a12", self.a12)

def read_data(db_path):
	results = []

	conn = sqlite3.connect(db_path)
	c = conn.cursor()
	data = c.execute("SELECT * FROM stats").fetchall()

	for entry in data:
		temp = TargetResult(*(entry[1:]))
		results.append(temp)

	c.close()
	conn.close()
	return results

def get_stats(pair, target, seed, results):
	fuzzer_a, fuzzer_b = pair
	for entry in results:
		if entry.base_fuzzer == fuzzer_a and entry.compare_fuzzer == fuzzer_b and entry.target == target and entry.seed == seed:
			return entry

	raise LookupError

def get_ranking(scores):
	ranks = deepcopy(scores)
	temp = rankdata([-1 * i for i in list(scores.values())], method="average")
	i = 0
	for key in ranks.keys():
		ranks[key] = temp[i]
		i += 1

	return ranks

def get_rank_id(c, seed, stat, max_runs, max_targets, max_time, threshold_p, threshold_odds_ratio_1, threshold_odds_ratio_2, threshold_a12_1, threshold_a12_2):
	try:
		result_id = c.execute("SELECT id FROM ranking WHERE seed = ? AND stat = ? AND max_runs = ? AND max_targets = ? AND max_time = ? AND "
										  "p_threshold = ? AND or_threshold_1 = ? AND or_threshold_2 = ? AND a12_threshold_1 = ? AND a12_threshold_2 = ?",
										  (seed, stat, max_runs, max_targets, max_time, threshold_p, threshold_odds_ratio_1, threshold_odds_ratio_2,
										   threshold_a12_1, threshold_a12_2)).fetchone()[0]
	except (IndexError, TypeError):
		result_id = None

	return result_id

def calculate_ranking(db_path, db_result_path, threshold_p, threshold_odds_ratio_1, threshold_odds_ratio_2, threshold_a12_1, threshold_a12_2):
	
	print("Calculate ranking for db:", db_path)
	all_target_results = read_data(db_path)
	fuzzers = []
	targets = []
	seed = all_target_results[0].seed

	for result in all_target_results:
		if result.base_fuzzer not in fuzzers:
			fuzzers.append(result.base_fuzzer)
		if result.target not in targets:
			targets.append(result.target)
	
	max_targets = len(targets)
	foo = os.path.basename(db_path).split("_")
	max_runs = int(foo[3])
	max_time = int(foo[7])
	
	pairs = list(combinations(fuzzers, 2))
	result_stat_db_path = db_result_path
	result_stat_conn = sqlite3.connect(result_stat_db_path)
	result_stat_c = result_stat_conn.cursor()

	result_stat_c.execute("CREATE TABLE IF NOT EXISTS 'ranking' ([id] INTEGER PRIMARY KEY,\
	[seed] TEXT,\
	[stat] TEXT,\
	[max_runs] INTEGER,\
	[max_targets] INTEGER,\
	[target_set] TEXT,\
	[max_time] INTEGER,\
	[p_threshold] TEXT,\
	[or_threshold_1] TEXT,\
	[or_threshold_2] TEXT,\
	[a12_threshold_1] TEXT,\
	[a12_threshold_2] TEXT,\
	[fuzzer1] TEXT,\
	[avg_rank1] TEXT,\
	[fuzzer2] TEXT,\
	[avg_rank2] TEXT,\
	[fuzzer3] TEXT,\
	[avg_rank3] TEXT,\
	[fuzzer4] TEXT,\
	[avg_rank4] TEXT,\
	[fuzzer5] TEXT,\
	[avg_rank5] TEXT,\
	[fuzzer6] TEXT,\
	[avg_rank6] TEXT,\
	[fuzzer7] TEXT,\
	[avg_rank7] TEXT,\
	[fuzzer8] TEXT,\
	[avg_rank8] TEXT,\
	[fuzzer9] TEXT,\
	[avg_rank9] TEXT)")
	result_stat_conn.commit()

	all_ranks_mwu = {}
	for fuzzer in fuzzers:
		all_ranks_mwu[fuzzer] = []

	all_ranks_fet = {}
	for fuzzer in fuzzers:
		all_ranks_fet[fuzzer] = []

	for target in targets:
		score_mwu = {}
		for fuzzer in fuzzers:
			score_mwu[fuzzer] = 0

		score_fet = deepcopy(score_mwu)

		for pair in pairs:
			try:
				target_result = get_stats(pair, target, seed, all_target_results)
				if target_result.p_mwu < threshold_p:
					#If you use another evaluation metric (e.g., number of BB found) you can swap the decrease/increase
					if target_result.a12 < threshold_a12_1:
						score_mwu[pair[0]] += 1
						score_mwu[pair[1]] -= 1
					elif target_result.a12 > threshold_a12_2:
						score_mwu[pair[0]] -= 1
						score_mwu[pair[1]] += 1

				if target_result.p_fet < threshold_p:
					if target_result.odds_ratio > threshold_odds_ratio_1:
						score_fet[pair[0]] += 1
						score_fet[pair[1]] -= 1
					elif target_result.a12 < threshold_odds_ratio_2:
						score_fet[pair[0]] -= 1
						score_fet[pair[1]] += 1

			except (TypeError, AttributeError):
				print("Could not find statistical results for:", target, pair[0], pair[1])
				pass
	
		ranks_mwu = get_ranking(score_mwu)
		for key in ranks_mwu.keys():
			all_ranks_mwu[key].append(ranks_mwu[key])

		ranks_fet = get_ranking(score_fet)
		for key in ranks_fet.keys():
			all_ranks_fet[key].append(ranks_fet[key])

	avg_ranks_mwu = {}
	for key in all_ranks_mwu.keys():
		avg_ranks_mwu[key] = mean(all_ranks_mwu[key])

	avg_ranks_mwu = {k: v for k, v in sorted(avg_ranks_mwu.items(), key=lambda item: item[1])}

	result_id = get_rank_id(result_stat_c, seed, "interval scaled", max_runs, max_targets, max_time, threshold_p, threshold_odds_ratio_1, threshold_odds_ratio_2,
									   threshold_a12_1, threshold_a12_2)

	if not result_id:
		result_stat_c.execute("INSERT INTO ranking VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
						  (None, seed, "interval scaled", max_runs, max_targets, str(targets), max_time, threshold_p, threshold_odds_ratio_1,
						   threshold_odds_ratio_2, threshold_a12_1, threshold_a12_2) + 18 * (None,))
		result_id = get_rank_id(result_stat_c, seed, "interval scaled", max_runs, max_targets, max_time, threshold_p, threshold_odds_ratio_1, threshold_odds_ratio_2,
										   threshold_a12_1, threshold_a12_2)
		i = 1
		for key in avg_ranks_mwu.keys():
			result_stat_c.execute("UPDATE ranking SET fuzzer" + str(i) + " = ?, avg_rank"+str(i)+" = ? WHERE id = ?", (key, avg_ranks_mwu[key], result_id))
			i+=1

		result_stat_conn.commit()

	avg_ranks_fet = {}
	for key in all_ranks_fet.keys():
		avg_ranks_fet[key] = mean(all_ranks_fet[key])

	avg_ranks_fet = {k: v for k, v in sorted(avg_ranks_fet.items(), key=lambda item: item[1])}

	result_id = get_rank_id(result_stat_c, seed, "dichotomous", max_runs, max_targets, max_time, threshold_p, threshold_odds_ratio_1, threshold_odds_ratio_2,
									   threshold_a12_1, threshold_a12_2)

	if not result_id:
		result_stat_c.execute("INSERT INTO ranking VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
						  (None, seed, "dichotomous", max_runs, max_targets, str(targets), max_time, threshold_p, threshold_odds_ratio_1,
						   threshold_odds_ratio_2, threshold_a12_1, threshold_a12_2) + 18 * (None,))
		result_id = get_rank_id(result_stat_c, seed, "dichotomous", max_runs, max_targets, max_time, threshold_p, threshold_odds_ratio_1, threshold_odds_ratio_2,
									   threshold_a12_1, threshold_a12_2)

		i = 1
		for key in avg_ranks_fet.keys():
			result_stat_c.execute("UPDATE ranking SET fuzzer" + str(i) + " = ?, avg_rank" + str(i) + " = ? WHERE id = ?", (key, avg_ranks_fet[key], result_id))
			i += 1

		result_stat_conn.commit()

	result_stat_c.close()
	result_stat_conn.close()
	print("Results stored in:", db_result_path)

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("-i", "--identifier", type = str, help="Set abitrary identifier.")
	parser.add_argument("-p", "--threshold_p", type = float, help="Set p threshold.")
	parser.add_argument("--threshold_o1", type = float, help="Set threshold for odds ratio.")
	parser.add_argument("--threshold_o2", type = float, help="Set threshold for odds ratio.")
	parser.add_argument("--threshold_a1", type = float, help="Set threshold for A12 statistic.")
	parser.add_argument("--threshold_a2", type = float, help="Set threshold for A12 statistic.")
	args = parser.parse_args()
	
	identifier = args.identifier if args.identifier else ""
	db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stat_dbs_"+identifier)
	db_result_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scores_"+identifier+".db")
	all_rank_configs = []
	threshold_p = args.threshold_p if args.threshold_p else 0.05
	threshold_odds_ratio_1 = args.threshold_o1 if args.threshold_o1 else 1.0
	threshold_odds_ratio_2 = args.threshold_o2 if args.threshold_o2 else 1.0
	threshold_a12_1 = args.threshold_a1 if args.threshold_a1 else 0.5
	threshold_a12_2 = args.threshold_a2 if args.threshold_a2 else 0.5

	for db in os.listdir(db_path):
		calculate_ranking(os.path.join(db_path, db), db_result_path, threshold_p, threshold_odds_ratio_1, threshold_odds_ratio_2, threshold_a12_1, threshold_a12_2)

if __name__ == "__main__":
	main()