## SENF (Statistical EvaluatioN of Fuzzers)

SENF is a statistical evaluation framework to compare the performance of an arbitrary set of fuzzers on a set of test programs. SENF has been used in an extensive evaluation to quantify the influence of different evaluation parameters, e.g, the run-time or number of trials. Given a SQLite database which contains the experiment results, SENF calculates the p-value (using interval-scaled and dichotomous tests) and standardized effect sizes comparing each fuzzer on every target. Additionally, SENF calculates a ranking which compares the overall performance of the tested fuzzers.

Our paper about SENF will be published at [ESORICS 2021](https://esorics2021.athene-center.de/). The final authenticated version is available online at https://doi.org/TBA. An extended version of this paper is available on [arXiv](https://arxiv.org/abs/2108.07076).

### Required packages:
* [R-Project](https://www.r-project.org/) (has to be in `PATH`)
* [python3](https://www.python.org/)
* [scipy](https://www.scipy.org/)

### Usage

* `result_data.db` is a SQLite3 database that contains the raw data of our experiments, i.e., the time it took each fuzzer to find the bug on each target on each run.
* The `evaldata.py` file contains the list of seeds, targets, and fuzzers that should be considered in the evaluation.
* To run statistical evaluation execute `statistical_comparison.py`.
* To calculate rankings run `calc_scores.py`.
* Per default SENF calculates the statistical evaluation an ranking for all targets, seeds, and fuzzers with 24h run-time, a p threshold of 0.05 without any effect size thresholds. Note that you can adjust all these parameters. Execute each script with `--help` for more information.
* You can find the result databases (statistical test and ranking) for the default parameters in `results_default/`.
* To enable reproducability of our experiments we provide all used seed files in `seeds/`.


### Evaluating fuzzers with SENF

* Simply provide a SQLite database with the provided SQLite SCHEMA:
```
CREATE TABLE "results" (
	`e_id`	INTEGER,
	`fuzzer`	TEXT,
	`target`	TEXT,
	`seed`	TEXT,
	`run1`	INTEGER,
	`run2`	INTEGER,
	`run3`	INTEGER,
	`run4`	INTEGER,
	`run5`	INTEGER,
	`run6`	INTEGER,
	`run7`	INTEGER,
	`run8`	INTEGER,
	`run9`	INTEGER,
	`run10`	INTEGER,
	`run11`	INTEGER,
	`run12`	INTEGER,
	`run13`	INTEGER,
	`run14`	INTEGER,
	`run15`	INTEGER,
	`run16`	INTEGER,
	`run17`	INTEGER,
	`run18`	INTEGER,
	`run19`	INTEGER,
	`run20`	INTEGER,
	`run21`	INTEGER,
	`run22`	INTEGER,
	`run23`	INTEGER,
	`run24`	INTEGER,
	`run25`	INTEGER,
	`run26`	INTEGER,
	`run27`	INTEGER,
	`run28`	INTEGER,
	`run29`	INTEGER,
	`run30`	INTEGER,
	PRIMARY KEY(`e_id`)
)
```
* `e_id` is a unique identifier. `fuzzer` contains the name of the tested fuzzer. `target` is a unique identifier for the bug the fuzzer should be able to find. `seed` is an identifier for the used seed set. The `run` fields contain the time it took each fuzzer to detect the respective bug.
* Adjust the values in `evaldata.py` which should contain the name of all fuzzers, targets, and seed-sets that should be used in the evaluation. Next, you can run the evaluation as described above.


### Other use cases

You can use SENF to evaluate any number of fuzzers on any test set. If you want to use code coverage as an evaluation metric you can simply replace the time it took the fuzzer until it found a specific bug with the time it took the fuzzer to find an input which triggers a certain code location.
