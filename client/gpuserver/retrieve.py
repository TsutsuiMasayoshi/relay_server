# クライアント側のコード例
import requests
import base64

response = requests.get('http://34.30.245.193/debug_retrieve')
data = response.json()

if data['status'] == 'success':
    # 画像の保存
    img_content = base64.b64decode(data['data']['image']['content'])
    with open(data['data']['image']['filename'], 'wb') as f:
        f.write(img_content)
    
    # 音声の保存
    sound_content = base64.b64decode(data['data']['sound']['content'])
    with open(data['data']['sound']['filename'], 'wb') as f:
        f.write(sound_content)