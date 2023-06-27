import re
import requests
from datetime import datetime
import os
import subprocess
import configparser
import pytz

# Singapore time
utc_time = datetime.utcnow()
utc_plus_eight = pytz.timezone('Etc/GMT-8')
formatted_datetime = utc_time.replace(tzinfo=pytz.utc).astimezone(utc_plus_eight).strftime("%Y-%m-%d-%H:%M:%S")
this_folder = os.path.dirname(os.path.abspath(__file__))

def scrape():
    # get path of config.txt
    config_file = os.path.join(this_folder, 'config.txt')

    # read from config file
    config = configparser.ConfigParser()
    config.read(config_file)
    endpoint = config.get('LTA', 'endpoint')
    grep = config.get('LTA', 'grep')

    # create the directory if it not exist
    os.makedirs(f"{this_folder}/outputs/{formatted_datetime}", exist_ok=True)  

    # curl to output.txt
    command = f"curl {endpoint} | grep {grep} > {this_folder}/outputs/{formatted_datetime}/output.txt"
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        output = result.stdout
        print(output)
    else:
        error = result.stderr
        print(f"Command failed with error: {error}")

def download_image(url, directory_path, filename):
    response = requests.get(url)
    if response.status_code == 200:
        file_path = os.path.join(directory_path, filename)
        with open(file_path, 'wb') as file:
            file.write(response.content)
            print("Image downloaded successfully!")
        return file_path
    else:
        print("Failed to download the image.")

if __name__ == "__main__":
    # scrape data
    scrape()
    sources = []

    pattern = r'src=["\']([^"\']+)["\']'

    # read output file after scrapping
    with open(f"{this_folder}/outputs/{formatted_datetime}/output.txt", 'r') as file:
        for line in file:
            line = line.strip()  # Remove leading/trailing whitespaces and newline characters
            match = re.search(pattern, line)
            if match:
                sources.append(match.group(1))

    # regex to filter sources
    count = 0
    for source in sources:
        file_path = download_image(f"https:{source}", f"{this_folder}/outputs/{formatted_datetime}", f"{formatted_datetime}-{count}.png")
        count += 1

