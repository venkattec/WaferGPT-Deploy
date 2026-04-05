import logging,os
import numpy as np
from typing import Any, Dict

# Assumes your state models and base agent are in these locations
from models.state import AgentState, ClassificationData
from agents.tools.sem_inference import predict
from agents.tools.visualTransformer import find_defects
from .base import BaseAgent


# --- Tool Definition ---
# IMPORTANT: This section should import your actual tools.
# For this example, we'll define mock tools that include logging.
# from tools import log_tool_usage, log_tool_result, predict, find_defects, ...

def log_tool_usage(tool_name, question, image_path):
    """Placeholder for your logging function."""
    logging.info(f"Tool Used: {tool_name} | Question: {question} | Image: {image_path}")


def log_tool_result(tool_name, result):
    """Placeholder for your logging function."""
    logging.info(f"Tool Result: {tool_name} | Result: {result}")


# def predict(image_path: str) -> Dict[str, Any]:
#     """Placeholder for your SEM image classification model."""
#     return {"result": "Micro-cracking", "confidence": 0.92}
#
#
# def find_defects(image: str) -> Dict[str, Any]:
#     """Placeholder for your standard wafer classification model."""
#     return {"result": "Contamination", "confidence": 0.98}


def change_file_path(input_path):
    directory, file_name = os.path.split(input_path)
    new_directory = directory.replace('png_files', 'npy_files')
    new_file_name = os.path.splitext(file_name)[0] + '.npy'
    new_path = os.path.join(new_directory, new_file_name)
    return new_path

def defect_classification_tool(image_path: str, question: str) -> Dict[str, Any]:
    """
    Classifies the defect type in the wafer image.
    (This is your provided tool function, slightly adapted to return a dict for consistency)
    """
    tool_name = "DefectClassifier"
    log_tool_usage(tool_name, question, image_path)
    try:
        if "sem" in image_path:
            output = predict(image_path)
        else:
            image_path = change_file_path(image_path)
            array = np.load(image_path, allow_pickle=True)
            array = np.expand_dims(array, -1)
            image = np.array([array])
            output = find_defects(image)

        log_tool_result(tool_name, str(output))
        return {"result":output}
    except Exception as e:
        error_msg = f"Error in {tool_name}: {e}"
        log_tool_result(tool_name, error_msg)
        raise


# --- Agent Definition ---

class ClassificationAgent(BaseAgent):
    """An agent specialized in classifying wafer defects."""

    @property
    def name(self) -> str:
        """The unique name of the agent."""
        return "Classification"

    async def process(self, state: AgentState) -> Dict[str, Any]:
        """
        Executes the defect classification tool and updates the state.
        """
        # Call the specific tool for this agent
        tool_result = defect_classification_tool(
            image_path=state["image_path"],
            question=state["question"]
        )

        # Structure the output using the Pydantic model
        data = ClassificationData(
            defect_type=tool_result["result"]
            # confidence_score=tool_result.get("confidence")  # .get() is safer
        )

        # Return the specific state key this agent is responsible for
        return {"classification_data": data}