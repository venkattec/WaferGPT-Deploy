import sqlite3
import random
import datetime

"""
 +-------------------+          +----------------------+
 |   process_route   |1 ------< |    process_step      |
 +-------------------+          +----------------------+
 | route_id (PK)     |          | step_id (PK)         |
 | route_name        |          | route_id (FK)        |
 +-------------------+          | step_seq             |
                                | step_name            |
                                | operation_type       |
                                +----------------------+
                                           |
                             has parameters|
                                           v
                                +-----------------------+
                                |   process_parameter   |
                                +-----------------------+
                                | parameter_id (PK)     |
                                | step_id (FK)          |
                                | parameter_name        |
                                | unit                  |
                                | control_low/high      |
                                | spec_low/high         |
                                +-----------------------+

 +------------------+           +------------------+
 |       lot        |1 ------< |     wafer        |
 +------------------+           +------------------+
 | lot_id (PK)      |           | wafer_id (PK)    |
 | product_code     |           | lot_id (FK)      |
 | route_id (FK)    |           | slot_number      |
 | start_time       |           | status           |
 | end_time         |           +------------------+
 +------------------+                     |
                                           |
                                           v
                          +-----------------------------------+
                          |       wafer_process_run           |
                          +-----------------------------------+
                          | run_id (PK)                       |
                          | wafer_id (FK)                     |
                          | step_id (FK)                      |
                          | tool_id (FK)                      |
                          | chamber_id (FK)                   |
                          | recipe_id (FK)                    |
                          | start_time / end_time             |
                          | pass_flag                         |
                          +-----------------------------------+
                                |                     |
       produces measurements     |                     | uses
                                v                     v
                      +------------------+     +------------------+
                      | parameter_meas.  |     | recipe_version   |
                      +------------------+     +------------------+
                      | measurement_id   |     | recipe_id (PK)   |
                      | run_id (FK)      |     | step_id (FK)     |
                      | parameter_id(FK) |     | version          |
                      | value            |     +------------------+
                      | measured_at      |
                      +------------------+
                             |
                             v
                      +----------------+
                      |   excursion    |
                      +----------------+
                      | excursion_id   |
                      | measurement_id |
                      | type, severity |
                      | detected_at    |
                      +----------------+

 +------------+       has chambers       +----------------+
 |    tool    |1 ----------------------< |    chamber     |
 +------------+                          +----------------+
 | tool_id PK |                          | chamber_id PK  |
 | tool_name  |                          | tool_id  FK    |
 | tool_group |                          | chamber_name   |
 +------------+                          +----------------+
       |
       | undergoes
       v
 +----------------+
 |  maintenance   |
 +----------------+
 | maint_id PK    |
 | tool_id FK     |
 | chamber_id FK  |
 | start_time     |
 | end_time       |
 | notes          |
 +----------------+

 wafer -> metrology measurements
            |
            v
 +-------------------------+
 |  metrology_measurement  |
 +-------------------------+
 | metro_id (PK)           |
 | wafer_id (FK)           |
 | feature_name            |
 | measured_value          |
 | measured_at             |
 +-------------------------+

 wafer -> defects
            |
            v
 +----------------+
 |  wafer_defect  |
 +----------------+
 | defect_id PK   |
 | wafer_id FK    |
 | location_x/y   |
 | severity/type  |
 | detected_at    |
 | run_id FK      |
 +----------------+
    {
        "description": "Get all defective wafers with their run, tool, and chamber",
        "query": 
SELECT wd.wafer_id, wd.defect_type, wd.severity, wd.detected_at, wpr.run_id, t.tool_name, c.chamber_name
FROM wafer_defect wd
JOIN wafer_process_run wpr ON wd.run_id = wpr.run_id
JOIN tool t ON wpr.tool_id = t.tool_id
JOIN chamber c ON wpr.chamber_id = c.chamber_id;

    },
    {
        "description": "Find all parameter excursions for a given wafer",
        "query": 
SELECT pm.parameter_id, pm.value, e.type, e.severity, e.detected_at
FROM wafer_process_run wpr
JOIN parameter_measurement pm ON wpr.run_id = pm.run_id
LEFT JOIN excursion e ON e.measurement_id = pm.measurement_id
WHERE wpr.wafer_id = 123; -- replace 123 with actual wafer_id

    },
    {
        "description": "Get tool sensor readings for a wafer run",
        "query": 
SELECT tsd.sensor_name, tsd.value, tsd.measured_at
FROM wafer_process_run wpr
JOIN tool_sensor_data tsd
  ON tsd.tool_id = wpr.tool_id
  AND tsd.measured_at BETWEEN wpr.start_time AND wpr.end_time
WHERE wpr.wafer_id = 123; -- replace 123 with actual wafer_id

    },
    {
        "description": "Metrology measurement trends for a wafer",
        "query": SELECT feature_name, measured_value, measured_at
FROM metrology_measurement
WHERE wafer_id = 123
ORDER BY measured_at;

    },
    {
        "description": "List tools with most excursions",
        "query": 
SELECT t.tool_name, COUNT(e.excursion_id) AS num_excursions
FROM excursion e
JOIN parameter_measurement pm ON e.measurement_id = pm.measurement_id
JOIN wafer_process_run wpr ON pm.run_id = wpr.run_id
JOIN tool t ON wpr.tool_id = t.tool_id
GROUP BY t.tool_name
ORDER BY num_excursions DESC;

    }
]


"""

