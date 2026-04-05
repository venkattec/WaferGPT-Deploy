import logging
from typing import Dict
from sem_inference import predict
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from langchain.tools import tool
from langchain.chains import LLMChain, TransformChain, SequentialChain
from langchain.llms import Ollama
from langchain.prompts import PromptTemplate
import os
from transformers import LlavaProcessor, LlavaForConditionalGeneration
from calculateDefect import detect_defects
from localizeDefect import detect_and_localize_defects
from visualTransformer import find_defects
# from save_img import cnv
import numpy as np
import torch
from PIL import Image
from datetime import datetime
from locate_sem import locate_sem_defect

LOG_FILE = "tools.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)
def change_file_path(input_path):
    directory, file_name = os.path.split(input_path)
    new_directory = directory.replace('png_files', 'npy_files')
    new_file_name = os.path.splitext(file_name)[0] + '.npy'
    new_path = os.path.join(new_directory, new_file_name)
    return new_path
# Log function to record tool execution details
def log_tool_usage(tool_name, question, image_path=None):
    """
    Logs the tool usage: question, tool name, timestamp, image path if provided.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if image_path:
        logging.info(f"Timestamp: {timestamp} | Tool: {tool_name} | Question: {question} | Image Path: {image_path}")
    else:
        logging.info(f"Timestamp: {timestamp} | Tool: {tool_name} | Question: {question}")

def log_tool_result(tool_name, result):
    """
    Logs the result of the tool execution.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.info(f"Timestamp: {timestamp} | Tool: {tool_name} | Result: {result}")

