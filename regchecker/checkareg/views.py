from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView
from django.conf import settings
import base64, requests, json
import webcolors

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
        data = constructFeatureQuery("text", encoded_string)

        #  sending Cloud Vision API post request and saving response as json
        response = requests.post(url = API_ENDPOINT, json = data)
        
        # extracting response json
        json_resp = response.json()

        # get Feature result and score     
        (value, score) = getFeatureResultAndScoreFromJsonResponse("text", json_resp)
  
        # render a view to contain the results 
        return render(request, 'checkareg/get_reg.html', {
            'feature' : "text",
            'value': value,
            'score': score,
            'json' : json_resp
        })
    
    # default page to render when url called as GET
    return render(request, 'checkareg/get_reg.html')

        # extract result value and reliability score from response
def getFeatureResultAndScoreFromJsonResponse(feature, json_resp):
    if feature == "colour":
        # extract colour from json (dict)
        (value,score) = extractColourFromResponse(json_resp)
    elif feature == "logo":
        # extract logo from json (dict)
        (value,score) = extractLogoFromResponse(json_resp)
    else: 
        # extract number text from json (dict)
        value = extractNumberFromResponse(json_resp)
        score = 1
    return (value, score)

# construct and return a Cloud Vision Json Query object for required feature 
def constructFeatureQuery(feature, encoded_string):
    if feature == 'colour':
        ftype = "IMAGE_PROPERTIES"
    elif feature == "logo":
        ftype = "LOGO_DETECTION"
    else:
        ftype = "TEXT_DETECTION"

    data = {
            "requests":[
                {
                    "image": {
                        "content": encoded_string
                    },
                    "features":[
                        {
                            "type": ftype
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
def extractLogoFromResponse( json_resp ):
    try:
        logo = json_resp['responses'][0]['logoAnnotations'][0]['description']
        score = json_resp['responses'][0]['logoAnnotations'][0]['score']
    except (IndexError, KeyError) :
        logo = 'Error parsing response'
        score = 0
    return (logo,score)

# extract closest colour from json (dict)
def extractColourFromResponse( json_resp ):
    try:
        rgb_colour = json_resp['responses'][0]['imagePropertiesAnnotation']['dominantColors']['colors'][0]['color']        
        colour = closest_colour(rgb_colour)
        score = json_resp['responses'][0]['imagePropertiesAnnotation']['dominantColors']['colors'][0]['score']
    except (IndexError, KeyError) :
        colour = 'Error parsing response'
    return (colour,score)

# determine closest color name from rgb colour parameter
def closest_colour(requested_colour):
    min_colours = {}
    for key, name in webcolors.css3_hex_to_names.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(key)
        rd = (r_c - requested_colour['red']) ** 2
        gd = (g_c - requested_colour['green']) ** 2
        bd = (b_c - requested_colour['blue']) ** 2
        min_colours[(rd + gd + bd)] = name
    return min_colours[min(min_colours.keys())]

        