# -------------------------
# CONFIG
# -------------------------
DB_NAME = "semiconductor_super_v1.db"
NUM_LOTS = 150
WAFERS_PER_LOT = 20
PROCESS_ROUTES = 5
STEPS_PER_ROUTE = 6

# Full fab tool list with variable chambers
TOOLS = {
    "Etcher": 4,
    "Deposition": 4,
    "CMP": 2,
    "Implanter": 2,
    "Scanner": 1,
    "SEM": 1,
    "CD-SEM": 1,
    "AFM": 1,
    "Cleaner": 2,
    "Inspector": 1
}

PARAMETERS = ["Pressure","Temp","Flow","Time","Voltage"]
SENSOR_NAMES = ["Pressure_Sensor","Temp_Sensor","Flow_Sensor","Voltage_Sensor"]
FEATURES = ["CD","Thickness","Resistivity","Roughness"]

# Fab simulation period: 3 months
FAB_START = datetime.datetime(2026, 1, 1, 8, 0, 0)
FAB_END   = FAB_START + datetime.timedelta(days=360)

# -------------------------
# HELPER FUNCTIONS
# -------------------------
def random_datetime(start, end):
    """Return random datetime between start and end"""
    delta = end - start
    seconds = random.randint(0, int(delta.total_seconds()))
    return start + datetime.timedelta(seconds=seconds)

def rand_val(low, high):
    return round(random.uniform(low, high), 2)

# -------------------------
# CONNECT DB
# -------------------------
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