def log_tool_execution(tool_name, arguments):
    """
    Logs the arguments passed to the tool during execution.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.info(f"Timestamp: {timestamp} | Executing Tool: {tool_name} | Arguments: {arguments}")

# Initialize models
llava_processor = LlavaProcessor.from_pretrained("llava-hf/llava-1.5-7b-hf")
llava_model = LlavaForConditionalGeneration.from_pretrained("llava-hf/llava-1.5-7b-hf")


# Define tools
@tool
def multimodal_tool(image_path: str, question: str) -> str:
    """
    Performs a multimodal analysis on the given image and provides a general summary.
    """
    tool_name = "MultimodalTool"
    log_tool_usage(tool_name, question, image_path)
    try:
        # Load and preprocess the image
        # image_path = cnv(image_path)
        image = Image.open(image_path)
        prompt = f"USER: <image>\nConsider yourself as a image analyst and please answer the question from the user based on the image given.User will upload a wafer image from the semiconductor factory. Answer the question based on that wafer image {question}. ASSISTANT:"
        # print(prompt)
        inputs = llava_processor(images=image, text=prompt, return_tensors="pt")

        # Debug: Check image tokenization
        # print("Pixel values shape:", inputs.get("pixel_values", None).shape)

        # Generate output
        with torch.no_grad():
            # outputs = self.model.generate(**inputs)
            generate_ids = llava_model.generate(**inputs, max_new_tokens=100)
            answer = llava_processor.batch_decode(generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
            log_tool_result(tool_name, answer.split('ASSISTANT:')[-1])
            return answer.split('ASSISTANT:')[-1]
        # Decode and return the response
        # return self.processor.decode(outputs[0], skip_special_tokens=True)
    except Exception as e:
        log_tool_result(tool_name, f"Error during analysis: {e}")
        return "An error occurred during processing."


@tool
def defect_percentage_tool(image_path: str, question: str) :
    """
    Calculates the percentage of the wafer that is defective.
    """
    tool_name = "DefectPercentageCalculator"
    log_tool_usage(tool_name, question, image_path)
    try:
        if not image_path:
            return "Error: Image path is missing."
        if "sem" in image_path:
            return "The defect percentage cannot be calculated for SEM images."
        defect_percentage,output_image = detect_defects(npy_path=change_file_path(image_path))
        log_tool_result(tool_name, str(defect_percentage))
        # return str(defect_percentage)
        return {"result": defect_percentage, "image_path": output_image}
    except Exception as e:
        log_tool_result(tool_name, f"Error: {str(e)}")
        return f"Error while calculating defect percentage: {str(e)}"


@tool
def defect_localize_tool(image_path: str, question: str) :
    """
    Localizes the largest defect in the wafer image.
    """
    tool_name = "DefectLocalizer"
    log_tool_usage(tool_name, question, image_path)
    try:
        if not image_path:
            return "Error: Missing image path."
        if "sem" in image_path:
            output,output_image = locate_sem_defect(image_path)
        else:
            output,output_image = detect_and_localize_defects(npy_path=change_file_path(image_path))
        log_tool_result(tool_name, str(output))
        # return str(output)
        return {"result": output, "image_path": output_image}

    except Exception as e:
        log_tool_result(tool_name, f"Error: {str(e)}")
        return f"Error during localization: {str(e)}"

@tool
def defect_classification_tool(image_path: str, question: str) -> str:
    """
    Classifies the defect type in the wafer image.
    """
    tool_name = "DefectClassifier"
    log_tool_usage(tool_name, question, image_path)
    try:
        if "sem" in image_path:
            output = predict(image_path)
        else:
            # save_image = cnv(image_path)
            image_path = change_file_path(image_path)
            array = np.load(image_path, allow_pickle=True)
            array = np.expand_dims(array, -1)  # Add batch dimension
            image = np.array([array])
            output = find_defects(image)
        log_tool_result(tool_name, output)
        return output
    except Exception as e:
        log_tool_result(tool_name, f"Error: {str(e)}")
        return str(e)


# Define output schema
class DefectAnalysisOutput(BaseModel):
    result: str = Field(..., description="The output of the selected tool based on the user's question.")


parser = PydanticOutputParser(pydantic_object=DefectAnalysisOutput)

# Initialize LLM
llm = Ollama(model="llama3")

# Define prompt template
tool_selection_prompt = PromptTemplate(
    input_variables=["question"],
    template="""
    You are an assistant analyzing wafer maps. The human has asked a question.

    Question: {question}

    You have access to the following tools:
    1. DefectPercentageCalculator: Calculates the percentage of the wafer that is defective.
    2. DefectLocalizer: Localizes the largest defect on the wafer.
    3. DefectClassifier: Classifies the defect type in the wafer image.
    4. MultimodalLLMTool: Answers general questions about the wafer image.

    Based on the question, select the most relevant tool and return its name as:
    Tool: <tool_name>
    """
)

# Tool selection chain
tool_selector = LLMChain(
    llm=llm,
    prompt=tool_selection_prompt,
    output_key="selected_tool"
)


# Tool execution logic
def execute_tool(selected_tool: str, image_path: str, question: str):
    """
    Executes the selected tool and returns the result.
    """
    tool_mapping = {
        "DefectPercentageCalculator": defect_percentage_tool,
        "DefectLocalizer": defect_localize_tool,
        "DefectClassifier": defect_classification_tool,
        "MultimodalLLMTool": multimodal_tool,
    }
    selected_tool = selected_tool.split(':')[-1].strip()
    log_tool_execution(selected_tool, {"image_path": image_path, "question": question})
    if selected_tool in tool_mapping:
        tool = tool_mapping[selected_tool]

        # Ensure inputs are passed as a dictionary with correct types
        inputs = {"image_path": str(image_path), "question": str(question)}
        result = tool(inputs)  # Call the tool

        # If the tool returns an image, format response accordingly
        if isinstance(result, dict) and "image_path" in result:
            return result  # Returning a dictionary with text and image
        else:
            return {"result": result}
        # return tool(inputs)  # Pass dictionary to the tool
    else:
        return "Invalid tool selected."



# TransformChain for tool execution
tool_executor = TransformChain(
    input_variables=["selected_tool", "image_path", "question"],
    output_variables=["tool_result"],
    transform=lambda inputs: {
        "tool_result": execute_tool(inputs["selected_tool"], inputs["image_path"], inputs["question"])
    }
)

# Create a SequentialChain to combine selection and execution
chain = SequentialChain(
    chains=[tool_selector, tool_executor],
    input_variables=["image_path", "question"],
    output_variables=["tool_result"]
)

def get_answer(question,file_path):
    # Inputs
    inputs = {
        "image_path": os.path.abspath(file_path),
        "question": question
    }

    # Run the chain
    response = chain.run(inputs)
    print("Agent Response:", response)
    return response
