from flask import Flask, render_template, request, session, redirect, url_for
from datetime import timedelta
import folium
from selenium import webdriver
import os
import time
import openai

import numpy as np
import matplotlib.pyplot as plt
from skimage.segmentation import clear_border
from skimage import measure
from skimage.measure import label,regionprops
from scipy import ndimage as ndi
from scipy.ndimage import measurements, center_of_mass, binary_dilation, zoom
import plotly.graph_objects as go
from PIL import Image

# -----------------------------------------------------------------------------------------------------------------

api_key = "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"
openai.api_key = api_key

context = "You are now a virtual assistant who helps people resolve their problems while using an app. The app's name is \"VeggieTools\"\n" \
          "The app in question aims to provide users with a simple and effective way to help do biome restoration work without needing to be too complicated.\n" \
          "One of the most common questions will be about how to get started. Respond with the following:\n" \
          "Here's how to get started:\n" \
          "1. Go to the projects tab and create a project.\n" \
          "2. Add objects to your workspace i.e. maps and data analyzers.\n" \
          "3. Use the AI powered tools in the toolbar to assist with the planning and execution of your project\n"\
          "4. Once you have completed your project, you can share it with the community or export it for further use.\n" \
          "Do NOT break character!!\n\n\n"

global conversation
conversation = context

def converse(message):
    prompt = message
    global conversation
    conversation += prompt + "\n"


    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=conversation,
        temperature=0,
        max_tokens=128,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )

    print(response["choices"][0]["text"])
    conversation += response["choices"][0]["text"] + "\n"

    return response["choices"][0]["text"] + "\n"

# -----------------------------------------------------------------------------------------------------------------

app = Flask(__name__, static_folder="assets")
app.secret_key = "hello"
app.permanent_session_lifetime = timedelta(minutes=5)

count = 1


@app.route('/')
@app.route('/home')
def index():
    session.clear()
    return render_template('index.html')


@app.route("/projects")
def about():
    session.clear()
    return render_template("projects.html")


@app.route("/help", methods=["POST", "GET"])
def help():

    if request.method == "POST":
        if request.form["submitButton"] == "clear":
            session.clear()
            return render_template("help.html")

        if request.form["submitButton"] == "submit":
            text = request.form["nm"]
            if "history" in session:
                if session["history"] is None:
                    response = converse(text)
                    session["history"] = text + " \n " + response
                else:
                    response = converse(text)
                    session["history"] = session["history"] + " \n " + text + " \n " + response
            else:
                response = converse(text)
                session["history"] = text + " \n " + response

            # Convert to Good Looking stuff
            new = session["history"].split(" \n ")


            return render_template("help.html", text=new)

    else:
        return render_template("help.html")



def getImage(lat, lon):
    global count
    count += 1

    mapObj = folium.Map(location=[lat, lon],
                        zoom_start=20)

    tile = folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri Satellite',
        overlay=False,
        control=True
        ).add_to(mapObj)


    # save the map as html
    mapFname = 'output.html'
    tile.save(mapFname)

    mapUrl = 'file://{0}/{1}'.format(os.getcwd(), mapFname)

    # download gecko driver for firefox from here - https://github.com/mozilla/geckodriver/releases

    # use selenium to save the html as png image
    driver = webdriver.Firefox()
    driver.get(mapUrl)
    # wait for 5 seconds for the maps and other assets to be loaded in the browser
    time.sleep(10)
    driver.save_screenshot(f'assets/img/mapImages/output{str(count)}.png')
    driver.quit()

    return str(count)


@app.route("/placeholder", methods=['POST', 'GET'])
def placeholder():
    if request.method == "POST":
        lat = int(request.form["lat"])
        lon = int(request.form["lon"])

        # Get Image
        image = getImage(lat, lon)

        img = np.asarray(Image.open(f"assets/img/mapImages/output{image}.png"))[:, :, 0]
        img = np.flip(img, 0)
        mask = img < 55
        plt.figure(figsize=(8, 8))
        plt.pcolormesh(mask)
        plt.colorbar()
        plt.savefig(f"assets/img/segmented/segmented{image}.jpg")

        return redirect(url_for("mapShow", mapImg=image))
    else:
        return render_template("placeholder.html")


@app.route("/<mapImg>")
def mapShow(mapImg):
    print("hello")
    print(mapImg)


    return render_template("customMap.html", mapImg=mapImg)

if __name__ == '__main__':
    app.run()
