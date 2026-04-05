from flask import Flask, render_template,request,jsonify

from langchainFlow1 import get_answer
app = Flask(__name__)

import os

def change_file_path(input_path):
    directory, file_name = os.path.split(input_path)
    new_directory = directory.replace('png_files', 'npy_files')
    new_file_name = os.path.splitext(file_name)[0] + '.npy'
    new_path = os.path.join(new_directory, new_file_name)
    return new_path

# Test the function
input_path = '/home/sbna/Documents/WaferDefectDetector/png_files/image11.png'
new_path = change_file_path(input_path)

print(new_path)


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get-answer', methods=['POST'])
def run_agent():
    question = request.args.get('question')
    image_path = request.args.get('image_path')
    if question and image_path:
        return get_answer(question, image_path)
    elif not image_path:
        return "No wafer selected. Please select a wafer image."

@app.route('/get-report', methods=['POST'])
def get_report():
    image_path = request.args.get('image_path')
    if image_path:
        print(f"Generating report for image: {image_path}")
        from report import generate_report
        result = generate_report(image_path)
        return jsonify(result)
    return "No image path provided. Please provide an image_path parameter."


# @app.route('/detect-defect-sem-api')
# def detect_defect_sem_api():
#     image_path = request.args.get('image_path')
#     if image_path:
#         print(f"Detecting defect in SEM image: {image_path}")
#         predicted_class, confidence = predict(image_path)
#         return {"predicted_class": predicted_class, "confidence": confidence}
#     return "No image path provided. Please provide an image_path parameter."
#
# @app.route('/detect-defect-sem', methods=['POST'])
# def detect_defect_sem():
#     image = request.files.get('image')
#     if image:
#         image_path = f"./uploads/{image.filename}"
#         image.save(image_path)  # Save uploaded image
#         predicted_class, confidence = predict(image_path)
#         return {"predicted_class": predicted_class, "confidence": confidence}
#     return "No image uploaded. Please upload an image."
#

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8555, debug=True)
