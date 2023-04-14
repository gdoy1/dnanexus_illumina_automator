# Developed by George
# 14/02/2023

# Script designed to check Q30 and error rate exceed minimum threshold before launching pipeline

from interop import py_interop_run_metrics, py_interop_run, py_interop_summary, py_interop_plot, py_interop_table
from decimal import Decimal, getcontext
import io
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import sys
import sqlite3
import xml.etree.ElementTree as ET

def check_rta_complete(output_dir):
    """Check if RTA has completed through RTAComplete.txt."""
    return os.path.exists(os.path.join(output_dir, "RTAComplete.txt"))

def load_run_metrics(run_folder):
    """Load the run metrics from the InterOp files."""
    run_metrics = py_interop_run_metrics.run_metrics()
    valid_to_load = py_interop_run.uchar_vector(py_interop_run.MetricCount, 0)
    py_interop_run_metrics.list_summary_metrics_to_load(valid_to_load)
    run_metrics.read(run_folder, valid_to_load)
    return run_metrics

def update_run_metrics(run_id, q30, error_rate, yield_g, pct_pf_clusters, cluster_density, qscore_histogram, scatter_plot, flowcell, instrument, side):
    '''Updates the run_metrics table in the SQLite database with the provided data.'''
    conn = sqlite3.connect("db/pipemanager.db")
    cursor = conn.cursor()

    cursor.execute("INSERT OR REPLACE INTO run_metrics (run_id, q30, error_rate, yield, cluster_pf, cluster_density, qscore_histogram, scatter_plot, flowcell, instrument, side) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (run_id, q30, error_rate, yield_g, pct_pf_clusters, cluster_density, qscore_histogram, scatter_plot, flowcell, instrument, side))
    conn.commit()
    conn.close()

def generate_summary(run_metrics):
    """Create summary object and populate it from the run metrics."""
    summary = py_interop_summary.run_summary()
    py_interop_summary.summarize_run_metrics(run_metrics, summary)
    return summary

def get_total_summary(summary):
    """Return the total_summary object from the summary."""
    return summary.total_summary()

def get_total_density(summary):
    """Calculate the mean density of all lanes."""
    total_density = 0
    total_lanes = summary.lane_count()
    for lane in range(total_lanes):
        total_density += summary.at(0).at(lane).density().mean()
    mean_density = total_density / total_lanes
    return mean_density

def generate_qscore_histogram(run_folder, run_id):
    '''Generates and saves a Q-score histogram plot as a PNG image in the static output folder.'''
    run_metrics = py_interop_run_metrics.run_metrics()
    valid_to_load = py_interop_run.uchar_vector(py_interop_run.MetricCount, 0)
    valid_to_load[py_interop_run.Q] = 1
    run_metrics.read(run_folder, valid_to_load)
    bar_data = py_interop_plot.bar_plot_data()
    boundary = 30
    options = py_interop_plot.filter_options(run_metrics.run_info().flowcell().naming_method())
    py_interop_plot.plot_qscore_histogram(run_metrics, options, bar_data, boundary)

    for i in range(bar_data.size()):
        x = [bar_data.at(i).at(j).x() for j in range(bar_data.at(i).size())]
        y = [bar_data.at(i).at(j).y() for j in range(bar_data.at(i).size())]
        w = [bar_data.at(i).at(j).width() for j in range(bar_data.at(i).size())]
        plt.bar(x, y, width=w, color=bar_data.at(i).color())
    
    plt.xlabel(bar_data.xyaxes().x().label(), fontsize=10)
    plt.ylabel(bar_data.xyaxes().y().label(), fontsize=10)
    plt.title(bar_data.title(), fontsize=10)
    plt.ylim([bar_data.xyaxes().y().min(), bar_data.xyaxes().y().max()])
    plt.xlim([bar_data.xyaxes().x().min(), bar_data.xyaxes().x().max()])

    # Save the Q-score histogram as a PNG image in the output folder
    output_folder = "static/qscore_histograms"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    output_file = os.path.join(output_folder, f'qscore_histogram_{run_id}.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    return output_file

def generate_scatter_plot(data_occupied, data_pf, run_id):
    '''Generates and saves a scatter plot of % Occupied vs % Pass Filter as a PNG image in the output folder.'''
    fig, ax = plt.subplots()
    ax.scatter(data_occupied, data_pf, s=8, c='darkblue')

    ax.set_xlabel('% Occupied')
    ax.set_ylabel('% Pass Filter')
    ax.set_title('Scatter plot: % Occupied vs % Pass Filter')

    ax.set_xlim(70, 110)
    ax.set_ylim(30, 90)
    ax.grid(True, linewidth=0.5, zorder=-10)

    correlation_coefficient = np.corrcoef(data_occupied, data_pf)[0, 1]
    if correlation_coefficient > 0 and np.max(data_occupied) < 90:
        status = 'Underloaded'
    elif correlation_coefficient > 0 and np.max(data_occupied) >= 90:
        status = 'Optimally Loaded'
    else:
        status = 'Overloaded'

    plt.text(0.05, 0.95, f'Estimation: {status}', transform=ax.transAxes, fontsize=6, verticalalignment='top')

    output_folder = "static/scatter_plots"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    output_file = os.path.join(output_folder, f'scatter_plot_{run_id}.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    return output_file

def extract_data_for_scatter_plot(run_folder):
    '''Extracts the data for the scatter plot from the InterOp files.'''
    run_metrics = py_interop_run_metrics.run_metrics()
    valid_to_load = py_interop_run.uchar_vector(py_interop_run.MetricCount, 0)
    py_interop_table.list_imaging_table_metrics_to_load(valid_to_load)
    run_metrics.read(run_folder, valid_to_load)

    columns = py_interop_table.imaging_column_vector()
    py_interop_table.create_imaging_table_columns(run_metrics, columns)
    headers = []
    for i in range(columns.size()):
        column = columns[i]
        if column.has_children():
            headers.extend([column.name()+"("+subname+")" for subname in column.subcolumns()])
        else:
            headers.append(column.name())

    column_count = py_interop_table.count_table_columns(columns)
    row_offsets = py_interop_table.map_id_offset()
    py_interop_table.count_table_rows(run_metrics, row_offsets)
    data = np.zeros((row_offsets.size(), column_count), dtype=np.float32)
    py_interop_table.populate_imaging_table_data(run_metrics, columns, row_offsets, data.ravel())

    d = []
    for col, label in enumerate(headers):
        d.append((label, pd.Series([val for val in data[:, col]], index=[tuple(r) for r in data[:, :3]])))
    df = pd.DataFrame.from_dict(dict(d))

    first_cycle_df = df.loc[df['Cycle'] == 1.0]
    data_pf = first_cycle_df['% Pass Filter'].values
    data_occupied = first_cycle_df['% Occupied'].values

    return data_occupied, data_pf

def main():
    output_dir = sys.argv[1]
    run_id = int(sys.argv[3])

    if not check_rta_complete(output_dir):
        print("RTAComplete.txt not found in output directory. Aborting...")
        sys.exit(1)

    run_folder = output_dir
    run_metrics = load_run_metrics(run_folder)
    summary = generate_summary(run_metrics)
    total_summary = get_total_summary(summary)

    average_q30 = total_summary.percent_gt_q30()
    average_error_rate = total_summary.error_rate()
    yield_g = total_summary.yield_g()
    pct_pf_clusters = (total_summary.cluster_count_pf() / total_summary.cluster_count()) * 100
    mean_density = get_total_density(summary)
    qscore_histogram = generate_qscore_histogram(run_folder, run_id)

    data_occupied, data_pf = extract_data_for_scatter_plot(run_folder)
    scatter_plot = generate_scatter_plot(data_occupied, data_pf, run_id)

    # Console prints
    print("Average Q30: {:.2f}%".format(average_q30))
    print("Average Error Rate: {:.2f}%".format(average_error_rate))
    print("Yield: {:.2f} Gb".format(yield_g))
    print("Clusters Passing Filter: {:.2f}%".format(pct_pf_clusters))
    print("Density (K/mm2): {:.2f}".format(mean_density / 1000))

    # Parse the RunInfo.xml file
    tree = ET.parse(os.path.join(run_folder, 'RunInfo.xml'))
    root = tree.getroot()
    flowcell = root.find('Run/Flowcell').text
    instrument = root.find('Run/Instrument').text

    # Parse the RunParameters.xml file
    tree = ET.parse(os.path.join(run_folder, 'RunParameters.xml'))
    root = tree.getroot()
    side = root.find('Side').text

    # Update the run_metrics table with all the scraped information
    update_run_metrics(run_id, average_q30, average_error_rate, yield_g, pct_pf_clusters, mean_density/1000, qscore_histogram, scatter_plot, flowcell, instrument, side)

if __name__ == "__main__":
    main()