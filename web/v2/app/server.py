import aiohttp
import asyncio
import uvicorn
from fastai import *
from fastai.vision import *
from torch import topk
from io import BytesIO
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, JSONResponse
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from PIL import Image
import urllib.request
import requests

export_file_url = 'https://www.dropbox.com/s/6bgq8t6yextloqp/export.pkl?raw=1'
export_file_name = 'export.pkl'
mapbox_key = "pk.eyJ1IjoianBrdW5rbGVyIiwiYSI6ImNqZzB0MjFjNDBiam8ycXFweGlnMThmbG8ifQ.vA1aff3tTCIX_zQsPj0cTg"

valid_api_keys = ["4ab88b42-3a5c-4318-83a6-fca9d06efc4c"] # required to access classification API

classes = ['Gut', 'Mittel', 'Schlecht', 'Sehr_Gut']
path = Path(__file__).parent

app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_headers=['X-Requested-With', 'Content-Type'])
app.mount('/static', StaticFiles(directory='app/static'))


async def download_file(url, dest):
    if dest.exists(): return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            with open(dest, 'wb') as f:
                f.write(data)


async def setup_learner():
    await download_file(export_file_url, path / export_file_name)
    try:
        learn = load_learner(path, export_file_name)
        return learn
    except RuntimeError as e:
        if len(e.args) > 0 and 'CPU-only machine' in e.args[0]:
            print(e)
            message = "\n\nThis model was trained with an old version of fastai and will not work in a CPU environment.\n\nPlease update the fastai library in your training environment and export your model again.\n\nSee instructions for 'Returning to work' at https://course.fast.ai."
            raise RuntimeError(message)
        else:
            raise


loop = asyncio.get_event_loop()
tasks = [asyncio.ensure_future(setup_learner())]
learn = loop.run_until_complete(asyncio.gather(*tasks))[0]
loop.close()


@app.route('/')
async def homepage(request):
    html_file = path / 'view' / 'index.html'
    return HTMLResponse(html_file.open().read())


@app.route('/analyze', methods=['POST'])
async def analyze(request):
    img_data = await request.form()
    with urllib.request.urlopen(img_data["file"]) as url:
        f = BytesIO(url.read())
    img = open_image(f)
    prediction = learn.predict(img)
    prob, label = topk(prediction[2],len(classes))
    inv_map = {v: k for k, v in learn.data.c2i.items()}
    labels = list(map(inv_map.get,label.data.tolist()))
    prob = [round(float(x),2) for x in prob.data.tolist()]
    output = dict(zip(labels, prob))
    output.update({'result': str(prediction[0])})
    return JSONResponse(output)

@app.route('/api/v1.0/classify/{addr}')
async def homepage(request):
    addr = request.path_params["addr"]
    print(addr)

    # Check for required access token in URL
    try:
        validation = request.query_params["access_token"]
    except: # return error if no token was supplied
        return JSONResponse({"message": "Please enter an access_token using ?access_token=YOUR_TOKEN."}, status_code=400)

    # check if token is valid
    if validation in valid_api_keys:
        output = classifyLocation(*geocode(addr, mapbox_key))

        # if our model returned None as result, an error occured
        if output["result"] == None:
            return JSONResponse(output, status_code = 400) # error retrieving location
        else: # no error occured --> return result
            return JSONResponse(output)
    else: # token was supplied but not valid
        return JSONResponse({"message": "Invalid Access Token."}, status_code = 400)

def geocode(addr, api_key):
    """Use Mapbox Geocoding Service to retrieve coordinate pair for given address."""
    base_url = "https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json?access_token={API_KEY}&language=de"
    headers = {'Content-Type': 'application/json',
           'Authorization': 'Bearer {0}'.format(api_key)}
    url = base_url.format(address=addr, API_KEY = api_key)

    response = requests.get(url.format(address=addr, API_KEY = mapbox_key), headers = headers)

    if response.status_code == 200:
        data = json.loads(response.content.decode('utf-8'))
        most_relevant = data["features"][0]
        if most_relevant["relevance"] < 0.8:
            return (None, None, None)

        lng = most_relevant["center"][0]
        lat = most_relevant["center"][1]
        rel = most_relevant["relevance"]
        return (lat, lng, rel)
    else:
        return (None, None, None)

def classifyLocation(lat, lng, relevance):
    """Classify location specified by coordinate pair using our trained CNN model."""

    if lat == None or lng == None or relevance == None:
        return {"prediction": {},"result": None, "addr": {"coords": [], "relevance": None}, "message": "Error: Could not find geolocation."}

    width, height = 300, 500
    img_base_url = "https://dev.virtualearth.net/REST/v1/Imagery/Map/Aerial/{lat},{lon}/17?ms={width},{height}&od=1&c=de-DE&key=AijbFhynMi9YlUoC5sbBKfrfbnkcMJ34sYBEORQwbsviodnw8nTkkgh5se5COtMs"
    url = img_base_url.format(lat = lat, lon = lng, width = width, height = height)
    with urllib.request.urlopen(url) as response:
        f = BytesIO(response.read())

    img = open_image(f)
    prediction = learn.predict(img)
    prob, label = topk(prediction[2],len(classes))
    inv_map = {v: k for k, v in learn.data.c2i.items()}
    labels = list(map(inv_map.get,label.data.tolist()))
    prob = [round(float(x),2) for x in prob.data.tolist()]
    pred_dict = dict(zip(labels, prob))
    output = dict({'prediction': pred_dict})
    output.update({'result': str(prediction[0])})
    output.update({'addr': {'coords': [lng, lat], 'relevance': relevance}})

    return output

if __name__ == '__main__':
    if 'serve' in sys.argv:
        uvicorn.run(app=app, host='0.0.0.0', port=5000, log_level="info")
