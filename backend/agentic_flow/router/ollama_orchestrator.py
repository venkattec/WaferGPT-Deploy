from typing import List

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_community.llms import Ollama
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
import os
# Import the shared state definition from your models package
from models.state import AgentState

# --- 1. LLM Configuration (Updated for Ollama) ---
# We specify the model and tell it to always output in JSON format.
# Make sure you have the 'llama3' model pulled in Ollama: `ollama pull llama3`
# llm = Ollama(model="llama3.1", format="json", temperature=0)
llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))


# --- 2. Planner Definition (Updated for JSON Mode) ---

class Plan(BaseModel):
    """A plan of which agents to run to answer the user's query."""
    required_agents: List[str] = Field(
        description="A list of agent names (in order) required. Choose from: [Percentage, Localize, Classification,SQL, General]",
    )


# Create a parser that will convert the LLM's JSON output into our Pydantic `Plan` object.
parser = PydanticOutputParser(pydantic_object=Plan)

# Update the prompt to include instructions for generating JSON.
planner_prompt = ChatPromptTemplate.from_template(
    """You are a master planner specializing in semiconductor wafer analysis. 
    Your role is to decide which specialist agents are strictly required to answer the user's question. 
    Do not include extra agents. Select only those directly needed for a complete answer.

    {format_instructions}

    Available agents and their responsibilities:
    - **Percentage**: Use only for questions explicitly asking for the proportion of defective area 
        on the wafer (e.g., "What is the defect density?").
    - **Localize**: Use only for questions about the physical coordinates or regions of defects 
        (e.g., "Where is the scratch?").
    - **Classification**: Use only for identifying the type or category of a defect 
        (e.g., "What kind of defect is this?").
     - **SQL**: Use for any questions that require querying the fab database at the wafer level.
        This includes:
        • wafer history across process steps (wafer_process_run)
        • parameter measurements and excursions (parameter_measurement, excursion)
        • tool and chamber usage (tool, chamber)
        • metrology measurements (metrology_measurement)
        • defect records (wafer_defect)
        • tool sensor data or maintenance events
        Examples:
        "Find all excursions for this wafer",
        "Which tool and chamber processed this wafer?",
        "Did this wafer experience any out-of-spec parameters?",
        "Show metrology trends for this wafer",
        "Is this defect associated with a specific tool or step?"
    - **General**: Use only for high-level reasoning that requires synthesizing all data. 
        Examples: Root cause summaries, fixing advice, or broad wafer descriptions.

    Rules:
    - Pick the minimal set. If the user asks "Find the defect and see if the tool had an excursion," 
      you must pick ["Localize", "SQL"].
    - Always include **SQL** for questions involving:
        • tools, chambers, recipes, or steps
        • parameter excursions or SPC
        • metrology or defect history
    - Use **General** only if the query cannot be answered solely by the other specialists.

    Example:  
    Question: "Locate the defect and check the maintenance log for that tool."  
    Answer: {{"required_agents": ["Localize", "SQL"]}}

    Question: {question}
    """,
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

# The new planner chain uses the prompt, the Ollama LLM, and the Pydantic parser.
planner = planner_prompt | llm | parser


# --- 3. Orchestrator Node (No changes needed here) ---
# This function remains exactly the same because it still receives a `Plan` object.
def orchestrator_node(state: AgentState):
    """
    The central router that plans and dispatches agents.
    """
    if "required_agents" not in state or not state.get("required_agents"):
        print("---ORCHESTRATOR: PLANNING---")
        plan = planner.invoke({"question": state["question"]})
        state["required_agents"] = plan.required_agents
        state["completed_agents"] = []
    else:
        print("---ORCHESTRATOR: ROUTING---")

    completed = state.get("completed_agents", [])
    for agent in state["required_agents"]:
        if agent not in completed:
            print(f"Next agent to run: {agent}")
            return agent.lower() + "_agent_node"

    print("---ORCHESTRATOR: ALL TASKS COMPLETE---")
    return "final_response_node"

def planner_node(state: AgentState):
    """
    A dedicated NODE that only handles planning and updates the state.
    """
    print("---PLANNER: CREATING PLAN---")
    # This returns a dictionary to update the state
    plan = planner.invoke({"question": state["question"]})
    return {
        "required_agents": plan.required_agents,
        "completed_agents": []
    }

def router(state: AgentState):
    """
    A ROUTER function for conditional edges. It returns a string.
    """
    print("---ROUTER: DECIDING NEXT STEP---")
    completed = state.get("completed_agents", [])
    
    # Check each required agent against the completed list
    for agent in state["required_agents"]:
        if agent not in completed:
            print(f"Next agent to run: {agent}")
            return agent.lower() + "_agent_node"

    print("---ROUTER: ALL TASKS COMPLETE---")
    return "final_response_node"