# -------------------------
# CREATE TABLES (same as before)
# -------------------------
c.executescript("""

CREATE TABLE IF NOT EXISTS process_route(
    route_id INTEGER PRIMARY KEY,
    route_name TEXT
);

CREATE TABLE IF NOT EXISTS process_step(
    step_id INTEGER PRIMARY KEY,
    route_id INTEGER,
    step_seq INTEGER,
    step_name TEXT,
    operation_type TEXT,
    FOREIGN KEY(route_id) REFERENCES process_route(route_id)
);

CREATE TABLE IF NOT EXISTS process_parameter(
    parameter_id INTEGER PRIMARY KEY,
    step_id INTEGER,
    parameter_name TEXT,
    unit TEXT,
    control_low REAL,
    control_high REAL,
    spec_low REAL,
    spec_high REAL,
    FOREIGN KEY(step_id) REFERENCES process_step(step_id)
);

CREATE TABLE IF NOT EXISTS recipe_version(
    recipe_id INTEGER PRIMARY KEY,
    step_id INTEGER,
    version TEXT,
    FOREIGN KEY(step_id) REFERENCES process_step(step_id)
);

CREATE TABLE IF NOT EXISTS lot(
    lot_id INTEGER PRIMARY KEY,
    product_code TEXT,
    route_id INTEGER,
    start_time TEXT,
    end_time TEXT,
    FOREIGN KEY(route_id) REFERENCES process_route(route_id)
);

CREATE TABLE IF NOT EXISTS wafer(
    wafer_id INTEGER PRIMARY KEY,
    lot_id INTEGER,
    slot_number INTEGER,
    status TEXT,
    FOREIGN KEY(lot_id) REFERENCES lot(lot_id)
);

CREATE TABLE IF NOT EXISTS wafer_process_run(
    run_id INTEGER PRIMARY KEY,
    wafer_id INTEGER,
    step_id INTEGER,
    tool_id INTEGER,
    chamber_id INTEGER,
    recipe_id INTEGER,
    start_time TEXT,
    end_time TEXT,
    pass_flag INTEGER,
    FOREIGN KEY(wafer_id) REFERENCES wafer(wafer_id),
    FOREIGN KEY(step_id) REFERENCES process_step(step_id),
    FOREIGN KEY(tool_id) REFERENCES tool(tool_id),
    FOREIGN KEY(chamber_id) REFERENCES chamber(chamber_id),
    FOREIGN KEY(recipe_id) REFERENCES recipe_version(recipe_id)
);

CREATE TABLE IF NOT EXISTS parameter_measurement(
    measurement_id INTEGER PRIMARY KEY,
    run_id INTEGER,
    parameter_id INTEGER,
    value REAL,
    measured_at TEXT,
    FOREIGN KEY(run_id) REFERENCES wafer_process_run(run_id),
    FOREIGN KEY(parameter_id) REFERENCES process_parameter(parameter_id)
);

CREATE TABLE IF NOT EXISTS excursion(
    excursion_id INTEGER PRIMARY KEY,
    measurement_id INTEGER,
    type TEXT,
    severity TEXT,
    detected_at TEXT,
    FOREIGN KEY(measurement_id) REFERENCES parameter_measurement(measurement_id)
);

CREATE TABLE IF NOT EXISTS tool(
    tool_id INTEGER PRIMARY KEY,
    tool_name TEXT,
    tool_group TEXT
);

CREATE TABLE IF NOT EXISTS chamber(
    chamber_id INTEGER PRIMARY KEY,
    tool_id INTEGER,
    chamber_name TEXT,
    FOREIGN KEY(tool_id) REFERENCES tool(tool_id)
);

CREATE TABLE IF NOT EXISTS maintenance(
    maint_id INTEGER PRIMARY KEY,
    tool_id INTEGER,
    chamber_id INTEGER,
    start_time TEXT,
    end_time TEXT,
    notes TEXT,
    FOREIGN KEY(tool_id) REFERENCES tool(tool_id),
    FOREIGN KEY(chamber_id) REFERENCES chamber(chamber_id)
);

CREATE TABLE IF NOT EXISTS tool_sensor_data(
    sensor_id INTEGER PRIMARY KEY,
    tool_id INTEGER,
    chamber_id INTEGER,
    sensor_name TEXT,
    value REAL,
    measured_at TEXT,
    FOREIGN KEY(tool_id) REFERENCES tool(tool_id),
    FOREIGN KEY(chamber_id) REFERENCES chamber(chamber_id)
);

CREATE TABLE IF NOT EXISTS metrology_measurement(
    metro_id INTEGER PRIMARY KEY,
    wafer_id INTEGER,
    feature_name TEXT,
    measured_value REAL,
    measured_at TEXT,
    FOREIGN KEY(wafer_id) REFERENCES wafer(wafer_id)
);

CREATE TABLE IF NOT EXISTS wafer_defect(
    defect_id INTEGER PRIMARY KEY,
    wafer_id INTEGER,
    location_x INTEGER,
    location_y INTEGER,
    severity TEXT,
    defect_type TEXT,
    detected_at TEXT,
    run_id INTEGER,
    FOREIGN KEY(wafer_id) REFERENCES wafer(wafer_id),
    FOREIGN KEY(run_id) REFERENCES wafer_process_run(run_id)
);

""")
conn.commit()

