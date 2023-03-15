# Developed by George
# 14/02/2023

# Script designed to check Q30 and error rate exceed minimum threshold before launching pipeline

from interop import py_interop_run_metrics, py_interop_run, py_interop_summary
import os
import numpy as np
import sys

output_dir = sys.argv[1]

# Check RTA has completed
if not os.path.exists(os.path.join(output_dir, "RTAComplete.txt")):
    print("RTAComplete.txt not found in output directory. Aborting...")
    sys.exit(1)

# Set the path to the run folder
run_folder = output_dir

# Create a run metrics object and load the InterOp files
run_metrics = py_interop_run_metrics.run_metrics()
run_folder = run_metrics.read(run_folder)

# Create a summary object and populate it from the run metrics
summary = py_interop_summary.run_summary()
py_interop_summary.summarize_run_metrics(run_metrics, summary)

# Calculate the average Q30 and error rate
q30_total = 0
q30_count = 0
error_rate_total = 0
error_rate_count = 0
for i in range(summary.size()):
    read_summary = summary.at(i)
    for j in range(read_summary.size()):
        lane_summary = read_summary.at(j)
        if lane_summary.percent_gt_q30() is not None:
            q30_total += lane_summary.percent_gt_q30()
            q30_count += 1
        mean_error_rate = lane_summary.error_rate().mean()
        if not np.isnan(mean_error_rate):
            error_rate_total += mean_error_rate
            error_rate_count += 1

average_q30 = q30_total / q30_count
average_error_rate = error_rate_total / error_rate_count

if average_q30 >= 80 and average_error_rate < 2:
   with open(os.path.join(output_dir, "qc.pass"), "w") as f:
        f.write("Average Q30: {:.2f}%\n".format(average_q30))
        f.write("Average Error Rate: {:.2f}%\n".format(average_error_rate))
#else:
#    print('Fail')

# Print the average Q30 and error rate
print("Average Q30: {:.2f}%".format(average_q30))
print("Average Error Rate: {:.2f}%".format(average_error_rate))
