import os
import subprocess
import sys
import time
import re
import psutil
import socket
import math
import logging
import shutil

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port(start_port, end_port):
    for port in range(start_port, end_port + 1):
        if not is_port_in_use(port):
            return port
    return None

def increase_file_watchers_limit():
    try:
        import resource
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        current = soft
        step = 16384  # Increase by 16384 at a time
        while current < hard:
            current = min(current + step, hard)
            try:
                resource.setrlimit(resource.RLIMIT_NOFILE, (current, hard))
                logging.info(f"Increased file watchers limit to {current}")
                return True
            except ValueError:
                pass
        logging.warning(f"Could not increase file watchers limit beyond {soft}")
        return False
    except Exception as e:
        logging.error(f"Failed to increase file watchers limit: {str(e)}")
        return False

def generate_qr_code(url):
    try:
        import qrcode
        from PIL import Image

        qr = qrcode.QRCode(version=1, box_size=5, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        img.save("expo_qr_code.png")
        logging.info("QR code saved as expo_qr_code.png")
        
        qr.print_tty()
        logging.info(f"Expo URL: {url}")
    except ImportError as e:
        logging.error(f"Error: Unable to generate QR code. {str(e)}")
        logging.info("Please make sure 'qrcode' and 'pillow' libraries are installed.")
        logging.info(f"Expo URL: {url}")
    except Exception as e:
        logging.error(f"Error: Failed to generate QR code. {str(e)}")
        logging.info(f"Expo URL: {url}")

def check_disk_space(path, required_space_gb=1):
    total, used, free = shutil.disk_usage(path)
    free_space_gb = free // (2**30)
    if free_space_gb < required_space_gb:
        logging.warning(f"Low disk space: {free_space_gb}GB free. At least {required_space_gb}GB recommended.")
        return False
    return True

def check_system_resources():
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_percent = psutil.virtual_memory().percent
    
    if cpu_percent > 80:
        logging.warning(f"High CPU usage: {cpu_percent}%. This may affect Expo server performance.")
    if memory_percent > 80:
        logging.warning(f"High memory usage: {memory_percent}%. This may affect Expo server performance.")
    
    return cpu_percent < 90 and memory_percent < 90

def check_common_issues():
    issues = []
    
    if is_port_in_use(19000):
        issues.append("Port 19000 is already in use. We'll try to find an available port.")
    
    try:
        subprocess.run(["npm", "list", "expo", "react", "react-native"], 
                       stdout=subprocess.DEVNULL, 
                       stderr=subprocess.DEVNULL, 
                       check=True)
    except subprocess.CalledProcessError:
        issues.append("Some required dependencies (expo, react, react-native) may be missing. Please run 'npm install' in the project directory.")
    
    if not check_disk_space("."):
        issues.append("Low disk space detected. This may cause issues with Metro bundler.")
    
    if not check_system_resources():
        issues.append("System resources (CPU or memory) are running low. This may affect Expo server performance.")

    return issues

def run_project(max_retries=5):
    for attempt in range(max_retries):
        try:
            os.chdir("happyhouse")
            
            logging.info(f"Starting Expo development server for mobile (Attempt {attempt + 1}/{max_retries})...")
            
            common_issues = check_common_issues()
            if common_issues:
                logging.warning("Found potential issues:")
                for issue in common_issues:
                    logging.warning(f"- {issue}")
            
            if not increase_file_watchers_limit():
                logging.warning("Could not increase file watchers limit. This may cause issues.")
            
            port = find_available_port(19000, 19100)
            if not port:
                raise RuntimeError("Unable to find an available port between 19000 and 19100.")
            
            process = subprocess.Popen(
                ["npx", "expo", "start", "--port", str(port), "--max-workers", "2"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            start_time = time.time()
            url_pattern = re.compile(r'(exp://.*:\d+)')
            url_found = False
            timeout_duration = 1800  # 30 minutes timeout
            progress_interval = 30  # Show progress every 30 seconds
            
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    logging.info(output.strip())
                    url_match = url_pattern.search(output)
                    if url_match and not url_found:
                        url = url_match.group(1)
                        logging.info(f"Expo development server is running on {url}")
                        logging.info("To run on a physical device, scan the QR code with the Expo Go app")
                        generate_qr_code(url)
                        url_found = True
                    elif "Starting project" in output:
                        logging.info("Expo is starting, waiting for URL information...")
                    elif "Building JavaScript bundle" in output:
                        logging.info("Building JavaScript bundle...")
                
                error_output = process.stderr.readline()
                if error_output:
                    logging.error(f"Error: {error_output.strip()}")
                    if "ENOSPC" in error_output:
                        logging.error("File watcher limit reached. Attempting to increase the limit...")
                        if increase_file_watchers_limit():
                            logging.info("File watcher limit increased. Restarting Expo...")
                            return run_project(max_retries - 1)
                    elif "Cannot find module" in error_output:
                        logging.error("Missing module. Try running 'npm install' in the project directory.")
                        subprocess.run(["npm", "install"], check=True)
                        logging.info("Dependencies installed. Restarting Expo...")
                        return run_project(max_retries - 1)
                    elif "Metro Bundler process exited" in error_output:
                        logging.error("Metro Bundler process exited unexpectedly. This might be due to system resource constraints.")
                        if check_system_resources():
                            logging.info("System resources look okay. Restarting Expo...")
                            return run_project(max_retries - 1)
                
                elapsed_time = time.time() - start_time
                if elapsed_time > timeout_duration:
                    raise TimeoutError(f"Timeout: Expo development server did not provide URL information within {timeout_duration // 60} minutes.")
                
                if int(elapsed_time) % progress_interval == 0:
                    logging.info(f"Still waiting for URL information... ({int(elapsed_time // 60)} minutes {int(elapsed_time % 60)} seconds elapsed)")
            
            if not url_found:
                raise RuntimeError("Expo development server failed to provide URL information.")
            
            return  # Success, exit the retry loop
            
        except (TimeoutError, RuntimeError, subprocess.CalledProcessError) as e:
            logging.error(f"Error: {str(e)}")
            backoff_time = min(30 * (2 ** attempt), 300)  # Exponential backoff with max 5 minutes
            logging.info(f"Attempt {attempt + 1} failed. Retrying in {backoff_time} seconds...")
            time.sleep(backoff_time)
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            logging.error("Stack trace:", exc_info=True)
            backoff_time = min(30 * (2 ** attempt), 300)  # Exponential backoff with max 5 minutes
            logging.info(f"Attempt {attempt + 1} failed. Retrying in {backoff_time} seconds...")
            time.sleep(backoff_time)
    
    logging.error("All retry attempts failed. Please check the logs for more information.")
    print_error_output(process)
    sys.exit(1)

def print_error_output(process):
    if process is None:
        logging.error("No process information available.")
        return

    error_output = process.stderr.read()
    if error_output:
        logging.error("Error output:")
        logging.error(error_output)
    else:
        logging.info("No error output found.")
    
    logging.info("\nMetro bundler logs:")
    try:
        with open(os.path.join("happyhouse", "metro-logs.txt"), "r") as log_file:
            logging.info(log_file.read())
    except FileNotFoundError:
        logging.error("Metro bundler log file not found.")

def main():
    run_project()

if __name__ == "__main__":
    main()
