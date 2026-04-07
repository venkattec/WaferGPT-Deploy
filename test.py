import requests
import base64

# Load and encode image
image_path = r"D:\Defect Detection\WaferGPT-Backend\png_files\image6.png"
with open(image_path, 'rb') as f:
    image_b64 = base64.b64encode(f.read()).decode('utf-8')

# API call
response = requests.post(
    'http://172.17.0.2:8555/get-answer',
    params={
        'question': 'where are defects in this wafer?',
        'image_b64': image_b64,
        'category': 'wafer'
    }
)

print("Status:", response.status_code)
print("Response:", response.text)