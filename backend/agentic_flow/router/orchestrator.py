from typing import List

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

# Import the shared state definition from your models package
from models.state import AgentState

# --- 1. LLM Configuration ---
# This can be defined here or imported from a central config file.
llm = ChatOpenAI(model="gpt-4o", temperature=0,api_key=)


# --- 2. Planner Definition ---
# This Pydantic model defines the structure of the plan.
class Plan(BaseModel):
    """A plan of which agents to run to answer the user's query."""
    required_agents: List[str] = Field(
        description="A list of agent names (in order) that are required to fully answer the query. Choose from: [Percentage, Localize, Classification, General]",
    )


# The planner chain uses the LLM to create a plan based on the user's question.
planner_llm = llm.with_structured_output(Plan)

planner_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", """You are a master semiconductor analysis planner. 
        Your job is to create a step-by-step plan by selecting the necessary specialist agents to answer the user's query.

        You must choose from the following available agents:
        - **Percentage**: Use for questions about calculating defect percentages.
        - **Localize**: Use for questions about finding or locating defects.
        - **Classification**: Use for questions about the type or class of a defect.
        - **General**: Use for general descriptions or broad questions about the image.

        Based on the user's question, create a plan by listing the agents that need to be called in the correct order. For example, if the user asks to "find and classify the defect", you should respond with ["Localize", "Classification"].
        """),
        ("human", "Question: {question}"),
    ]
)

planner = planner_prompt | planner_llm


# --- 3. Orchestrator Node ---
# This is the main function you will import into your graph assembly file.
def orchestrator_node(state: AgentState):
    """
    The central router that plans and dispatches agents.
    """
    # If a plan doesn't exist yet, create one. This is the "planning" step.
    if "required_agents" not in state or not state.get("required_agents"):
        print("---ORCHESTRATOR: PLANNING---")
        plan = planner.invoke({"question": state["question"]})
        state["required_agents"] = plan.required_agents
        state["completed_agents"] = []  # Initialize completed agents list
    else:
        print("---ORCHESTRATOR: ROUTING---")

    # Determine the next agent to run based on the plan. This is the "routing" step.
    completed = state.get("completed_agents", [])
    for agent in state["required_agents"]:
        if agent not in completed:
            print(f"Next agent to run: {agent}")
            # The return value is the name of the next node in the graph.
            return agent.lower() + "_agent_node"

    # If all planned agents have been completed, move to the final response step.
    print("---ORCHESTRATOR: ALL TASKS COMPLETE---")
    return "final_response_node"