# -------------------------
# POPULATE PROCESS ROUTES & STEPS
# -------------------------
route_ids = []
for i in range(1, PROCESS_ROUTES+1):
    route_name = f"Route_{i}"
    c.execute("INSERT INTO process_route(route_name) VALUES (?)", (route_name,))
    route_id = c.lastrowid
    route_ids.append(route_id)
    for step_seq in range(1, STEPS_PER_ROUTE+1):
        step_name = f"Step_{step_seq}"
        op_type = random.choice(list(TOOLS.keys()))
        c.execute("INSERT INTO process_step(route_id, step_seq, step_name, operation_type) VALUES (?,?,?,?)",
                  (route_id, step_seq, step_name, op_type))
        step_id = c.lastrowid
        # Add parameters for this step
        for param_name in PARAMETERS:
            low = rand_val(10, 50)
            high = low + rand_val(5, 15)
            spec_low = low - rand_val(1,5)
            spec_high = high + rand_val(1,5)
            c.execute("""INSERT INTO process_parameter(step_id, parameter_name, unit, control_low, control_high, spec_low, spec_high)
                         VALUES (?,?,?,?,?,?,?)""",
                      (step_id, param_name, "units", low, high, spec_low, spec_high))
        # Add a recipe
        c.execute("INSERT INTO recipe_version(step_id, version) VALUES (?,?)", (step_id,f"v{random.randint(1,5)}"))
conn.commit()

# -------------------------
# POPULATE TOOLS & CHAMBERS
# -------------------------
tool_ids = []
for tool_group, num_instances in TOOLS.items():
    for i in range(1, num_instances+1):
        tool_name = f"{tool_group}-{i:02d}"
        c.execute("INSERT INTO tool(tool_name, tool_group) VALUES (?,?)",(tool_name, tool_group))
        tool_id = c.lastrowid
        tool_ids.append(tool_id)
        # Assign chambers per tool type
        chambers_for_tool = 1
        if tool_group in ["Etcher","Deposition","CMP","Cleaner"]:
            chambers_for_tool = 2
        elif tool_group in ["Implanter"]:
            chambers_for_tool = 2
        else:
            chambers_for_tool = 1
        for ch in range(1,chambers_for_tool+1):
            chamber_name = f"{tool_name}_C{ch}"
            c.execute("INSERT INTO chamber(tool_id,chamber_name) VALUES (?,?)",(tool_id,chamber_name))
conn.commit()

# -------------------------
# POPULATE LOTS & WAFERS OVER 3 MONTHS
# -------------------------
wafer_ids = []
lot_ids = []
for lot_num in range(1, NUM_LOTS+1):
    product_code = f"P{random.randint(100,999)}"
    route_id = random.choice(route_ids)
    start_time = random_datetime(FAB_START, FAB_END)
    end_time = start_time + datetime.timedelta(hours=random.randint(1,5))
    c.execute("INSERT INTO lot(product_code,route_id,start_time,end_time) VALUES (?,?,?,?)",
              (product_code, route_id, start_time.isoformat(), end_time.isoformat()))
    lot_id = c.lastrowid
    lot_ids.append(lot_id)
    for slot in range(1,WAFERS_PER_LOT+1):
        status = random.choice(["Good","Pending"])
        c.execute("INSERT INTO wafer(lot_id,slot_number,status) VALUES (?,?,?)",(lot_id,slot,status))
        wafer_ids.append(c.lastrowid)
conn.commit()

