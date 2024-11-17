import json
from flask import Flask, jsonify
from flask import request
from werkzeug.utils import secure_filename
import os
import time
import base64

DEBUG = True

def dbgprint(message: str, val):
    if DEBUG:
        print(message, val)

app = Flask(__name__)

upload_dir = 'uploads'
response_dir = 'response'


@app.route("/")
def index():
    """ ブラウザに「Hello World」と表示 """
    return "Hello World"

@app.route("/json")
def hello_world():
    """ jsonを返却するサンプル """
    res_dict = {
        "id": 1,
        "data": [
            {
                "user_id": 1,
                "name": "yamada",
                "age": "26"
            }
        ]
    }
    return json.dumps(res_dict)

@app.route("/upload", methods=['POST'])
def upload_and_wait():
    """画像と音声ファイルを受信するエンドポイント"""
    if 'image' not in request.files:
        return json.dumps({"error": "画像ファイルがありません"}), 400
    
    imgfile   = request.files['image']
    soundfile = request.files['sound']
    dbgprint('img  : ', imgfile)
    dbgprint('sound: ', soundfile)

    if imgfile.filename == '':
        return json.dumps({"error": "ファイルが選択されていません"}), 400
        
    if not (imgfile and imgfile.filename.endswith('.jpg')):
        return json.dumps({"error": "jpg画像のみ対応しています"}), 400

    if not (soundfile and soundfile.filename.endswith('.wav')):
        return json.dumps({"error": "wavファイルのみ対応しています"}), 400

    # imgfileをlocalに保存
    imgfilename = secure_filename(imgfile.filename)
    imgfilepath = os.path.join(upload_dir, imgfilename)
    imgfile.save(imgfilepath)

    # soundfileをlocalに保存
    soundfilename = secure_filename(soundfile.filename)
    soundfilepath = os.path.join(upload_dir, soundfilename)
    soundfile.save(soundfilepath)

    timeout = 60  # タイムアウト秒数
    start_time = time.time()
    response_file = os.path.join(response_dir, 'response.txt')
    while time.time() - start_time < timeout:
        if not os.path.exists(response_file):
            print('waiting for response...')
            time.sleep(5) # 10秒待つ
        else:
            break

    print('Response received!')

    with open(response_file, 'r') as f:
        response_text = f.read()

    #if os.path.exists(response_file): # 読み終わったらファイルを削除
        #os.remove(response_file)
    #if os.path.exists(imgfilepath):
        #os.remove(imgfilepath)
    #if os.path.exists(soundfilepath):
        #os.remove(soundfilepath)

    return json.dumps({"response": response_text})


@app.route("/respond", methods=['POST'])
def upload_response():
    """MLサーバーが応答テキストをuploadするエンドポイント"""
    response_text = request.form.get('text', '')
    response_path = os.path.join(response_dir, 'response.txt')
    with open(response_path, 'w', encoding='utf-8') as f:
        f.write(response_text)
    
    # return success
    return jsonify({"message": "Success"}), 200


@app.route("/retrieve")
def retrieve():
    """MLサーバーが画像と音声を回収するエンドポイント"""
    res_dict = {
        "image": "",
        "sound": ""
    }

    # ファイルがアップロードされるのを待機
    timeout = 60  # タイムアウト秒数
    start_time = time.time()
    while time.time() - start_time < timeout:
        files = os.listdir(upload_dir)
        
        # アップロードファイルが2つあるか確認
        if len(files) == 2:
            # 画像とテキストのファイルを区別して取得
            image_file = None
            sound_file = None
            for file in files:
                if file.endswith('.jpg'):
                    image_file = file
                elif file.endswith('.wav'):
                    sound_file = file

            # ファイル形式が正しいか確認
            if not image_file or not sound_file:
                return jsonify({"error": "jpgおよびwavファイルが揃っていません"}), 400

            # ファイル内容を読み込み、base64エンコードしてJSONに格納
            with open(os.path.join(upload_dir, image_file), 'rb') as img_f:
                res_dict['image'] = base64.b64encode(img_f.read()).decode('utf-8')
            with open(os.path.join(upload_dir, sound_file), 'r', encoding='utf-8') as snd_f:
                res_dict['sound'] = snd_f.read()

            # ファイルを処理済みとして削除（必要に応じてバックアップ）
            #os.remove(os.path.join(upload_dir, image_file))
            #os.remove(os.path.join(upload_dir, sound_file))

            return jsonify(res_dict)

        # ファイルが揃っていない場合は待機
        print('waiting img and sound file to be uploaded...')
        time.sleep(5)

    # タイムアウト処理
    return jsonify({"error": "タイムアウトしました"}), 408

if __name__ == '__main__':
    upload_dir = 'uploads'
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    response_dir = 'response'
    if not os.path.exists(response_dir):
        os.makedirs(response_dir)

    app.run(host='0.0.0.0', port=80, debug=True)