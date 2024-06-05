import plotly.graph_objects as go
import os
import re
import csv
import datetime
from pathlib import Path

def exclude_percentiles_and_average(total_nodes_list):
    sorted_nodes = sorted(total_nodes_list)
    
    num_nodes = len(sorted_nodes)
    if num_nodes < 20:  # Adjusted to ensure there are enough data points to exclude 5% from both ends
        print("Not enough data to exclude 5% from both ends.")
        return None
    
    cut_off = int(0.05 * num_nodes)  # Change from 0.15 to 0.05 for 5% exclusion
    reduced_list = sorted_nodes[cut_off:-cut_off]
    
    if reduced_list:
        average_nodes = sum(reduced_list) / len(reduced_list)
        return average_nodes
    else:
        print("No data left after exclusion.")
        return None

def log_data(timestamp, average_nodes):
    log_file_path = os.path.expanduser('~/node_data.csv')
    file_exists = Path(log_file_path).exists()
    try:
        with open(log_file_path, 'a', newline='') as csvfile:
            fieldnames = ['timestamp', 'average_nodes']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow({'timestamp': timestamp, 'average_nodes': average_nodes})
        print(f"Data logged to {log_file_path}")
    except Exception as e:
        print(f"Error writing to CSV: {e}")

def read_logged_data():
    log_file_path = os.path.expanduser('~/node_data.csv')
    timestamps = []
    averages = []
    try:
        with open(log_file_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                timestamps.append(datetime.datetime.fromisoformat(row['timestamp']))
                averages.append(float(row['average_nodes']))
    except FileNotFoundError:
        print("No data file found. Ensure logging has occurred.")
    except Exception as e:
        print(f"Error reading data: {e}")
    return timestamps, averages

def calculate_total_nodes(kbucket_data):
    buckets = re.findall(r'\((\d+), (\d+), (\d+)\)', kbucket_data)
    
    nodes_in_non_full_buckets = 0
    num_of_full_buckets = 0
    
    for depth, nodes, capacity in buckets:
        nodes = int(nodes)
        if nodes == 20:
            num_of_full_buckets += 1
        else:
            nodes_in_non_full_buckets += nodes

    total_nodes_including_self = nodes_in_non_full_buckets + 1
    total_nodes = total_nodes_including_self * (2 ** num_of_full_buckets)

    return total_nodes

def get_latest_kbucket_data(log_file):
    try:
        with open(log_file, 'r') as file:
            lines = file.readlines()[-2000:]
        for line in reversed(lines):
            if "kBucketTable" in line:
                return line.strip()
    except Exception as e:
        print(f"Error reading log file: {e}")
    return None

def read_node_data(filepath):
    with open(filepath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        node_values = [float(row['average_nodes']) for row in reader]
    return min(node_values), max(node_values), node_values[-1]

def plot_current_node_count_as_gauge(current_value, min_value, max_value):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = current_value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Node Count", 'font': {'size': 24, 'color': 'white'}},
        gauge = {
            'axis': {'range': [None, max_value], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "deepskyblue"},
            'bgcolor': "black",
            'borderwidth': 2,
            'bordercolor': "white",
            'steps': [
                {'range': [0, min_value], 'color': 'yellow'},
                {'range': [min_value, current_value], 'color': 'yellow'},
                {'range': [current_value, max_value], 'color': 'gray'}
            ],
            'threshold': {
                'line': {'color': "gray", 'width': 4},
                'thickness': 0.75,
                'value': max_value
            }
        }
    ))

    fig.update_layout(paper_bgcolor = "black", font = {'color': "white", 'family': "Arial"})
    fig.write_image("average_nodes_over_time.png")

def time_line():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def main(node_base_path):
    node_base_path = os.path.expanduser(node_base_path)
    if not os.path.exists(node_base_path):
        print(f"Node base path does not exist: {node_base_path}")
        return

    node_dirs = [d for d in os.listdir(node_base_path) if os.path.isdir(os.path.join(node_base_path, d))]
    total_nodes_list = []
    for node_dir in node_dirs:
        log_path = os.path.join(node_base_path, node_dir, 'safenode.log')
        if os.path.exists(log_path):
            kbucket_data = get_latest_kbucket_data(log_path)
            if kbucket_data:
                total_nodes = calculate_total_nodes(kbucket_data)
                total_nodes_list.append(total_nodes)
            else:
                print(f"Log file not found for node: {node_dir}")

    if total_nodes_list:
        average_nodes = exclude_percentiles_and_average(total_nodes_list)
        if average_nodes is not None:
            timestamp = time_line() 
            log_data(timestamp, average_nodes)
            print(f"Average total nodes across nodes, excluding the top and bottom 5%: {average_nodes:.2f}")
            plot_current_node_count_as_gauge(average_nodes, 0, 20000)
        else:
            print("Insufficient data after excluding top and bottom 5%.")
    else:
        print("No node data found to calculate.")

if __name__ == "__main__":
    node_base_path = '/var/log/safenode/'
    main(node_base_path)
