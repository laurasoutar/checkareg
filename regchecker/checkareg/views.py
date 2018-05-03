from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView
from django.conf import settings
import base64, requests, json
from django import forms
import urllib

_regno = ''

# Create your views here.
def post_list(request):
    return render(request, 'checkareg/post_list.html', {})


def get_reg(request):
     # check if a post request and process file upload
    if request.method == 'POST': #and request.FILES['imagefile']:
        API_ENDPOINT = "https://vision.googleapis.com/v1/images:annotate?key=AIzaSyD9CNPDx3kLZk0j1viCztlLDhi6wROrNIk"
        # extract file from request and store locally in media folder
        image_file = request.FILES['imagefile']
        fs = FileSystemStorage()
        filename = fs.save(image_file.name, image_file)

        # base64 encode the file
        with open(fs.location + "/" + filename, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

        # now delete the file
        fs.delete(filename)

        # extract feature extraction from request
        #feature = request.POST["feature"]

        # construct feature API query object to contain base64 string
        data = constructFeatureQuery(encoded_string)

        #  sending Cloud Vision API post request and saving response as json
        response = requests.post(url = API_ENDPOINT, json = data)
        
        # extracting response json
        json_resp = response.json()

        # get Feature result and score     
        (makevalue, numbervalue) = getFeatureResultAndScoreFromJsonResponse(json_resp)
  
        global _regno
        _regno = numbervalue

        # render a view to contain the results 
        return render(request, 'checkareg/confirmation.html', {

            'feature' : "logo",
            'makevalue': makevalue,
            'numbervalue': numbervalue,
            'json' : json_resp
        })
    
    # default page to render when url called as GET
    return render(request, 'checkareg/get_reg.html')

        # extract result value and reliability score from response
def getFeatureResultAndScoreFromJsonResponse(json_resp):
    makevalue = extractMakeFromResponse(json_resp)
    numbervalue = extractNumberFromResponse(json_resp)
    return (makevalue, numbervalue)

# construct and return a Cloud Vision Json Query object for required feature 
def constructFeatureQuery(encoded_string):
    data = {
            "requests":[
                {
                    "image": {
                        "content": encoded_string
                    },
                    "features":[
                        {
                            "type": "TEXT_DETECTION"
                        },
                        {
                            "type": "LABEL_DETECTION"
                        }
                    ]
                }
            ]
        }

    return data


# extract number text from json (dict)
def extractNumberFromResponse( json_resp ):
    try:
        number = json_resp['responses'][0]['textAnnotations'][0]['description']
    except (IndexError, KeyError) :
        number = 'Error parsing description'
    return number

# extract logo name from json (dict)
def extractMakeFromResponse( json_resp ):
    car_array = ['range rover', 'lamborghini', 'fiat 500', 'mini cooper']
    try:
        for desc in json_resp['responses'][0]['labelAnnotations']:
            for car in car_array:
                if(car ==  desc['description']):
                    make = desc['description']
                    
        #make = json_resp['responses'][0]['labelAnnotations'][0]['description']
        #score = json_resp['responses'][0]['labelAnnotations'][0]['score']
    except (IndexError, KeyError) :
        make = 'Error parsing response'
       # score = 0
    return make

# check licence plate against PNC
def checkPNC(request): 
    global _regno
    _regno = _regno.strip()
    params = {"VehicleReg": _regno}
    url = "http://codeitteam3.westeurope.cloudapp.azure.com/api/vehicles?%s" %(urllib.parse.urlencode(params))

    r = requests.get(url, auth=('admin@civica.local', 'password123'))
    
    vehicle = json.loads(r.text)
    return render(request, 'checkareg/success.html', {'status': r.status_code, 'data': vehicle, 'regno': _regno, 'url': url})

        
