import os
import subprocess
import sys
import time
import re

def generate_qr_code(url):
    try:
        import qrcode
        from PIL import Image

        qr = qrcode.QRCode(version=1, box_size=5, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code to a file
        img.save("expo_qr_code.png")
        print("QR code saved as expo_qr_code.png")
        
        # Display ASCII QR code in the console
        qr.print_tty()
        print(f"\nExpo URL: {url}")
    except ImportError as e:
        print(f"Error: Unable to generate QR code. {str(e)}")
        print("Please make sure 'qrcode' and 'pillow' libraries are installed.")
        print(f"Expo URL: {url}")
    except Exception as e:
        print(f"Error: Failed to generate QR code. {str(e)}")
        print(f"Expo URL: {url}")

def check_file_watcher_limit():
    try:
        with open("/proc/sys/fs/inotify/max_user_watches", "r") as f:
            current_limit = int(f.read().strip())
        return current_limit
    except Exception as e:
        print(f"Error checking file watcher limit: {str(e)}")
        return None

def run_project():
    try:
        os.chdir("happyhouse")
        
        # Check file watcher limit
        current_limit = check_file_watcher_limit()
        if current_limit is not None and current_limit < 524288:
            print("Warning: File watcher limit is low. This may cause issues with Expo.")
            print("Consider increasing the limit if you encounter problems.")
        
        print("Starting Expo development server for mobile...")
        
        env = os.environ.copy()
        env['CI'] = '1'  # Set CI environment variable to disable watch mode
        
        process = subprocess.Popen(
            ["npx", "expo", "start", "--port", "19000", "--no-dev", "--minify"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1,
            env=env
        )
        
        start_time = time.time()
        url_pattern = re.compile(r'(exp://.*:\d+)')
        url_found = False
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
                url_match = url_pattern.search(output)
                if url_match and not url_found:
                    url = url_match.group(1)
                    print(f"Expo development server is running on {url}")
                    print("To run on a physical device, scan the QR code with the Expo Go app")
                    generate_qr_code(url)
                    url_found = True
                elif "Starting project" in output:
                    print("Expo is starting, waiting for URL information...")
            
            if time.time() - start_time > 300:  # 5 minutes timeout
                print("Timeout: Expo development server did not provide URL information within 5 minutes.")
                break
            
            if time.time() - start_time > 60 and (int(time.time() - start_time) % 30 == 0):
                print(f"Still waiting for URL information... ({int((time.time() - start_time) / 60)} minutes elapsed)")
        
        if not url_found:
            print("Error: Expo development server failed to provide URL information.")
            print("Checking for error messages...")
            
            error_output = process.stderr.read()
            if error_output:
                print("Error output:")
                print(error_output)
            
            if process.returncode is not None and process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, process.args)
        
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        sys.exit(1)

def main():
    run_project()

if __name__ == "__main__":
    main()
