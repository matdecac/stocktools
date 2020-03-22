from _plotly_utils.utils import PlotlyJSONEncoder
from IPython.display import Image as ImageD
import io
import requests
import json
from PIL import Image
server_url = "http://docker_orcapp_1:9091"

def genIMGfromFile(filenameout=''):
    request_params = {
        "figure": fig.to_dict(),
        "format": "png", # any format from "png", "jpeg", "webp", "svg", "pdf", "eps"
        "scale": 1,
        "width": 1000,
        "height": 500
    }
    json_str = json.dumps(request_params, cls=PlotlyJSONEncoder)
    response = requests.post(server_url + "/", data=json_str)
    image = response.content
    if len(filenameout) > 0:
        imgPIL = Image.open(io.BytesIO(image))
        #with open("img.png", 'w') as file:
        imgPIL.save(filenameout)
    return image
display(ImageD(data=genIMGfromFile('img.png')))