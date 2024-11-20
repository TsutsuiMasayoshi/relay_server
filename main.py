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
debug_upload_dir = 'debug_uploads'
response_dir = 'response'

response_file_path = os.path.join(response_dir, 'response.txt')

@app.route("/")
def index():
    return "Welcome to Chiikawa team's GCP server!"

@app.route("/debug_upload", methods=['POST'])
def debug_upload_and_wait():
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

    return json.dumps({"response": "This is a debug response. Image file and sound file are received successfully."})


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
    while time.time() - start_time < timeout:
        if not os.path.exists(response_file_path):
            print('waiting for response...')
            time.sleep(5) # 10秒待つ
        else:
            break

    print('Response received!!')

    with open(response_file_path, 'r') as f:
        response_text = f.read()

    if os.path.exists(response_file_path): # 読み終わったらファイルを削除
        os.remove(response_file_path)
    if os.path.exists(imgfilepath):
        os.remove(imgfilepath)
    if os.path.exists(soundfilepath):
        os.remove(soundfilepath)

    return json.dumps({"response": response_text})


@app.route("/respond", methods=['POST'])
def upload_response():
    """MLサーバーが応答テキストをuploadするエンドポイント"""
    data = request.get_json()
    if not data or 'response_text' not in data:
        return jsonify({"error": "Invalid data"}), 400

    # 受信したデータを展開
    response_text = data['response_text']
    print(f"Received response_text: {response_text}")

    with open(response_file_path, 'w', encoding='utf-8') as f:
        f.write(response_text)
    
    # 確認用のレスポンスを返す
    return jsonify({"message": "Data received successfully", "response_text": response_text}), 200

def retrieve_files_from(dir: str):
    res_dict = {
        "image": "",
        "sound": ""
    }

    # ファイルがアップロードされるのを待機
    timeout = 60  # タイムアウト秒数
    start_time = time.time()
    while time.time() - start_time < timeout:
        files = os.listdir(dir)
        
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

            try:
                # 両方のファイルをbase64エンコードしてJSONで返す
                with open(os.path.join(dir, image_file), 'rb') as img_f:
                    img_base64 = base64.b64encode(img_f.read()).decode('utf-8')
                with open(os.path.join(dir, sound_file), 'rb') as sound_f:
                    sound_base64 = base64.b64encode(sound_f.read()).decode('utf-8')

                res_dict = {
                    "status": "success",
                    "data": {
                        "image": {
                            "filename": image_file,
                            "content": img_base64,
                            "content_type": "image/jpeg"
                        },
                        "sound": {
                            "filename": sound_file,
                            "content": sound_base64,
                            "content_type": "audio/wav"
                        }
                    }
                }

                return jsonify(res_dict)
                
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500
            
            return jsonify(res_dict)

        # ファイルが揃っていない場合は待機
        print('waiting img and sound file to be uploaded...')
        time.sleep(5)

    # タイムアウト処理
    return jsonify({"error": "タイムアウトしました"}), 408

@app.route("/debug_retrieve")
def debug_retrieve():
    """MLサーバーが画像と音声を回収するエンドポイントDebug ver."""
    return retrieve_files_from(debug_upload_dir)


@app.route("/retrieve")
def retrieve():
    """MLサーバーが画像と音声を回収するエンドポイントRelease ver."""
    return retrieve_files_from(upload_dir)

if __name__ == '__main__':
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    if not os.path.exists(debug_upload_dir):
        print("Error. Please prepare debug_upload_dir as " + debug_upload_dir + " and prepare sample image and wav files.")
        exit(1)
    if not os.path.exists(response_dir):
        os.makedirs(response_dir)

    app.run(host='0.0.0.0', port=80, debug=True)