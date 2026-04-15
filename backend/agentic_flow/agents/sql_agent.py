import sqlite3,uuid
import logging
import os,re,random
from typing import Any, Dict, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI # Changed from Ollama
from .base import BaseAgent
from data_models.state import AgentState, SQLAnalysisData
from dotenv import load_dotenv
from matplotlib import pyplot as plt
import pandas as pd
import plotly.express as px

# Define the schema context so the LLM knows the tables
DB_SCHEMA = """
Tables:

wafer(wafer_id, lot_id, slot_number, status)
lot(lot_id, product_code, route_id, start_time, end_time)

process_route(route_id, route_name)
process_step(step_id, route_id, step_seq, step_name, operation_type)
process_parameter(parameter_id, step_id, parameter_name, unit, control_low, control_high, spec_low, spec_high)
recipe_version(recipe_id, step_id, version)

wafer_process_run(
  run_id, wafer_id, step_id, tool_id, chamber_id,
  recipe_id, start_time, end_time, pass_flag
)

parameter_measurement(
  measurement_id, run_id, parameter_id, value, measured_at
)

excursion(
  excursion_id, measurement_id, type, severity, detected_at
)

tool(tool_id, tool_name, tool_group)
chamber(chamber_id, tool_id, chamber_name)

tool_sensor_data(
  sensor_id, tool_id, chamber_id, sensor_name, value, measured_at
)

metrology_measurement(
  metro_id, wafer_id, feature_name, measured_value, measured_at
)

wafer_defect(
  defect_id, wafer_id, location_x, location_y,
  severity, defect_type, detected_at, run_id
)
"""

load_dotenv()  

