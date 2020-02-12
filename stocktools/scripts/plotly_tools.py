from _plotly_utils.utils import PlotlyJSONEncoder
import io
import requests
import json
from PIL import Image

def genIMGfromFile(fig, filenameout='', scale=1.0, width=1000, height=500):
    server_url = "http://docker_orcapp_1:9091"
    request_params = {
        "figure": fig.to_dict(),
        "format": "png", # any format from "png", "jpeg", "webp", "svg", "pdf", "eps"
        "scale": scale,
        "width": width,
        "height": height
    }
    json_str = json.dumps(request_params, cls=PlotlyJSONEncoder)
    response = requests.post(server_url + "/", data=json_str)
    image = response.content
    if len(filenameout) > 0:
        imgPIL = Image.open(io.BytesIO(image))
        #with open("img.png", 'w') as file:
        imgPIL.save(filenameout)
    return image