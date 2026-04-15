import requests
import base64

# Load and encode image
image_path = r"backend/png_files/image1.png"
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

# Step 3: Save returned image (if exists)
try:
    data = response.json()

    if "image_b64" in data:
        with open("response_image.png", "wb") as f:
            f.write(base64.b64decode(data["image_b64"]))
        print("Saved response_image.png")

    print("Answer:", data.get("answer"))

except Exception as e:
    print("Error parsing response:", e)
    print("Raw response:", response.text)

# Load and encode image
image_path = r"response_image.png"
with open(image_path, 'rb') as f:
    image_b64 = base64.b64encode(f.read()).decode('utf-8')

# API call
response = requests.post(
    'http://172.17.0.2:8555/get-answer',
    params={
        'question': 'Can you quantify the size of the defects',
        'image_b64': image_b64,
        'category': 'wafer'
    }
)

print("Status:", response.status_code)
print("Response:", response.text)

print("===============================")

# API call
response = requests.post(
    'http://146.235.237.150:8555/get-answer',
    params={
        'question': 'where are defects in this wafer?',
        'image_b64': image_b64,
        'category': 'wafer'
    }
)

print("Status:", response.status_code)
print("Response:", response.text)
