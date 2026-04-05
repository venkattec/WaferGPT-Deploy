import os
import asyncio
from typing import Dict, Any

from langgraph.graph import StateGraph, END
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.llms import Ollama

# 1. Import State and the Planner
from models.state import AgentState
# We only need the planner, not the old orchestrator node
from router.ollama_orchestrator import planner

# 2. Import all the concrete agent classes
from agents.percentage_agent import PercentageAgent
from agents.localize_agent import LocalizeAgent
from agents.classification_agent import ClassificationAgent
from agents.general_agent import GeneralAgent

# 3. Instantiate your agents
percentage_agent = PercentageAgent()
localize_agent = LocalizeAgent()
classification_agent = ClassificationAgent()
general_agent = GeneralAgent()

# 4. Define LLM and Final Nodes
llm = Ollama(model="llama3.1", temperature=0)


def plan_node(state: AgentState) -> Dict[str, Any]:
    """Creates the initial plan and updates the state. This is a node."""
    print("---PLANNER: CREATING PLAN---")
    plan = planner.invoke({"question": state["question"]})
    print(f"Planned Agents: {plan.required_agents}")
    return {
        "required_agents": plan.required_agents,
        "completed_agents": [],
    }


def route_agents(state: AgentState) -> str:
    """The router that decides which agent to run next. This is a conditional edge function."""
    print("---ROUTER: DECIDING NEXT STEP---")
    completed = state.get("completed_agents", [])
    for agent in state["required_agents"]:
        if agent not in completed:
            print(f"Next agent to run: {agent}")
            return agent.lower() + "_agent_node"

    print("---ROUTER: ALL TASKS COMPLETE---")
    return "final_response_node"


def final_response_node(state: AgentState) -> Dict[str, Any]:
    """Generates the final response draft from all collected data."""
    print("---GENERATING FINAL RESPONSE DRAFT---")
    response = f"Analysis for query: '{state['question']}'\n"
    if data := state.get("percentage_data"):
        response += f"- Defect Percentage: {data.defect_percentage}%\n"
    if data := state.get("localization_data"):
        # locations = [d.description for d in data.defects_found]
        response += f"- Defect Locations: {data.defects_found}\n"
    if data := state.get("classification_data"):
        response += f"- Defect Type: {data.defect_type} (Confidence: {data.confidence_score})\n"
    if data := state.get("general_analysis_data"):
        response += f"- General Summary: {data.summary}\n"
    return {"response": response}


def validation_node(state: AgentState) -> Dict[str, Any]:
    """Validates and rephrases the final response."""
    print("---VALIDATING AND REPHRASING RESPONSE---")
    validation_prompt = ChatPromptTemplate.from_template(
    """You are a semiconductor wafer defect analysis assistant.  
    Your job is to polish and rephrase the draft response so that it:  
    - Directly answers the original question in a natural, fluent way.  
    - Keeps all key metrics (percentages, defect type, location, etc.) exactly as they appear in the draft.  
    - Rewrites fixed or template-like sentences into a smoother, more natural form (1–2 sentences).  
    - Removes unnecessary symbols, redundancy, or robotic phrasing.  
    - Does not add new information or assumptions.  

    Always return only the improved, natural-sounding response. Give only the final answer string, nothing else.

    Original Question: "{question}"  
    Draft AI Response: "{draft_response}"  
    """
    )

    validation_chain = validation_prompt | llm | StrOutputParser()
    final_response = validation_chain.invoke({
        "question": state["question"],
        "draft_response": state["response"]
    })
    return {"response": final_response}


# 5. Assemble the Graph
workflow = StateGraph(AgentState)

# Add the planner node and all the agent/final nodes
workflow.add_node("planner", plan_node)
workflow.add_node("percentage_agent_node", percentage_agent)
workflow.add_node("localize_agent_node", localize_agent)
workflow.add_node("classification_agent_node", classification_agent)
workflow.add_node("general_agent_node", general_agent)
workflow.add_node("final_response_node", final_response_node)
workflow.add_node("validation_node", validation_node)

# The entry point is now the planner
workflow.set_entry_point("planner")

# The routing map for our conditional edges
routing_map = {
    "percentage_agent_node": "percentage_agent_node",
    "localize_agent_node": "localize_agent_node",
    "classification_agent_node": "classification_agent_node",
    "general_agent_node": "general_agent_node",
    "final_response_node": "final_response_node",
}

# The planner connects to the router, which decides the first agent
workflow.add_conditional_edges("planner", route_agents, routing_map)

# After each agent runs, it also goes back to the router to decide the next step
workflow.add_conditional_edges("percentage_agent_node", route_agents, routing_map)
workflow.add_conditional_edges("localize_agent_node", route_agents, routing_map)
workflow.add_conditional_edges("classification_agent_node", route_agents, routing_map)
workflow.add_conditional_edges("general_agent_node", route_agents, routing_map)

# The final nodes connect sequentially
workflow.add_edge("final_response_node", "validation_node")
workflow.add_edge("validation_node", END)

# Compile the final, runnable app
app = workflow.compile()

async def get_answer(question, image_path):
    """Run wafer analysis asynchronously and return the final response."""
    inputs = {
        "question": question,
        "image_path": os.path.abspath(image_path)
    }

    final_response = None

    async for s in app.astream(inputs, stream_mode="values"):
        if "response" in s and s["response"]:
            final_response = s["response"]
        else:
            last_key = list(s.keys())[-1]
            print(f"Step Output ({last_key}):\n{s[last_key]}")

    if final_response is None:
        final_response = "No valid response generated by the model."

    return final_response

# 6. Run the Application
async def run_analysis():
    # question = "Find the largest defect and tell me its type. Also, what is the total defect percentage?"
    question = "is the wafer good or bad? if bad then why?"
    # IMPORTANT: Replace with a real image path
    image_path = r'/app/backend/png_files/image2.png'

    inputs = {
        "question": question,
        "image_path": os.path.abspath(image_path)
    }

    print(f"\n--- Running Analysis for Question: '{question}' ---\n")
    async for s in app.astream(inputs, stream_mode="values"):
        print("---")
        if "response" in s and s["response"]:
            print(f"\nFinal Polished Response:\n{s['response']}")
        else:
            last_key = list(s.keys())[-1]
            print(f"Step Output ({last_key}):\n{s[last_key]}")


if __name__ == "__main__":
    asyncio.run(run_analysis())