class SQLAgent(BaseAgent):
    def __init__(self):
        # Initializing ChatOpenAI. 
        # Make sure your OPENAI_API_KEY is set in your environment variables.
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0,api_key=os.getenv("OPENAI_API_KEY"))
        self.db_path = "/app/backend/semiconductor_super_v1.db"

    @property
    def name(self) -> str:
        return "SQL"

    async def process(self, state: AgentState) -> Dict[str, Any]:
        # 1. Generate SQL Query using JSON Mode
        # OpenAI models handle "with_structured_output" natively which is even better
        prompt = ChatPromptTemplate.from_template("""
        You are a SQL expert for a semiconductor fab.

        Schema:
        {schema}

        User question:
        "{question}"

        IMPORTANT RULES:
        - You MUST filter results using wafer_id = {wafer_id}
        - The wafer_id is ALWAYS provided — do NOT invent one
        - Use ONLY valid SQLite syntax
        - DO NOT use placeholders like '?'
        - Prefer joins through wafer_process_run when needed
        - Return ONLY JSON in the form: {{ "sql": "SELECT ..." }}
        """)

        wafer_id = self.map_image_to_db_wafer_id(state["image_path"])
        
        # We use .bind(response_format={"type": "json_object"}) for explicit JSON mode
        json_llm = self.llm.bind(response_format={"type": "json_object"})
        chain = prompt | json_llm | JsonOutputParser()

        response = chain.invoke({"schema": DB_SCHEMA, "question": state["question"], "wafer_id": wafer_id})
        sql_query = response["sql"]
        print(f"---SQL AGENT: EXECUTING QUERY: {sql_query}---")
        data = []
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql_query) # Now executing without a second 'bindings' argument
            rows = cursor.fetchall()
            data = [dict(row) for row in rows]
            conn.close()
        except Exception as e:
            print(f"SQL Execution Error: {e}")
            # Optionally provide a fallback summary if the query fails
        print(f"---SQL AGENT: QUERY RETURNED {data} ROWS---")
        graph_path = None
        if len(data) > 1:
            vis_prompt = ChatPromptTemplate.from_template("""
            Based on this data sample: {sample}
            And this user question: "{question}"
            
            Determine if a graph is helpful. If yes, choose the best PRESET type.
            Presets:
            - "LINE": Best for trends over time (X must be a date/time/sequence).
            - "BAR": Best for comparing quantities (X is a category/name).
            - "SCATTER": Best for relationship between two numeric variables.
            - "NONE": If the data doesn't fit these or is just a simple list.

            Return JSON: {{"preset": "BAR", "x_col": "column_name", "y_col": "column_name", "title": "label"}}
            """)
            
            vis_chain = vis_prompt | self.llm.bind(response_format={"type": "json_object"}) | JsonOutputParser()
            vis_choice = vis_chain.invoke({"sample": data[:3], "question": state["question"]})
            print(f"---SQL AGENT: VISUALIZATION CHOICE: {vis_choice}---")
            # --- STEP 4: EXECUTE PRESET PLOTTING CODE ---
            graph_path = self._generate_preset_graph(data, vis_choice)

        # 3. Summarize the findings
        # summary_prompt = ChatPromptTemplate.from_template(
        #     "Data: {data}. Question: {question}. Provide a clear answer based on the data."
        # )
        summary_prompt = ChatPromptTemplate.from_template("""
        You are given QUERY RESULTS from a real database.
        The SQL query has already been executed successfully.

        RULES:
        - Do NOT question data availability
        - Do NOT explain what *could* be done
        - ONLY summarize what the data explicitly shows
        - If rows exist, list findings clearly
        - If no rows exist, explicitly say "Not enough available data found"

        Question:
        {question}

        Query Results:
        {data}

        Write a concise, factual answer.
        """)

        summary_chain = summary_prompt | self.llm
        summary_msg = summary_chain.invoke({"data": data[:20], "question": state["question"]})

        # Update state: include results and mark as completed for the router
        current_completed = state.get("completed_agents", [])
        return {
            "sql_data": SQLAnalysisData(
                query=sql_query,
                data_points=data,
                summary=summary_msg.content # Access .content for OpenAI
            ),
            "completed_agents": current_completed + ["SQL"]
        }
    # def _generate_preset_graph(self, data: List[Dict], config: Dict) -> str:
        """Contains the hardcoded preset plotting templates."""
        preset = config.get("preset", "NONE")
        if preset == "NONE": return None

        try:
            df = pd.DataFrame(data)
            x, y = config["x_col"], config["y_col"]
            plt.figure(figsize=(10, 5))
            
            # PRESET 1: LINE CHART
            if preset == "LINE":
                if 'measured_at' in df.columns or 'start_time' in df.columns:
                    df[x] = pd.to_datetime(df[x])
                df = df.sort_values(by=x)
                plt.plot(df[x], df[y], marker='o', linestyle='-', color='b')
            
            # PRESET 2: BAR CHART
            elif preset == "BAR":
                plt.bar(df[x].astype(str), df[y], color='skyblue')
            
            # PRESET 3: SCATTER PLOT
            elif preset == "SCATTER":
                plt.scatter(df[x], df[y], alpha=0.5, color='green')

            plt.title(config.get("title", "Analysis Result"))
            plt.xlabel(x)
            plt.ylabel(y)
            plt.xticks(rotation=45)
            plt.tight_layout()

            # Save to a plots directory
            os.makedirs("plots", exist_ok=True)
            filename = f"plots/viz_{uuid.uuid4().hex[:6]}.png"
            plt.savefig(filename)
            plt.close()
            return filename
        except Exception as e:
            print(f"Preset Plotting Error: {e}")
            return None

    def _generate_preset_graph(self, data: List[Dict], config: Dict) -> str:
        """Generate interactive Plotly graph and save as HTML."""
        
        preset = config.get("preset", "NONE")
        if preset == "NONE":
            return None

        try:
            df = pd.DataFrame(data)
            x = config.get("x_col")
            y = config.get("y_col")
            title = config.get("title", "Analysis Result")

            if x not in df.columns or y not in df.columns:
                print("Plotly Error: Invalid columns selected")
                return None

            # --- Create Interactive Plot ---
            if preset == "LINE":
                if "measured_at" in df.columns or "start_time" in df.columns:
                    df[x] = pd.to_datetime(df[x])
                df = df.sort_values(by=x)
                fig = px.line(df, x=x, y=y, markers=True, title=title)

            elif preset == "BAR":
                fig = px.bar(df, x=x, y=y, title=title)

            elif preset == "SCATTER":
                fig = px.scatter(df, x=x, y=y, title=title)

            else:
                return None

            # --- Save as HTML ---
            os.makedirs("plots", exist_ok=True)
            filename = f"plots/viz_{uuid.uuid4().hex[:6]}.html"

            fig.write_html(filename, include_plotlyjs="cdn")

            print(f"---SQL AGENT: INTERACTIVE GRAPH SAVED AT {filename}---")
            return filename

        except Exception as e:
            print(f"Plotly Generation Error: {e}")
            return None


    def map_image_to_db_wafer_id(self,image_path: str,total_db_wafers: int = 3000,total_ui_wafers: int = 38) -> int:

        print(image_path)
        # --- Try to extract UI wafer ID ---
        filename = os.path.basename(image_path)
        match = re.search(r"(\d+)", filename)

         # Defensive: ensure image_path is usable
        if not isinstance(image_path, (str, bytes, os.PathLike)):
            image_path = ""

        # If no number found, pick random UI wafer
        if match:
            ui_wafer_id = int(match.group(1))
        else:
            ui_wafer_id = random.randint(1, total_ui_wafers)

        # Clamp UI wafer ID safely
        if ui_wafer_id < 1 or ui_wafer_id > total_ui_wafers:
            ui_wafer_id = random.randint(1, total_ui_wafers)

        # --- Bucket mapping ---
        bucket_size = total_db_wafers // total_ui_wafers
        bucket_start = (ui_wafer_id - 1) * bucket_size + 1
        bucket_end = (
            bucket_start + bucket_size - 1
            if ui_wafer_id < total_ui_wafers
            else total_db_wafers
        )

        # --- Random pick inside bucket ---
        return random.randint(bucket_start, bucket_end)