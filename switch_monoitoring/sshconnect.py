import paramiko
import time
import logging
import sys

# Log file path
log_file_path = "Switch_monitoring.log"

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(log_file_path, mode='w'),
                        logging.StreamHandler(sys.stdout)
                    ])

# Redirect standard output and error to the log file
class LoggerWriter:
    def __init__(self, log_func):
        self.log_func = log_func

    def write(self, message):
        if message.strip():
            self.log_func(message.strip())

    def flush(self):
        pass

sys.stdout = LoggerWriter(logger.info)
sys.stderr = LoggerWriter(logger.error)

class CustomSSHClient(paramiko.SSHClient):
    def _auth(self, username, password, *args, **kwargs):
        try:
            self._transport.auth_none(username)
        except paramiko.BadAuthenticationType as e:
            logger.info(f"Allowed authentication types: {e.allowed_types}")
            if 'publickey' in e.allowed_types:
                logger.info("Attempting public key authentication")
                self._transport.auth_publickey(username, paramiko.RSAKey.generate(2048))
            if 'password' in e.allowed_types:
                logger.info("Attempting password authentication")
                self._transport.auth_password(username, password)
            if not self._transport.is_authenticated():
                raise

def ssh_connect(host, username, password):
    try:
        ssh_client = CustomSSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connection_params = {
            'hostname': host,
            'username': username,
            'password': password,
            'look_for_keys': True,
            'allow_agent': True,
            'disabled_algorithms': {
                'kex': ['diffie-hellman-group1-sha1', 'diffie-hellman-group14-sha1'],
                'mac': ['hmac-sha1']
            },
            'timeout': 15
        }
        logger.info(f"Attempting to connect to {host} with username {username}")
        ssh_client.connect(**connection_params)
        channel = ssh_client.invoke_shell()
        channel.settimeout(20)
        logger.info(f"Successfully connected to {host}")
        return ssh_client, channel
    except Exception as e:
        logger.error(f"Connection error for {host}: {e}")
        print(f"Connection error for {host}: {e}")
        return None, None

def send_command(channel, command, wait_time=5, expected_prompts=None):
    try:
        logger.info(f"Sending command: {command}")
        channel.send(command + '\n')
        output = ""
        
        # Wait for initial response
        time.sleep(wait_time)
        
        # Buffer output until no more data or prompt is received
        end_time = time.time() + 10  # Max 10 seconds additional wait
        while time.time() < end_time:
            if channel.recv_ready():
                chunk = channel.recv(4096).decode('utf-8', errors='ignore')
                output += chunk
                # Reset timeout if we got data
                end_time = time.time() + 2
            if 'More:' in output:
                before_more = output.split('More:')[0]
                output = before_more
                channel.send(' ')
                time.sleep(1)
                continue
            if expected_prompts:
                for prompt in expected_prompts:
                    if prompt['text'] in output:
                        logger.info(f"Responding to prompt: {prompt['text']}")
                        channel.send(prompt['response'] + '\n')
                        time.sleep(1)
                        output = ""  # Clear output after prompt response
                        end_time = time.time() + 10  # Reset timeout
                        break
            # Check for command prompt (assuming '#' or '>' indicates end)
            if output.strip().endswith(('#', '>')):
                break
            time.sleep(0.5)  # Small delay to avoid busy-waiting
        
        logger.info(f"Full command output: {output}")
        return output
    except Exception as e:
        logger.error(f"Error sending command: {e}")
        return f"Error: {e}"