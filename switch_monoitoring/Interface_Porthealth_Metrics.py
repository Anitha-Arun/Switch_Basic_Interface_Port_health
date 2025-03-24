import configparser
import os
import sys
import datetime
import re
from sshconnect import ssh_connect, send_command, logger  # Import from sshconnect.py

INVENTORY_PATH = r"D:\Switch Monitoring tool\inventory.ini"

def read_inventory(selected_host):
    """
    Read connection details for a specific host from inventory.ini
    """
    config = configparser.ConfigParser()
    config.read(INVENTORY_PATH)

    section = 'switches'
    if section not in config:
        raise Exception(f"Section '{section}' not found in inventory.ini")

    if selected_host not in config[section]:
        raise Exception(f"{selected_host} not found in inventory.ini")

    return {
        'host': config[section][selected_host],
        'username': config[section].get('username', ''),
        'password': config[section].get('password', '')
    }

def get_gigabit_ports(channel):
    """
    Fetch the list of GigabitEthernet ports from 'show interface status'.
    """
    output = send_command(channel, "show interface status", wait_time=5)
    ports = []
    
    # Regular expression to match GigabitEthernet ports (e.g., Gi1, GigabitEthernet1)
    port_pattern = re.compile(r'^(Gi|GigabitEthernet)\d+', re.IGNORECASE)
    
    for line in output.splitlines():
        match = port_pattern.search(line.strip())
        if match:
            port_name = match.group(0)
            # Normalize to 'GigabitEthernetX' format
            if port_name.startswith('Gi'):
                port_num = port_name[2:]
                port_name = f"GigabitEthernet{port_num}"
            ports.append(port_name)
    
    return ports

def monitor_interface_port_health(channel):
    """
    Monitor and collect interface and port health metrics for the switch.
    """
    try:
        # Base commands
        base_commands = [
            ('show interface status', 'Port Status'),
            ('show interfaces status', 'Speed & Duplex'),
            ('show log', 'Port Flapping (Logs)'),
            ('show interfaces', 'Port Flapping (Interfaces)'),
            ('show queue statistics', 'Output Drops')
        ]

        # Get all GigabitEthernet ports
        gigabit_ports = get_gigabit_ports(channel)
        logger.info(f"Detected GigabitEthernet ports: {gigabit_ports}")

        # Dynamic CRC error commands for each port
        crc_commands = [(f"show interfaces counters {port}", f"CRC Errors - {port}") for port in gigabit_ports]

        # Combine all commands
        commands = base_commands + crc_commands

        for command, section_title in commands:
            output = send_command(channel, command, wait_time=5)
            logger.debug(f"{command} output: {output}")
            print(f"\n=== {section_title} ===")
            print(output)

    except Exception as e:
        logger.error(f"Error monitoring interface port health: {e}")

def extract_interface_port_info(log_file):
    """
    Extract interface port health data from the log file and save to a text file.
    """
    sections = {}
    current_section = None
    
    with open(log_file, "r") as file:
        for line in file:
            section_match = re.search(r"=== (.*?) ===", line)
            if section_match:
                current_section = section_match.group(1)
                sections[current_section] = []
                continue
            
            if current_section:
                if "Sending command:" in line:
                    current_section = None
                else:
                    sections[current_section].append(line.strip())

    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"interface_port_{date_str}.txt"

    with open(output_file, "w") as f:
        f.write("INTERFACE PORT HEALTH REPORT\n")
        f.write("============================\n\n")
        for section, lines in sections.items():
            f.write(f"\n=== {section} ===\n")
            for line in lines:
                f.write(line + "\n")

    print(f"Extracted data saved to {output_file}")
    return output_file

def process_host(host_info):
    """
    Process a single host for interface and port health monitoring.
    """
    HOST = host_info['host']
    USERNAME = host_info['username']
    PASSWORD = host_info['password']

    print(f"\n===== Processing Host: {HOST} =====")
    
    ssh_client, channel = ssh_connect(HOST, USERNAME, PASSWORD)
    if ssh_client and channel:
        try:
            prompts = [{'text': 'User Name:', 'response': USERNAME},
                       {'text': 'Password:', 'response': PASSWORD}]
            
            print("Entering enable mode:")
            send_command(channel, 'enable', expected_prompts=prompts)
            
            monitor_interface_port_health(channel)
                
        except Exception as e:
            logger.error(f"Error processing {HOST}: {e}")
        finally:
            if ssh_client:
                ssh_client.close()
                logger.info(f"SSH connection to {HOST} closed.")
                print(f"SSH connection to {HOST} closed.")
    else:
        logger.error(f"Failed to establish SSH connection to {HOST}")

def main():
    if len(sys.argv) < 2:
        print("Error: No host selected. Run script with a host argument.")
        sys.exit(1)

    selected_host = sys.argv[1]
    host_info = read_inventory(selected_host)

    process_host(host_info)
    extract_interface_port_info("Switch_monitoring.log")

if __name__ == "__main__":
    main()