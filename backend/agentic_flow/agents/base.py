from abc import ABC, abstractmethod
from typing import Any, Dict

# Import the shared state definition from your models package
from models.state import AgentState


class BaseAgent(ABC):
    """
    An abstract base class for all specialist agents in the workflow.

    This class defines a standard interface for agents, ensuring they can be
    seamlessly integrated into the LangGraph workflow. It includes input

    validation and requires concrete agents to implement their core logic.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique name of the agent."""
        pass

    @abstractmethod
    async def process(self, state: AgentState) -> Dict[str, Any]:
        """
        The core logic of the agent.

        This method processes the current state, performs its specific task
        (e.g., calling a tool, running a model), and returns a dictionary
        containing the updates to be merged back into the main state.

        Args:
            state: The current state of the workflow.

        Returns:
            A dictionary with keys corresponding to the AgentState fields
            that need to be updated.
        """
        pass

    def validate_inputs(self, state: AgentState) -> None:
        """
        Validates that the required inputs for the agent are present in the state.
        By default, it checks for 'question' and 'image_path'.

        Args:
            state: The current state of the workflow.

        Raises:
            ValueError: If a required key is missing from the state.
        """
        required_keys = ["question", "image_path"]
        for key in required_keys:
            if key not in state or state[key] is None:
                raise ValueError(f"Missing required key '{key}' in state for agent '{self.name}'")

    async def __call__(self, state: AgentState) -> Dict[str, Any]:
        """
        The entry point for calling the agent as a node in LangGraph.

        This method first validates the inputs and then executes the agent's
        core `process` logic. It also adds standardized logging.
        """
        print(f"---EXECUTING {self.name.upper()} AGENT---")
        self.validate_inputs(state)
        # The 'await' is used because our process method is async
        result = await self.process(state)

        # Add the agent's name to the list of completed agents
        completed = state.get("completed_agents", []) + [self.name]
        result["completed_agents"] = completed

        return result