import os
import paramiko
import time
from datetime import datetime
from getpass import getpass

# Create base output directory if it doesn't exist
base_output_dir = "./output"
if not os.path.exists(base_output_dir):
    os.makedirs(base_output_dir)

# Read IP addresses from deviceip.txt
def read_ip_list(filename):
    try:
        with open(filename, 'r', encoding='utf-8-sig') as file:
            return [ip.strip().replace('\ufeff', '') for ip in file.readlines() if ip.strip()]
    except FileNotFoundError:
        print(f"Error: {filename} not found!")
        return []

# Read commands from commands.txt
def read_commands(filename):
    try:
        with open(filename, 'r', encoding='utf-8-sig') as file:
            return [cmd.strip().replace('\ufeff', '') for cmd in file.readlines() if cmd.strip()]
    except FileNotFoundError:
        print(f"Error: {filename} not found!")
        return []

# Function to execute a single SSH command and save output
def execute_single_command(ip, username, password, command, device_dir):
    print(f"Executing '{command}' on {ip}")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(ip, username=username, password=password, timeout=10)
        stdin, stdout, stderr = ssh.exec_command(command, timeout=30)
        
        output = stdout.read().decode('utf-8').strip()
        error = stderr.read().decode('utf-8').strip()
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        file_content = f"Timestamp: {timestamp}\nCommand: {command}\n"
        if output:
            file_content += f"Output:\n{output}\n"
        if error:
            file_content += f"Error:\n{error}\n"
        
        command_safe = command.replace(' ', '_').replace('/', '_')
        filename = os.path.join(device_dir, f"{ip.replace('.', '_')}_{command_safe}.txt")
        with open(filename, 'w') as f:
            f.write(file_content)
        
        print(f"Completed '{command}' on {ip} - Output saved to {filename}")
    
    except paramiko.AuthenticationException as e:
        print(f"Authentication failed for {ip}: {str(e)}")
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        filename = os.path.join(device_dir, f"{ip.replace('.', '_')}_auth_error.txt")
        with open(filename, 'w') as f:
            f.write(f"Timestamp: {timestamp}\nError: Authentication failed - {str(e)}")
    except Exception as e:
        print(f"Failed to execute '{command}' on {ip}: {str(e)}")
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        filename = os.path.join(device_dir, f"{ip.replace('.', '_')}_{command_safe}_error.txt")
        with open(filename, 'w') as f:
            f.write(f"Timestamp: {timestamp}\nCommand: {command}\nError: {str(e)}")
    finally:
        ssh.close()

# Function to process all commands for a device
def execute_ssh_commands(ip, username, password, commands, output_dir):
    print(f"Processing {ip}...")
    device_dir = os.path.join(output_dir, f"device_ip_{ip.replace('.', '_')}")
    if not os.path.exists(device_dir):
        os.makedirs(device_dir)
    
    for command in commands:
        execute_single_command(ip, username, password, command, device_dir)

# Main execution
def main():
    username = input("Enter SSH username: ")
    password = getpass("Enter SSH password: ")
    
    ip_list = read_ip_list('deviceip.txt')
    commands = read_commands('commands.txt')
    
    if not ip_list:
        print("No IP addresses to process!")
        return
    if not commands:
        print("No commands to execute!")
        return
    
    now = datetime.now()
    month_name = now.strftime('%B')
    execution_timestamp = now.strftime(f'%Y_{month_name}_%d_%H_%M')
    output_dir = os.path.join(base_output_dir, execution_timestamp)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"Starting SSH command execution for {len(ip_list)} devices...")
    print(f"Output will be saved in {output_dir}")
    
    for ip in ip_list:
        execute_ssh_commands(ip, username, password, commands, output_dir)
    
    print("Command execution completed for all devices.")

if __name__ == "__main__":
    main()