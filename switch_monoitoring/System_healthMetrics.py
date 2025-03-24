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

def monitor_switch_status(channel):
    """
    Monitor and collect various system and interface stats for the switch.
    """
    try:
        commands = [
            ('show version', 'Version Information'),
            ('show system', 'System Information'),
            ('show cpu utilization', 'CPU Utilization'),
            ('show power inline', 'Power Supply Status'),
            ('show inventory', 'Inventory Information'),
            ('show voice vlan', 'Voice VLAN Information')
        ]

        for command, section_title in commands:
            # Execute command and get output
            output = send_command(channel, command, wait_time=5)
            
            # Log output for debugging (only visible in log file)
            logger.debug(f"{command} output: {output}")
            
            # Print formatted output to console (only once)
            print(f"\n=== {section_title} ===")
            print(output)

    except Exception as e:
        logger.error(f"Error monitoring switch status: {e}")

def extract_switch_info(log_file):
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

    # Get current date for filename
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"basicinfo_{date_str}.txt"

    # Save extracted info to a file
    with open(output_file, "w") as f:
        f.write("SWITCH MONITORING REPORT\n")
        f.write("=======================\n\n")
        for section, lines in sections.items():
            f.write(f"\n=== {section} ===\n")
            for line in lines:
                f.write(line + "\n")

    print(f"Extracted data saved to {output_file}")
    return output_file  # Return filename for reference

def process_host(host_info):
    """
    Process a single host for system monitoring and status.
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
            
            # Monitor Switch Status
            monitor_switch_status(channel)
                
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

    selected_host = sys.argv[1]  # Get host from command-line argument
    host_info = read_inventory(selected_host)

    # Process the selected host
    process_host(host_info)

    # Extract relevant log info
    extract_switch_info("Switch_monitoring.log")

if __name__ == "__main__":
    main()