# -------------------------
# POPULATE WAFER RUNS, MEASUREMENTS, EXCURSIONS, SENSORS
# -------------------------
for wafer_id in wafer_ids:
    # Get route for this wafer
    c.execute("""SELECT route_id,start_time FROM lot WHERE lot_id=(SELECT lot_id FROM wafer WHERE wafer_id=?)""",(wafer_id,))
    route_id, lot_start = c.fetchone()
    lot_start = datetime.datetime.fromisoformat(lot_start)
    # Get steps
    c.execute("SELECT step_id, operation_type FROM process_step WHERE route_id=? ORDER BY step_seq", (route_id,))
    steps = c.fetchall()
    wafer_start = lot_start
    for step_id, op_type in steps:
        # pick tool from same operation type
        c.execute("SELECT tool_id FROM tool WHERE tool_group=? ORDER BY RANDOM() LIMIT 1",(op_type,))
        tool_id = c.fetchone()[0]
        c.execute("SELECT chamber_id FROM chamber WHERE tool_id=? ORDER BY RANDOM() LIMIT 1",(tool_id,))
        chamber_id = c.fetchone()[0]
        c.execute("SELECT recipe_id FROM recipe_version WHERE step_id=? ORDER BY RANDOM() LIMIT 1",(step_id,))
        recipe_id = c.fetchone()[0]
        step_start = wafer_start + datetime.timedelta(minutes=random.randint(5,30))
        step_end = step_start + datetime.timedelta(minutes=random.randint(10,60))
        pass_flag = random.choice([0,1])
        c.execute("""INSERT INTO wafer_process_run(wafer_id,step_id,tool_id,chamber_id,recipe_id,start_time,end_time,pass_flag)
                     VALUES (?,?,?,?,?,?,?,?)""",
                  (wafer_id,step_id,tool_id,chamber_id,recipe_id,step_start.isoformat(),step_end.isoformat(),pass_flag))
        run_id = c.lastrowid
        # Measurements
        c.execute("SELECT parameter_id,control_low,control_high,spec_low,spec_high FROM process_parameter WHERE step_id=?",(step_id,))
        for pid,cl,ch,spec_l,spec_h in c.fetchall():
            val = rand_val(cl-5,ch+5)
            meas_time = step_start + datetime.timedelta(minutes=random.randint(0,int((step_end-step_start).seconds/60)))
            c.execute("""INSERT INTO parameter_measurement(run_id,parameter_id,value,measured_at)
                         VALUES (?,?,?,?)""",(run_id,pid,val,meas_time.isoformat()))
            measurement_id = c.lastrowid
            # Excursion if out of spec
            if val < spec_l or val > spec_h:
                exc_type = "High" if val>spec_h else "Low"
                severity = random.choice(["Minor","Major"])
                c.execute("""INSERT INTO excursion(measurement_id,type,severity,detected_at)
                             VALUES (?,?,?,?)""",(measurement_id,exc_type,severity,meas_time.isoformat()))
        # Tool sensor data
        for sname in SENSOR_NAMES:
            val = rand_val(10,100)
            ts_time = step_start + datetime.timedelta(minutes=random.randint(0,int((step_end-step_start).seconds/60)))
            c.execute("""INSERT INTO tool_sensor_data(tool_id,chamber_id,sensor_name,value,measured_at)
                         VALUES (?,?,?,?,?)""",(tool_id,chamber_id,sname,val,ts_time.isoformat()))
        wafer_start = step_end
conn.commit()

# -------------------------
# METROLOGY & DEFECTS
# -------------------------
for wafer_id in wafer_ids:
    for feature in FEATURES:
        val = rand_val(10,100)
        meas_time = random_datetime(FAB_START,FAB_END)
        c.execute("""INSERT INTO metrology_measurement(wafer_id,feature_name,measured_value,measured_at)
                     VALUES (?,?,?,?)""",(wafer_id,feature,val,meas_time.isoformat()))
    # Random defects (~5%)
    if random.random()<0.05:
        loc_x = random.randint(1,100)
        loc_y = random.randint(1,100)
        severity = random.choice(["Low","Medium","High"])
        defect_type = random.choice(["Particle","Scratch","Pattern"])
        detected_at = random_datetime(FAB_START,FAB_END)
        c.execute("SELECT run_id FROM wafer_process_run WHERE wafer_id=? ORDER BY RANDOM() LIMIT 1",(wafer_id,))
        run_id = c.fetchone()[0]
        c.execute("""INSERT INTO wafer_defect(wafer_id,location_x,location_y,severity,defect_type,detected_at,run_id)
                     VALUES (?,?,?,?,?,?,?)""",(wafer_id,loc_x,loc_y,severity,defect_type,detected_at.isoformat(),run_id))
conn.commit()

# -------------------------
# TOOL MAINTENANCE OVER 3 MONTHS
# -------------------------
for tool_id in tool_ids:
    c.execute("SELECT chamber_id FROM chamber WHERE tool_id=?", (tool_id,))
    chambers = [r[0] for r in c.fetchall()]
    for _ in range(random.randint(2,5)):
        maint_start = random_datetime(FAB_START,FAB_END)
        maint_end = maint_start + datetime.timedelta(hours=random.randint(1,8))
        chamber_id = random.choice(chambers)
        notes = "Routine maintenance"
        c.execute("""INSERT INTO maintenance(tool_id,chamber_id,start_time,end_time,notes)
                     VALUES (?,?,?,?,?)""",(tool_id,chamber_id,maint_start.isoformat(),maint_end.isoformat(),notes))
conn.commit()

print(f"Database {DB_NAME} created simulating 12 months fab operation.")
conn.close()

