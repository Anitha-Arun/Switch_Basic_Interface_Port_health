from flask import Flask, render_template, request, jsonify
import subprocess
import os
import time
import re
import configparser
import glob
from datetime import datetime
import logging

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Configure logging to Switch_monitoring.log
LOG_DIR = r"D:\Switch Monitoring tool"
LOG_FILE = os.path.join(LOG_DIR, "Switch_monitoring.log")

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logger = logging.getLogger('SwitchMonitoring')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(LOG_FILE)
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

SYSTEM_SCRIPT_PATH = r"D:\Switch Monitoring tool\System_healthMetrics.py"
INTERFACE_SCRIPT_PATH = r"D:\Switch Monitoring tool\Interface_Porthealth_Metrics.py"
INVENTORY_PATH = r"D:\Switch Monitoring tool\inventory.ini"

def get_available_hosts():
    config = configparser.ConfigParser()
    config.read(INVENTORY_PATH)
    hosts = []
    ip_mapping = {}
    if 'switches' in config:
        for key in config['switches']:
            if key.startswith('host'):
                host_ip = config['switches'][key]
                hosts.append((key, host_ip))
                ip_mapping[key] = host_ip
    return hosts, ip_mapping

@app.route('/')
def index():
    hosts, ip_mapping = get_available_hosts()
    frontend_hosts = [{"id": host, "ip": ip_mapping[host], "label": f"Switch IP Address {i+1}"} for i, (host, _) in enumerate(hosts)]
    return render_template('index3.html', hosts=frontend_hosts)

@app.route('/interface')
def interface():
    hosts, ip_mapping = get_available_hosts()
    frontend_hosts = [{"id": host, "ip": ip_mapping[host], "label": f"Switch IP Address {i+1}"} for i, (host, _) in enumerate(hosts)]
    return render_template('interface.html', hosts=frontend_hosts)

@app.route('/run-script', methods=['POST'])
def run_system_script():
    try:
        selected_host = request.form.get('selected_host')
        selected_ip = request.form.get('selected_ip')
        if not selected_host or not selected_ip:
            return jsonify({"error": "No switch selected."}), 400

        logger.info(f"Running system script for host: {selected_host}, IP: {selected_ip}")
        process = subprocess.run(['python', SYSTEM_SCRIPT_PATH, selected_host], capture_output=True, text=True)
        if process.returncode != 0:
            logger.error(f"System script failed: {process.stderr}")
            return jsonify({"error": f"System script execution failed: {process.stderr}"}), 500

        timeout = 30
        start_time = time.time()
        date_str = time.strftime("%Y%m%d")
        file_pattern = os.path.join(LOG_DIR, f"basicinfo_{date_str}_*.txt")

        latest_file = None
        while time.time() - start_time < timeout:
            files = glob.glob(file_pattern)
            if files:
                latest_file = max(files, key=os.path.getctime)
                break
            time.sleep(1)

        if not latest_file:
            logger.error("Timeout: No matching basicinfo file found.")
            return jsonify({"error": "Timeout: No matching basicinfo file found."}), 500

        with open(latest_file, 'r') as file:
            data = file.read()
            parsed_data = parse_switch_report(data)
            parsed_data["Switch IP Address"] = selected_ip
            parsed_data["timestamp"] = datetime.now().strftime("%A, %B %d, %Y %I:%M:%S %p")

        logger.info("System data retrieved")
        return jsonify(parsed_data)

    except Exception as e:
        logger.exception(f"Exception in run_system_script: {str(e)}")
        return jsonify({"error": str(e), "details": "See server logs"}), 500

@app.route('/run-interface-script', methods=['POST'])
def run_interface_script():
    try:
        selected_host = request.form.get('selected_host')
        selected_ip = request.form.get('selected_ip')
        if not selected_host or not selected_ip:
            logger.warning("No switch selected in run_interface_script")
            return jsonify({"error": "No switch selected."}), 400

        logger.info(f"Running interface script for host: {selected_host}, IP: {selected_ip}")
        process = subprocess.run(['python', INTERFACE_SCRIPT_PATH, selected_host], capture_output=True, text=True)
        if process.returncode != 0:
            logger.error(f"Interface script failed: {process.stderr}")
            return jsonify({"error": f"Interface script execution failed: {process.stderr}"}), 500

        timeout = 30
        start_time = time.time()
        date_str = time.strftime("%Y%m%d")
        file_pattern = os.path.join(LOG_DIR, f"interface_port_{date_str}_*.txt")

        latest_file = None
        while time.time() - start_time < timeout:
            files = glob.glob(file_pattern)
            if files:
                latest_file = max(files, key=os.path.getctime)
                logger.debug(f"Found interface file: {latest_file}")
                break
            time.sleep(1)

        if not latest_file:
            logger.error("Timeout: No matching interface_port file found.")
            return jsonify({"error": "Timeout: No matching interface_port file found."}), 500

        try:
            with open(latest_file, 'r') as file:
                file_contents = file.read()
            logger.info(f"Interface file contents (first 500 chars): {file_contents[:500]}")
            if not file_contents.strip():
                logger.warning("Interface file is empty")
                return jsonify({"error": "Interface file is empty"}), 500
        except IOError as e:
            logger.error(f"Failed to read interface file {latest_file}: {str(e)}")
            return jsonify({"error": f"Failed to read interface data: {str(e)}"}), 500

        interface_data = {
            "interface_result": file_contents,  # Keep raw data for static template
            "switch_ip": selected_ip,
            "timestamp": datetime.now().strftime("%A, %B %d, %Y %I:%M:%S %p")
        }
        # Optional: Add parsed data if you plan to use it later
        interface_data.update(parse_interface_report(file_contents))

        logger.info("Interface data retrieved successfully")
        return jsonify(interface_data)

    except Exception as e:
        logger.exception(f"Exception in run_interface_script: {str(e)}")
        return jsonify({"error": str(e), "details": "See server logs"}), 500
    
@app.route('/reset', methods=['POST'])
def reset_data():
    logger.info("Reset requested")
    return jsonify({"status": "reset"})

@app.route('/clear-logs', methods=['POST'])
def clear_logs():
    try:
        log_file = os.path.join(LOG_DIR, "Switch_monitoring.log")
        if os.path.exists(log_file):
            open(log_file, 'w').close()
        logger.info("Switch_monitoring.log cleared")
        return jsonify({"status": "logs cleared"})
    except Exception as e:
        logger.error(f"Failed to clear Switch_monitoring.log: {str(e)}")
        return jsonify({"error": str(e)}), 500

def parse_switch_report(data):
    sections = [
        "System Information",
        "Version Information",
        "Inventory Information",
        "CPU Utilization",
        "Power Supply Status",
        "Voice VLAN Information"
    ]
    parsed_data = {}
    for section in sections:
        match = re.search(fr'=== {section} ===(.*?)(?:\n===|$)', data, re.DOTALL)
        if match:
            parsed_data[section] = match.group(1).strip()
        else:
            parsed_data[section] = "No data found"
    return parsed_data

def parse_interface_report(data):
    sections = [
        "Port Status",
        "Speed & Duplex",
        "Port Flapping (Logs)",
        "Port Flapping (Interfaces)",
        "Output Drops"
    ]
    parsed_data = {}
    for section in sections:
        match = re.search(fr'=== {section} ===(.*?)(?:\n===|$)', data, re.DOTALL)
        if match:
            parsed_data[section] = match.group(1).strip()
        else:
            parsed_data[section] = "No data found"
    return parsed_data

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')