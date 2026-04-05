import logging,os
from typing import Any, Dict, List, Tuple

# Assumes your state models and base agent are in these locations
from models.state import AgentState, LocalizationData, DefectLocation
from agents.tools.localizeDefect import detect_and_localize_defects
from agents.tools.locate_sem import locate_sem_defect
from .base import BaseAgent


# --- Tool Definition ---
# IMPORTANT: This section should import your actual tools.
# For this example, we'll define mock tools that include logging.
# from tools import log_tool_usage, log_tool_result, locate_sem_defect, ...

def log_tool_usage(tool_name, question, image_path):
    """Placeholder for your logging function."""
    logging.info(f"Tool Used: {tool_name} | Question: {question} | Image: {image_path}")


def log_tool_result(tool_name, result):
    """Placeholder for your logging function."""
    logging.info(f"Tool Result: {tool_name} | Result: {result}")


# def locate_sem_defect(image_path: str) -> tuple[str, str]:
#     """Placeholder for your SEM defect location tool."""
#     # Mocking a successful result for an SEM image
#     output =  "center region"
#     output_image = "/path/to/output/sem_defect.png"
#     return output, output_image


# def detect_and_localize_defects(npy_path: str) -> tuple[str, str]:
#     """Placeholder for your standard defect location tool."""
#     # Mocking a successful result for a standard wafer image
#     output = "top-left quadrant"
#     output_image = "/path/to/output/localized_defect.png"
#     return output, output_image


def change_file_path(input_path):
    directory, file_name = os.path.split(input_path)
    new_directory = directory.replace('png_files', 'npy_files')
    new_file_name = os.path.splitext(file_name)[0] + '.npy'
    new_path = os.path.join(new_directory, new_file_name)
    return new_path

def defect_localize_tool(image_path: str, question: str) -> Dict[str, Any]:
    """
    Localizes the largest defect in the wafer image.
    (This is your provided tool function)
    """
    tool_name = "DefectLocalizer"
    log_tool_usage(tool_name, question, image_path)
    try:
        if not image_path:
            raise ValueError("Missing image path.")

        if "sem" in image_path:
            output, output_image = locate_sem_defect(image_path)
        else:
            output, output_image = detect_and_localize_defects(npy_path=change_file_path(image_path))

        result = {"result": output, "image_path": output_image}
        log_tool_result(tool_name, str(result))
        return result

    except Exception as e:
        error_msg = f"Error in {tool_name}: {e}"
        log_tool_result(tool_name, error_msg)
        raise


# --- Agent Definition ---

class LocalizeAgent(BaseAgent):
    """An agent specialized in localizing defects on a wafer."""

    @property
    def name(self) -> str:
        """The unique name of the agent."""
        return "Localize"

    async def process(self, state: AgentState) -> Dict[str, Any]:
        """
        Executes the defect localization tool and updates the state.
        """
        # Call the specific tool for this agent
        tool_result = defect_localize_tool(
            image_path=state["image_path"],
            question=state["question"]
        )

        # Process the raw tool output into a list of DefectLocation Pydantic models
        # defects = [
        #     DefectLocation(
        #         bounding_box=d["box"],
        #         center_point=d["center"],
        #         description=d["desc"],
        #         is_largest=d["largest"]
        #     )
        #     for d in tool_result["result"]
        # ]

        # Structure the final output using the main Pydantic model for this agent
        data = LocalizationData(
            defects_found=tool_result["result"],
            output_image_path=tool_result["image_path"]
        )

        # Return the specific state key this agent is responsible for
        return {"localization_data": data}