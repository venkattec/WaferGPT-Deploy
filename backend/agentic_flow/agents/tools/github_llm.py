from openai import OpenAI
import base64,os
from agents.tools.semikong_70b import semikong_query

# token = os.environ["GITHUB_TOKEN"]
endpoint = "https://models.github.ai/inference"
model = "gpt-4o-mini"
api_key = os.environ.get("OPENAI_API_KEY")  # Set this as environment variable4
client = OpenAI(
    api_key=api_key
)


def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


system_prompt = """You are an expert in semiconductor wafer defect analysis. 
Your task is to examine the provided wafer image and generate a precise, objective, 
and domain-specific description of what is visible. 

Guidelines:
- Focus only on features relevant to semiconductor wafers and defects (scratches, contamination, missing/extra points, pattern irregularities, edge defects, line/space defects, etc.).
- Avoid generic visual descriptions (e.g., colors, shapes) unless they are meaningful to wafer defect analysis.
- Do not speculate beyond the visible features. Keep the description factual and technical.
- Write the description clearly so it can be passed as input to another specialized wafer analysis model.

Return only the wafer description, nothing else.
"""

def get_openai_response(question, image_path):
    image_base64 = encode_image_to_base64(image_path)
    response = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }
                }
            ],
        }
    ],
    model=model
    )
    open_ai_response = response.choices[0].message.content
    print("Wafer Image Description:")
    print(open_ai_response)

    # Now pass description + question to semikong
    response = semikong_query(
        question=question,
        description=open_ai_response
    )
    return response


if __name__ == "__main__":
    # Example usage: set your image path here
    image_path = r"D:\Defect Detection\png_files\image27.png"
    # image_base64 = encode_image_to_base64(image_path)
    question = "This is a wafer map image. I'm going to use semikong which is a text based semiconductor model. so describe this wafer map image in detail. strictly give only the description of the image. don't give any other information."
    response = get_openai_response(question, image_path)
    # open_ai_response = response.choices[0].message.content
    # print("OpenAI/GitHub LLM Response:")
    # print(open_ai_response)
    print("\nSemikong 70B Model Response:")
    print(response)
