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

def run_project():
    try:
        os.chdir("happyhouse")
        
        print("Starting Expo development server for mobile...")
        
        process = subprocess.Popen(
            ["npx", "expo", "start", "--port", "19000", "--max-workers", "2"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        start_time = time.time()
        url_pattern = re.compile(r'(exp://.*:\d+)')
        url_found = False
        timeout_duration = 300  # 5 minutes timeout
        progress_interval = 30  # Show progress every 30 seconds
        
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
            
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_duration:
                raise TimeoutError(f"Timeout: Expo development server did not provide URL information within {timeout_duration // 60} minutes.")
            
            if int(elapsed_time) % progress_interval == 0:
                print(f"Still waiting for URL information... ({int(elapsed_time // 60)} minutes elapsed)")
        
        if not url_found:
            raise RuntimeError("Expo development server failed to provide URL information.")
        
    except TimeoutError as e:
        print(f"Error: {str(e)}")
        print("Possible reasons:")
        print("1. Slow internet connection")
        print("2. High system load")
        print("3. Insufficient system resources")
        print("Checking for error messages...")
        print_error_output(process)
        sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {str(e)}")
        print("Checking for error messages...")
        print_error_output(process)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error: Expo process exited with return code {e.returncode}")
        print("Checking for error messages...")
        print_error_output(process)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        print("Checking for error messages...")
        print_error_output(process)
        sys.exit(1)

def print_error_output(process):
    error_output = process.stderr.read()
    if error_output:
        print("Error output:")
        print(error_output)
    else:
        print("No error output found.")

def main():
    run_project()

if __name__ == "__main__":
    main()
