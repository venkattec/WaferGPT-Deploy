import os
import asyncio
from typing import Dict, Any
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# 1. Import the State and Orchestrator
from data_models.state import AgentState
from router.ollama_orchestrator import orchestrator_node,planner_node,router

# 2. Import all the concrete agent classes
from agents.percentage_agent import PercentageAgent
from agents.localize_agent import LocalizeAgent
from agents.classification_agent import ClassificationAgent
from agents.general_agent import GeneralAgent
from agents.sql_agent import SQLAgent

# 3. Instantiate your agents
percentage_agent = PercentageAgent()
localize_agent = LocalizeAgent()
classification_agent = ClassificationAgent()
general_agent = GeneralAgent()
sql_agent = SQLAgent()

load_dotenv()  
# 4. Define the Final Response and Validation Nodes
llm = ChatOpenAI(model="gpt-4o", temperature=0,api_key=os.getenv("OPENAI_API_KEY"))

def final_response_node(state: AgentState) -> Dict[str, Any]:
    """Generates the final response draft from all collected data."""
    print("---GENERATING FINAL RESPONSE DRAFT---")
    response = f"Analysis for query: '{state['question']}'\n"
    if data := state.get("percentage_data"):
        response += f"- Defect Percentage: {data.defect_percentage}%\n"
    if data := state.get("localization_data"):
        locations = [d for d in data.defects_found]
        response += f"- Defect Locations: {', '.join(locations)}\n"
    if data := state.get("classification_data"):
        response += f"- Defect Type: {data.defect_type} (Confidence: {data.confidence_score})\n"
    if data := state.get("general_analysis_data"):
        response += f"- General Summary: {data.summary}\n"
    if data := state.get("sql_data"):
        response += f"- Database Insight: {data.summary}\n"
        response += f"  (Query used: {data.query})\n"
    return {"response": response}

def validation_node(state: AgentState) -> Dict[str, Any]:
    """Validates and rephrases the final response."""
    print("---VALIDATING AND REPHRASING RESPONSE---")
    validation_prompt = ChatPromptTemplate.from_template(
        """You are a quality control assistant. Review and polish this draft response based on the original question.
        Original Question: "{question}"
        Draft AI Response: "{draft_response}"
        Return only the final, improved response."""
    )
    validation_chain = validation_prompt | llm | StrOutputParser()
    final_response = validation_chain.invoke({
        "question": state["question"],
        "draft_response": state["response"]
    })
    return {"response": final_response}


# 5. Assemble the Graph
workflow = StateGraph(AgentState)

# Add all nodes
# workflow.add_node("orchestrator", orchestrator_node)
workflow.add_node("planner", planner_node) # Changed from "orchestrator"
# We pass the agent *instances*, which are callable thanks to the __call__ method in BaseAgent
workflow.add_node("percentage_agent_node", percentage_agent)
workflow.add_node("localize_agent_node", localize_agent)
workflow.add_node("classification_agent_node", classification_agent)
workflow.add_node("general_agent_node", general_agent)
workflow.add_node("sql_agent_node", sql_agent)
workflow.add_node("final_response_node", final_response_node)
workflow.add_node("validation_node", validation_node)

# Set the entry point
# workflow.set_entry_point("orchestrator")
workflow.set_entry_point("planner")

# # Define all the edges
# workflow.add_conditional_edges(
#     "orchestrator",
#     lambda next_node: next_node,
#     {
#         "percentage_agent_node": "percentage_agent_node",
#         "localize_agent_node": "localize_agent_node",
#         "classification_agent_node": "classification_agent_node",
#         "general_agent_node": "general_agent_node",
#         "sql_agent_node": "sql_agent_node",
#         "final_response_node": "final_response_node"
#     }
# )

# Define the routing map
routing_map = {
    "percentage_agent_node": "percentage_agent_node",
    "localize_agent_node": "localize_agent_node",
    "classification_agent_node": "classification_agent_node",
    "general_agent_node": "general_agent_node",
    "sql_agent_node": "sql_agent_node",
    "final_response_node": "final_response_node"
}
workflow.add_conditional_edges("planner", router, routing_map)

workflow.add_conditional_edges("percentage_agent_node", router, routing_map)
workflow.add_conditional_edges("localize_agent_node", router, routing_map)
workflow.add_conditional_edges("classification_agent_node", router, routing_map)
workflow.add_conditional_edges("general_agent_node", router, routing_map)
workflow.add_conditional_edges("sql_agent_node", router, routing_map)

# Final sequence
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
    question = "Which tools have the highest number of excursions? Show me the top 5."
    image_path = "/home/sbna/Documents/WaferGPT-Backend/png_files/image7.png"

    inputs = {
        "question": question,
        "image_path": os.path.abspath(image_path)
    }

    print(f"\n--- Running Analysis for Question: '{question}' ---\n")
    # Use astream for the async version
    async for s in app.astream(inputs, stream_mode="values"):
        print("---")
        if "response" in s and s["response"]:
            print(f"\nFinal Polished Response:\n{s['response']}")
        else:
            last_step = list(s.keys())[-1]
            print(f"Step Output ({last_step}):\n{s[last_step]}")

if __name__ == "__main__":
    # To run the async stream, we use asyncio.run()
    asyncio.run(run_analysis())