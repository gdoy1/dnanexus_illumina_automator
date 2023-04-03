# Developed by George
# 14/02/2023

# Script designed to check Q30 and error rate exceed minimum threshold before launching pipeline

from interop import py_interop_run_metrics, py_interop_run, py_interop_summary
import os
import numpy as np
import sys
import sqlite3

def check_rta_complete(output_dir):
    """Check if RTA has completed through RTAComplete.txt."""
    return os.path.exists(os.path.join(output_dir, "RTAComplete.txt"))

def load_run_metrics(run_folder):
    """Load the run metrics from the InterOp files."""
    run_metrics = py_interop_run_metrics.run_metrics()
    run_metrics.read(run_folder)
    return run_metrics

def update_run_metrics(run_id, q30, error_rate, yield_g, pct_pf_clusters):
    conn = sqlite3.connect("db/pipemanager.db")
    cursor = conn.cursor()

    cursor.execute("INSERT OR REPLACE INTO run_metrics (run_id, q30, error_rate, yield, cluster_pf) VALUES (?, ?, ?, ?, ?)", (run_id, q30, error_rate, yield_g, pct_pf_clusters))
    conn.commit()
    conn.close()

def generate_summary(run_metrics):
    """Create summary object and populate it from the run metrics."""
    summary = py_interop_summary.run_summary()
    py_interop_summary.summarize_run_metrics(run_metrics, summary)
    return summary

def calculate_average_q30_and_error_rate(summary):
    """Calculate the average Q30 and error rate from the summary."""
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

    return average_q30, average_error_rate

def calculate_yield_and_pct_pf_clusters(summary):
    """Calculate the yield and percent of clusters passing filter from the summary."""
    yield_total = 0
    clusters_total = 0
    pf_clusters_total = 0

    for i in range(summary.size()):
        read_summary = summary.at(i)
        for j in range(read_summary.size()):
            lane_summary = read_summary.at(j)
            if lane_summary.yield_g() is not None:
                yield_total += lane_summary.yield_g()
            if lane_summary.cluster_count() is not None:
                clusters_total += lane_summary.cluster_count().mean()
            if lane_summary.percent_pf() is not None and lane_summary.cluster_count() is not None:
                pf_clusters_total += (lane_summary.percent_pf().mean() / 100) * lane_summary.cluster_count().mean()

    pct_pf_clusters = (pf_clusters_total / clusters_total) * 100 if clusters_total > 0 else 0
    yield_g = yield_total

    return yield_g, pct_pf_clusters

def main():
    output_dir = sys.argv[1]
    run_id = int(sys.argv[3])

    if not check_rta_complete(output_dir):
        print("RTAComplete.txt not found in output directory. Aborting...")
        sys.exit(1)

    run_folder = output_dir
    run_metrics = load_run_metrics(run_folder)
    summary = generate_summary(run_metrics)
    average_q30, average_error_rate = calculate_average_q30_and_error_rate(summary)
    yield_g, pct_pf_clusters = calculate_yield_and_pct_pf_clusters(summary)

    print("Average Q30: {:.2f}%".format(average_q30))
    print("Average Error Rate: {:.2f}%".format(average_error_rate))
    print("Yield: {:.2f} Gb".format(yield_g))
    print("Clusters Passing Filter: {:.2f}%".format(pct_pf_clusters))

    update_run_metrics(run_id, average_q30, average_error_rate, yield_g, pct_pf_clusters)

if __name__ == "__main__":
    main()