import requests
import ast, json
def invoke_api(image_path, user_message):
    """
    Sends a question and image path to the Flask backend and returns
    the result and processed image path (if any).
    """
    # Define the API URL of the running Flask server
    url = 'http://182.66.109.42:8555/get-answer'  # Corrected double slash

    print(f'''Request to API:
    question : {user_message}
    image_path : {image_path}''')
    if not image_path:
        return {"result": "please pick a wafer image", "image_path": None}
    try:
        # Send POST request with query parameters
        response = requests.post(url, params={"question": user_message, "image_path": image_path})

        # Check if the request succeeded
        if response.status_code == 200:
            try:
                # Parse JSON response safely
                data = response.json()
                print(f"Response from API: {json.dumps(data, indent=4)}")

                # Extract result and image path safely
                result = data.get("result", "No result found.")
                processed_image_path = data.get("image_path", None)

                return {
                    "result": result,
                    "image_path": processed_image_path
                }

            except json.JSONDecodeError:
                print("Error: Response was not valid JSON.")
                return {"result": "Invalid response format.", "image_path": None}

        else:
            print(f"Failed to get valid response. Status Code: {response.status_code}")
            print(f"Error: {response.text}")
            return {"result": {response.text}, "image_path": None}

    except Exception as e:
        print(f"Exception while calling API: {str(e)}")
        return {"result": "API call failed.", "image_path": None}

# def invoke_api(image_path, user_message):
#     # Define the API URL of the running Flask server
#     url = 'http://182.66.109.42:8555/get-answer'  # Adjust the URL if your server is running elsewhere

#     # Sample data to test the endpoint
#     # data = {
#     #     'question': 'how much is the wafer defected?',
#     #     'image_path': '/home/sbna/Documents/WaferDefectDetector/npy_files/image11.npy'  # Replace with an actual image path
#     # }
#     print(f'''Request to API:
#     question : {user_message}
#     image_path : {image_path}''')
#     # Make a POST request to the Flask API
#     response = requests.post(url, params={"question": user_message, "image_path": image_path})

#     # Print the response from the API
#     if response.status_code == 200:
#         print(f"Response from API: {response.text}")
#         return ast.literal_eval(response.text)
#     else:
#         print(f"Failed to get a valid response. Status Code: {response.status_code}, Error: {response.text}")
#         return {"result": "Failed to get a valid response."}

def get_report(image_path):
    # Define the API URL of the running Flask server
    url = 'http://182.66.109.42:8555//get-report'  # Adjust the URL if your server is running elsewhere

    # Sample data to test the endpoint

    print(f'''Request to generate report:
    image_path : {image_path}''')
    # Make a POST request to the Flask API
    response = requests.post(url, params={"image_path": image_path})

    # Print the response from the API
    if response.status_code == 200:
        print(f"Response from API: {response.text}")
        return ast.literal_eval(response.text)
    else:
        print(f"Failed to get a valid response. Status Code: {response.status_code}, Error: {response.text}")
        return {"result": {response.text}}

if __name__ == "__main__":
    # Example usage
    image_path = '/home/sbna/Documents/WaferGPT-Frontend/png_files/image37.png'  # Replace with an actual image path
    question = "how much is the wafer defected?"
    response = invoke_api(image_path, question)
    print(response)
    # report = get_report(image_path)
    # print(report)
    # print(type(report))