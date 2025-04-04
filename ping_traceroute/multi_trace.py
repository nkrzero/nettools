import os
import subprocess
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import re

# Create output directory if it doesn't exist
output_dir = "./traceroute_output"
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

# Function to extract IPs from traceroute output
def extract_ips(output):
    ip_pattern = r'\d+\.\d+\.\d+\.\d+'
    ips = re.findall(ip_pattern, output)
    seen = set()
    unique_ips = [ip for ip in ips if not (ip in seen or seen.add(ip))]
    return unique_ips

# Function to perform traceroute on an IP and write to file with real-time timing
def trace_ip(ip, filename):
    print(f"Running traceroute to {ip}")
    
    if os.name == 'nt':  # Windows
        command = ['tracert', '-d', ip]
    else:  # Linux/Mac
        command = ['traceroute', '-n', ip]
    
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        start_time = time.time()
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        output_lines = []
        hop_count = 0
        
        # Read output line by line in real-time
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line.strip():
                elapsed_seconds = round(time.time() - start_time, 1)
                stripped_line = line.strip()
                
                # Check if it's a hop line (starts with a number)
                if re.match(r'^\s*\d+', stripped_line):
                    hop_count += 1
                    output_lines.append(f"[{elapsed_seconds}s] {stripped_line}")
                # Handle header and completion lines
                elif not output_lines or "Tracing route" in stripped_line:
                    output_lines.append(stripped_line)
                elif "Trace complete" in stripped_line:
                    total_time = round((time.time() - start_time) * 1000)
                    output_lines.append(f"Trace complete - Total time: {total_time}ms")
        
        end_time = time.time()
        total_time = round((end_time - start_time) * 1000)  # Convert to ms
        
        # Get any error output
        stderr = process.stderr.read().strip()
        
        if process.returncode == 0:
            output = '\n'.join(output_lines)
            ips = extract_ips(output)
            file_content = f"{timestamp} - {ip} - SUCCESS\n{output}"
            console_summary = f"{timestamp} - {ip} - SUCCESS - {hop_count} hops - took {total_time}ms - Path: {' -> '.join(ips)}"
        else:
            output = '\n'.join(output_lines) + (f"\n{stderr}" if stderr else "")
            file_content = f"{timestamp} - {ip} - FAILED\n{output}\nTrace failed - Total time: {total_time}ms"
            console_summary = f"{timestamp} - {ip} - FAILED - took {total_time}ms"
        
        with open(filename, 'a') as f:
            f.write(file_content + '\n\n')
        
        print(console_summary)
        
    except subprocess.TimeoutExpired as e:
        total_time = round((time.time() - start_time) * 1000)
        output = '\n'.join(output_lines) + f"\n[{total_time/1000:.1f}s] Process timed out"
        ips = extract_ips(output)
        file_content = f"{timestamp} - {ip} - TIMEOUT\n{output}\nTrace timed out - Total time: {total_time}ms"
        console_summary = f"{timestamp} - {ip} - TIMEOUT - took {total_time}ms - Partial Path: {' -> '.join(ips)}" if ips else f"{timestamp} - {ip} - TIMEOUT - took {total_time}ms"
        with open(filename, 'a') as f:
            f.write(file_content + '\n\n')
        print(console_summary)
    except Exception as e:
        total_time = round((time.time() - start_time) * 1000)
        file_content = f"{timestamp} - {ip} - ERROR - {str(e)}\nTrace failed - Total time: {total_time}ms"
        console_summary = f"{timestamp} - {ip} - ERROR - took {total_time}ms"
        with open(filename, 'a') as f:
            f.write(file_content + '\n\n')
        print(console_summary)

# Main execution
def main():
    ip_list = read_ip_list('destinationip.txt')
    
    if not ip_list:
        print("No IP addresses to trace!")
        return
    
    # Get execution timestamp with month name
    now = datetime.now()
    month_name = now.strftime('%B')
    execution_timestamp = now.strftime(f'%Y_{month_name}_%d_%H_%M')
    
    print(f"Starting simultaneous traceroute monitoring for {len(ip_list)} IP addresses...")
    print(f"Output files will be saved in {output_dir}/ with timestamp {execution_timestamp}")
    
    # Use ThreadPoolExecutor to limit concurrent threads
    max_threads = len(ip_list) * 2
    executor = ThreadPoolExecutor(max_workers=max_threads)
    
    try:
        next_cycle_time = time.time()
        while True:
            for ip in ip_list:
                filename = f"{output_dir}/trace_{ip.replace('.', '_')}_{execution_timestamp}.log"
                executor.submit(trace_ip, ip, filename)
            
            next_cycle_time += 45
            sleep_time = next_cycle_time - time.time()
            if sleep_time > 0:
                print(f"Next cycle in {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
            else:
                print("Cycle running late, starting next immediately...")
            
    except KeyboardInterrupt:
        print("\nTraceroute monitoring stopped by user.")
        executor.shutdown(wait=False)
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        executor.shutdown(wait=False)
    finally:
        executor.shutdown(wait=True)

if __name__ == "__main__":
    main()