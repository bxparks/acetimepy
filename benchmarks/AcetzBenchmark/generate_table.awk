#!/usr/bin/gawk -f
#
# Usage: generate_table.awk < benchmark.txt
#
# Takes the *.txt file generated by benchmark.py and generates an ASCII
# table that can be inserted into the README.md.

BEGIN {
  # Set to 1 when 'START' is detected
  collect_start = 0

  # Set to 1 when 'BENCHMARKS' is detected
  collect_benchmarks = 0
}

/^START/ {
  collect_start = 1
  collect_benchmarks = 0
  sizeof_start = 0
  next
}

/^BENCHMARKS/ {
  collect_start = 0
  collect_benchmarks = 1
  benchmark_index = 0
  next
}

!/^END/ {
  if (collect_start) {
    s[start_index] = $0
    start_index++
  }
  if (collect_benchmarks) {
    u[benchmark_index]["name"] = $1
    u[benchmark_index]["count1"] = $2
    u[benchmark_index]["micros1"] = $3
    u[benchmark_index]["count2"] = $4
    u[benchmark_index]["micros2"] = $5
    benchmark_index++
  }
}

END {
  TOTAL_BENCHMARKS = benchmark_index
  TOTAL_START = start_index

  printf("+-------------------+----------------+----------------+\n")
  printf("| Time Zone Library | comp to epoch  | epoch to comp  |\n")
  printf("|                   | (micros/iter)  | (micros/iter)  |\n")

  for (i = 0; i < TOTAL_BENCHMARKS; i++) {
    name = u[i]["name"]
    if (name ~ /^acetz/) {
      printf(\
         "|-------------------+----------------+----------------|\n")
    }
    printf("| %-17s | %14.3f | %14.3f |\n",
        name, u[i]["micros1"], u[i]["micros2"])
  }
  printf("+-------------------+----------------+----------------+\n")
}