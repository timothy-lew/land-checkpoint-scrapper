import re
import requests
from datetime import datetime
import os
import subprocess
import configparser
import pytz
from PIL import Image, ImageDraw, ImageFont

# telegram bot
import asyncio
from telegram import Bot, InputMediaPhoto
from telegram.error import TelegramError

import shutil

# Singapore time
utc_time = datetime.utcnow()
utc_plus_eight = pytz.timezone('Etc/GMT-8')
formatted_datetime = utc_time.replace(tzinfo=pytz.utc).astimezone(utc_plus_eight).strftime("%Y-%m-%d-%H_%M")
this_folder = os.path.dirname(os.path.abspath(__file__))
output_directory = f"{this_folder}/outputs/{formatted_datetime}"

# read from config file
config = configparser.ConfigParser()

# get path of config.txt
config_file = os.path.join(this_folder, 'config.txt')
config.read(config_file)

def scrape():
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
    
    outline_color = (0, 0, 0)  # Black color
    outline_width = 6

    # Draw the text outline
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            draw.text((position[0] + dx, position[1] + dy), text, font=font, fill=outline_color)
        draw.text(position, text, font=font, fill=text_color)

    image.save(file_path)

async def sendImages(image_paths):
    bot_token = config.get('Telegram', 'bot_token')
    chat_id = config.get('Telegram', 'chat_id')

    bot = Bot(token=bot_token)
    try:
        media = [InputMediaPhoto(open(image_path, 'rb')) for image_path in image_paths]
        await bot.send_media_group(chat_id=chat_id, media=media)
    except TelegramError as e:
        print(f"Failed to send image: {e}")

def deleteDirectory(directory_path):
    try:
        shutil.rmtree(directory_path)
        print("Directory deleted successfully.")
    except OSError as e:
        print(f"Error occurred while deleting the directory: {e}")

if __name__ == "__main__":
    # scrape data
    scrape()
    sources = []
    dates = []

    # regex to filter sources and dates
    pattern_image = r'src=["\']([^"\']+)["\']'
    pattern_date = r'<span class="left">(\w{3} \w{3} \d{1,2} \d{2}:\d{2}:\d{2} \w{3} \d{4})</span>'

    # read output file after scrapping
    with open(f"{output_directory}/output.txt", 'r') as file:
        for line in file:
            line = line.strip()  # Remove leading/trailing whitespaces and newline characters
            match = re.search(pattern_image, line)
            if match:
                sources.append(match.group(1))
            match = re.search(pattern_date, line)
            if match:
                dates.append(match.group(1))

    count = 0
    names = ["tuas-jb-sg", "tuas-sg-jb", "cw-jb-sg", "cw-sg-jb"]
    print(dates)
    image_paths = []
    for source in sources:
        file_path = downloadImage(f"https:{source}", f"{output_directory}", f"{names[count]}.png")
        image_paths.append(file_path)
        writeDate(file_path, dates[count])
        count += 1

    asyncio.run(sendImages(image_paths))
    deleteDirectory(f"{output_directory}")
    