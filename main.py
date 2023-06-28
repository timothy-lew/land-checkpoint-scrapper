import re
import requests
from datetime import datetime
import os
import subprocess
import configparser
import pytz
from PIL import Image, ImageDraw, ImageFont

# Singapore time
utc_time = datetime.utcnow()
utc_plus_eight = pytz.timezone('Etc/GMT-8')
formatted_datetime = utc_time.replace(tzinfo=pytz.utc).astimezone(utc_plus_eight).strftime("%Y-%m-%d-%H_%M")
this_folder = os.path.dirname(os.path.abspath(__file__))

# read from config file
config = configparser.ConfigParser()
config_file = os.path.join(this_folder, 'config.txt')
config.read(config_file)

def scrape():
    # get path of config.txt

    endpoint = config.get('LTA', 'endpoint')
    grep = config.get('LTA', 'grep')

    # create the directory if it not exist
    os.makedirs(f"{this_folder}/outputs/{formatted_datetime}", exist_ok=True)  

    # curl to output.txt
    command = f"curl {endpoint} | grep '{grep}' > {this_folder}/outputs/{formatted_datetime}/output.txt"

    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        output = result.stdout
        print(output)
    else:
        error = result.stderr
        print(f"Command failed with error: {error}")

def downloadImage(url, directory_path, filename):
    response = requests.get(url)
    if response.status_code == 200:
        file_path = os.path.join(directory_path, filename)
        with open(file_path, 'wb') as file:
            file.write(response.content)
            print("Image downloaded successfully!")
        return file_path
    else:
        print("Failed to download the image.")

# write date updated to png file
def writeDate(file_path, text):
    image = Image.open(file_path)
    draw = ImageDraw.Draw(image)

    # set font and font size
    font_type = config.get('Local', 'font')
    font = ImageFont.truetype(font_type, 100)

    # Define the text position
    position = (50, 50)

    text_color = (255, 255, 255)  # White color
    draw.text(position, text, font=font, fill=text_color)

    image.save(file_path)


if __name__ == "__main__":
    # scrape data
    scrape()
    sources = []
    dates = []

    pattern_image = r'src=["\']([^"\']+)["\']'
    pattern_date = r'<span class="left">(\w{3} \w{3} \d{1,2} \d{2}:\d{2}:\d{2} \w{3} \d{4})</span>'

    # read output file after scrapping
    with open(f"{this_folder}/outputs/{formatted_datetime}/output.txt", 'r') as file:
        for line in file:
            line = line.strip()  # Remove leading/trailing whitespaces and newline characters
            match = re.search(pattern_image, line)
            if match:
                sources.append(match.group(1))
            match = re.search(pattern_date, line)
            if match:
                dates.append(match.group(1))

    # regex to filter sources
    count = 0
    names = ["tuas-jb-sg", "tuas-sg-jb", "cw-jb-sg", "cw-sg-jb"]
    print(dates)
    for source in sources:
        file_path = downloadImage(f"https:{source}", f"{this_folder}/outputs/{formatted_datetime}", f"{names[count]}.png")
        writeDate(file_path, dates[count])
        count += 1

