import os
import subprocess
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Create output directory if it doesn't exist
output_dir = "./ping_output"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Read IP addresses from destinationip.txt
def read_ip_list(filename):
    try:
        with open(filename, 'r', encoding='utf-8-sig') as file:
            return [ip.strip().replace('\ufeff', '') for ip in file.readlines() if ip.strip()]
    except FileNotFoundError:
        print(f"Error: {filename} not found!")
        return []

# Function to ping an IP and return result
def ping_ip(ip):
    param = '-n' if os.name == 'nt' else '-c'
    command = ['ping', param, '1', ip]
    
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        result = subprocess.run(command, stdout=subprocess.PIPE, text=True, timeout=2)  # Added timeout
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if 'time=' in output:
                time_ms = output.split('time=')[1].split('ms')[0].strip()
                return f"{timestamp} - {ip} - SUCCESS - {time_ms}ms"
            else:
                return f"{timestamp} - {ip} - SUCCESS - <time not parsed>"
        else:
            return f"{timestamp} - {ip} - FAILED - No response"
    except subprocess.TimeoutExpired:
        return f"{timestamp} - {ip} - FAILED - Timeout"
    except Exception as e:
        return f"{timestamp} - {ip} - ERROR - {str(e)}"

# Function to process results and write to files
def process_result(ip, result, output_dir, execution_timestamp):
    filename = f"{output_dir}/ping_{ip.replace('.', '_')}_{execution_timestamp}.log"
    with open(filename, 'a') as f:
        f.write(result + '\n')
    print(f"{result}")

# Main execution
def main():
    ip_list = read_ip_list('destinationip.txt')
    
    if not ip_list:
        print("No IP addresses to ping!")
        return
    
    # Get execution timestamp with month name
    now = datetime.now()
    month_name = now.strftime('%B')
    execution_timestamp = now.strftime(f'%Y_{month_name}_%d_%H_%M')
    
    print(f"Starting parallel ping monitoring for {len(ip_list)} IP addresses...")
    print(f"Output files will be saved in {output_dir}/ with timestamp {execution_timestamp}")
    
    try:
        while True:
            # Use ThreadPoolExecutor for parallel execution
            with ThreadPoolExecutor(max_workers=min(10, len(ip_list))) as executor:
                # Submit all ping tasks
                future_to_ip = {executor.submit(ping_ip, ip): ip for ip in ip_list}
                
                # Process results as they complete
                for future in as_completed(future_to_ip):
                    ip = future_to_ip[future]
                    try:
                        result = future.result()
                        process_result(ip, result, output_dir, execution_timestamp)
                    except Exception as e:
                        error_msg = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {ip} - ERROR - {str(e)}"
                        process_result(ip, error_msg, output_dir, execution_timestamp)
            
            time.sleep(1)  # Wait between batches
            
    except KeyboardInterrupt:
        print("\nPing monitoring stopped by user.")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")

if __name__ == "__main__":
    main()