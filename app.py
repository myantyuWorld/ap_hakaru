import os
import requests
import json
import base64
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# env
API_KEY_ID = ''
API_KEY_PASS = ''
ACCESS_TOKEN_URL = ''
URL = ''
CHECK_API_URL = ''

@app.route('/')
def hello():
    name = "Hello World"

    _id, _pass, _token_url, _url, _check_api_url, _request_id = _get_env()

    #  get access token
    access_t = _get_access_token(_url, _id, _pass)

    if access_t is 401:
        print("can not get access token!")
        return None
    
    image_data = _image_file_to_base64('image.jpg')

    # analysis degital meter
    meter_value, meter_time = _analysis_meter_image(_url, access_t, _request_id, image_data)

    return meter_value, meter_time


# Get the required value in the API from the environment variable
def _get_env():
    print("call _get_env()")

    API_KEY_ID = os.environ.get('H_API_KEY_ID')
    API_KEY_PASS = os.environ.get('H_API_KEY_PASS')
    ACCESS_TOKEN_URL = os.environ.get('H_ACCESS_TOKEN_URL')
    URL = os.environ.get('H_URL')
    REQUEST_ID = os.environ.get('H_REQUST_ID')

    print("end _get_env()")

    return API_KEY_ID, API_KEY_PASS, ACCESS_TOKEN_URL, URL, CHECK_API_URL, REQUEST_ID

# Convert image to base64
def _image_file_to_base64(file_path):
    with open(file_path, "rb") as image_file:
        data = base64.b64encode(image_file.read())

    print(str(data.decode))

    return data.decode()

# Get an API access token
def _get_access_token(_url, _id, _pass):
    print("start _get_access_token()")
    
    r = requests.post(
        _url + '/v2/oauth2/access_token',
        json.dumps({ 'username' : _id , 'password' : _pass }),
        headers = {'Content-Type': 'application/json'})
    
    data = r.json()
    # print(data)
    
    if r.status_code == 200:
        access_t = data['access_token']
    else:
        access_t = r.status_code
        print("value : access_token " + " r_status :" + str(r.status_code))

    print("end _get_access_token()")

    return access_t

def _analysis_meter_image(_url, _access_token, _request_id, _image_data):
    r = requests.post(
        _url + '/v1/resources/images/meter_type/MET0005',
        json.dumps({'image' : _image_data}),
        headers = {'Content-Type': 'application/json','Authorization': 'Bearer '+ str(_access_token),'X-Hakaru-Request-Id':_request_id})
    
    data = r.json()
    
    print(data)
    
    if data["result"]["error_code"] == 'OK':
        m_value = data["api_res"]["resource"]["value"]
        m_time  = data["api_res"]["resource"]["measured_at"]
        m_error = data["result"]["error_code"]
    else:
        m_value = '0000'
        m_time  = '0000'    

    return m_value, m_time

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
