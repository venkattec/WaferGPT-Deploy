from openai import OpenAI
import base64,os
api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


# Function to convert image to base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def get_openai_response(question,image_path=None):

    prompt = f'''Consider yourself as an image analyst, you inspects wafer images or
                     SEM images of wafer from semiconductor industry. User will upload either one of those image
                     and ask a question about it to get the answer. Answer in a way that is relevant to the image and semiconductor
                     industry in less than 50 words.                
                     Also if irrelevant questions come out of semiconductor industry, deny politely saying
                     you are specifically trained for semiconductor industry wafer based images. Other wise answer based on the 
                     question.
                     user question is {question}
                     '''
    message_content = [{"type": "text", "text": prompt}]

    if image_path:
        base64_image = encode_image(image_path)
        message_content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"  # Embed base64 image
                },
            }
        )
    # API request
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": message_content}],
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    question = "what do you see in this image?"
    image_path = "png_files/image3.png"
    response = get_openai_response(question, image_path)
    print(response)
