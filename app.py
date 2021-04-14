# -*- coding: utf-8 -*-
import os
import requests
import json
import base64
from datetime import datetime 
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Get the required value in the API from the environment variable
API_KEY_ID = os.environ.get('H_API_KEY_ID','')
API_KEY_PASS = os.environ.get('H_API_KEY_PASS','')
ACCESS_TOKEN_URL = os.environ.get('H_ACCESS_TOKEN_URL','')
URL = os.environ.get('H_URL','')
REQUEST_ID = os.environ.get('H_REQUST_ID','')
WEB_HOOK_URL = os.environ.get('TEAMS_WEB_HOOK_URL','')


# test method
@app.route('/analysis_temperature')
def hello():
    # environment variable check
    if API_KEY_ID is '':
        return "no setting environment variables!"

    #  get access token
    access_t = _get_access_token()
    if access_t is 401:
        print("can not get access token!")
        return None
    
    image_data = _image_file_to_base64('image.jpg')

    # analysis degital meter
    meter_value, meter_time = _analysis_meter_image(access_t, image_data)

    # notify micorosoft teams
    # TOD
    post_teams_message(meter_value, meter_time)

    name = "Hello World"
    return name

# ----------------------------------------------------------------------------------------

# Convert image to base64
def _image_file_to_base64(file_path):
    with open(file_path, "rb") as image_file:
        data = base64.b64encode(image_file.read())

    print(str(data.decode))

    return data.decode()

# Get an API access token
def _get_access_token():
    print("start _get_access_token()")
    
    r = requests.post(
        URL + '/v2/oauth2/access_token',
        json.dumps({ 
            'username' : API_KEY_ID ,
            'password' : API_KEY_PASS 
        }),
        headers = {
            'Content-Type': 'application/json'
        })
    
    data = r.json()
    
    if r.status_code == 200:
        access_t = data['access_token']
    else:
        access_t = r.status_code
        print("value : access_token " + " r_status :" + str(r.status_code))

    print("end _get_access_token()")

    return access_t

def _analysis_meter_image(_access_token, _image_data):
    r = requests.post(
        URL + '/v1/resources/images/meter_type/MET0005',
        json.dumps({
            'image' : _image_data
        }),
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer '+ str(_access_token),
            'X-Hakaru-Request-Id':REQUEST_ID
        })

    data = r.json()
    print(data)
    
    if data["result"]["error_code"] == 'OK':
        m_value = data["api_res"]["resource"]["value"]
        m_time  = data["api_res"]["resource"]["measured_at"]
        m_error = data["result"]["error_code"]
    else:
        m_value = '0000'
        m_time  = '0000'    

    # リクエスト結果（成功でも失敗でも）をDB OR JSONに保存
    # 　形式は以下の通りとする
    #       {
    #             id : auto_increment,
    #             value : merter_value,
    #             time : meter_time,
    #             analysis_result : 1/0{成功/失敗}
    #             image : image_data(base64形式)
    #       }　　
    _json_data = dict()
    data["id"] = "1"
    data["value"] = str(m_value)
    data["time"] = str(m_time)
    data["analysis_result"] = "1" if m_value is not '0000' else '0'
    data["image"] = _image_data

    with open('data.json', mode='wt') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    return m_value, m_time

def post_teams_message(_meter_value, _meter_time):

    dt_now = datetime.now()
    if _meter_value is '0000':
        print("error temporature analysis!")
        message = "error"
    else:
        message  = "{0}".format(str(_meter_value))
    
    requests.post(
        WEB_HOOK_URL, 
        json.dumps({
            'title': 'analysis result',
            'text': message
        }))

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
