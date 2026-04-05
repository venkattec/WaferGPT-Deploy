import logging,os
from typing import Any, Dict

# Assumes your state models and base agent are in these locations
from models.state import AgentState, PercentageData
from agents.tools.calculateDefect import detect_defects
from .base import BaseAgent


# --- Tool Definition ---
# IMPORTANT: This section should import your actual tool.
# For this example, we'll define a mock tool that includes logging.
# from tools import defect_percentage_tool, log_tool_usage, log_tool_result

def change_file_path(input_path):
    directory, file_name = os.path.split(input_path)
    new_directory = directory.replace('png_files', 'npy_files')
    new_file_name = os.path.splitext(file_name)[0] + '.npy'
    new_path = os.path.join(new_directory, new_file_name)
    return new_path

def log_tool_usage(tool_name, question, image_path):
    """Placeholder for your logging function."""
    logging.info(f"Tool Used: {tool_name} | Question: {question} | Image: {image_path}")


def log_tool_result(tool_name, result):
    """Placeholder for your logging function."""
    logging.info(f"Tool Result: {tool_name} | Result: {result}")


def defect_percentage_tool(image_path: str, question: str) -> Dict[str, Any]:
    """
    Calculates the percentage of the wafer that is defective.
    This is a mock implementation based on your provided example.
    """
    tool_name = "DefectPercentageCalculator"
    log_tool_usage(tool_name, question, image_path)
    try:
        if not image_path:
            raise ValueError("Missing image path.")

        # --- YOUR ACTUAL DEFECT CALCULATION LOGIC GOES HERE ---
        # For example: defect_percentage, output_image = detect_defects(...)

        if "sem" in image_path:
            return {"result":"The defect percentage cannot be calculated for SEM images.", "image_path": image_path}
        defect_percentage,output_image = detect_defects(npy_path=change_file_path(image_path))
        log_tool_result(tool_name, str(defect_percentage))
        # return str(defect_percentage)
        return {"result": defect_percentage, "image_path": output_image}

    except Exception as e:
        error_msg = f"Error in {tool_name}: {e}"
        log_tool_result(tool_name, error_msg)
        # Propagate the error or handle it as needed
        raise


# --- Agent Definition ---

class PercentageAgent(BaseAgent):
    """An agent specialized in calculating defect percentages."""

    @property
    def name(self) -> str:
        """The unique name of the agent."""
        return "Percentage"

    async def process(self, state: AgentState) -> Dict[str, Any]:
        """
        Executes the defect percentage tool and updates the state.
        """
        # Call the specific tool for this agent
        tool_result = defect_percentage_tool(
            image_path=state["image_path"],
            question=state["question"]
        )

        # Structure the output using the Pydantic model
        data = PercentageData(
            defect_percentage=tool_result["result"],
            output_image_path=tool_result["image_path"]
        )

        # Return the specific state key this agent is responsible for
        return {"percentage_data": data}