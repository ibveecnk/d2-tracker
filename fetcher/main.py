
import os
import time
import requests
import cv2
import pytesseract
import numpy as np
import gif2numpy
import PIL
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

url = "https://www.hochschulsport.uni-mannheim.de/cgi/studio.cgi?size=20"
headers = {
    "accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "accept-encoding": "gzip, deflate, br",
    "Referer": "https://www.hochschulsport.uni-mannheim.de/angebote/aktueller_zeitraum_0/_D2_FitnessGym_Studiobelegung.html",
    "User-Agent":
"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

ORG = os.environ["INFLUX_ORG"]
BUCKET = os.environ["INFLUX_BUCKET"]
TOKEN = os.environ["INFLUX_TOKEN"]
URL = "http://influxdb:8086"
client = influxdb_client.InfluxDBClient(url=URL, token=TOKEN, org=ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

while True:
    x = requests.get(url, headers=headers)

    # save x as a gif file
    with open('image.gif', 'wb') as f:
        f.write(x.content)

    # convert gif to png
    gif = PIL.Image.open('image.gif')
    gif.save('image.png', format='PNG')

    # read png and process it
    image = cv2.imread("image.png")

    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    image = cv2.copyMakeBorder(image, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    cv2.imwrite("final_image.png", image)

    # extract text from the image
    text = pytesseract.image_to_string("final_image.png", lang='eng',config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789').strip()

    value = int(text)

    print("value:", value)

    # add to influxdb
    r = influxdb_client.Point("gym").field("people", value=value)
    write_api.write(bucket=BUCKET, record=r)

    time.sleep(15)