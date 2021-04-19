# -*- coding: utf-8 -*-
import os
import requests
import json
import base64
from datetime import datetime 
from flask import *
from flask import render_template
from flask_cors import CORS
import picamera
from db import select_all, insert_analysis

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
CORS(app)

# 環境変数から値を取得します
API_KEY_ID = os.environ.get('H_API_KEY_ID','')
API_KEY_PASS = os.environ.get('H_API_KEY_PASS','')
ACCESS_TOKEN_URL = os.environ.get('H_ACCESS_TOKEN_URL','')
URL = os.environ.get('H_URL','')
REQUEST_ID = os.environ.get('H_REQUST_ID','')
WEB_HOOK_URL = os.environ.get('TEAMS_WEB_HOOK_URL','')

# 解析結果JSONファイルの中身を返します
@app.route('/fetch_all')
def fetch_all():
    return jsonify({"result" : select_all()})

@app.route('/photo_temperature')
def test_temperature():
    # TOD : ラズパイで写真撮影し、それを変数に格納
    _camera_capture()
    # TOD : 撮影した写真を返せるように修正（現在、ハードコーディング中
    return '<img src="data:image/png;base64,' + _image_file_to_base64('my_pic.jpg') + '"/>'

# 画像から解析AIに投げた結果をTeams通知します
@app.route('/analysis_temperature')
def analysis_temperature():
    # environment variable check
    if API_KEY_ID is '':
        return "no setting environment variables!"

    #  get access token
    access_t = _get_access_token()
    if access_t is 401:
        print("can not get access token!")
        return None
    
    # TOD カメラで温度計を撮影し、base64変換
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

    # リクエスト結果（成功でも失敗でも）をDBに保存
    insert_analysis(
        str(m_value), 
        str(m_time), 
        "1" if m_value is not '0000' else '0'
    )

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

def _camera_capture():
    with picamera.PiCamera() as camera:
        # 解像度の設定
        camera.resolution = (1024, 768)
        # 撮影の準備
        camera.start_preview()
        # 準備している間、少し待機する
        time.sleep(2)
        # 撮影して指定したファイル名で保存する
        camera.capture('my_pic.jpg')
        print('Camera End!')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
