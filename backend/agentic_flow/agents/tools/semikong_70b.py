import os,time
from openai import OpenAI
api_key = os.environ.get("HUGGING_FACE_API_KEY")  # Set this as environment variable4

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=api_key,
)


def semikong_query(question: str, description: str):
    completion = client.chat.completions.create(
        model="pentagoniac/SEMIKONG-70B:featherless-ai",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are SEMIKONG, a domain expert in semiconductor wafer analysis. "
                    "Your job is to provide precise, technical answers strictly related to "
                    "wafer defects, usability, defect spread, root cause, or corrective actions. "
                    "Never include unrelated commentary or speculative content."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Given the following wafer description and the user's question, provide a concise and domain-specific answer.\n\n"
                    f"Wafer Description:\n{description}\n\n"
                    f"Question:\n{question}\n\n"
                    "Answer strictly based on the wafer description and semiconductor knowledge. "
                    "If the description does not provide enough information to fully answer, say so clearly."
                ),
            }
        ],
    )
    return completion.choices[0].message.content


# print(completion.choices[0].message)
if __name__ == "__main__":
    description = "There are multiple defects in the lower-right region."
    question = "What type of defect pattern does this indicate?"
    start_time = time.time()
    answer = semikong_query(question, description)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print("Answer:", answer)
    print(f"Time taken: {elapsed_time:.2f} seconds")