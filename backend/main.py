import sqlite3
import json
from fastapi import FastAPI, Depends, HTTPException
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from . import schemas, execution
from .database import get_db, init_db

init_db()

app = FastAPI(title="Workflow Automation System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/workflows", response_model=schemas.Workflow)
def create_workflow(workflow: schemas.WorkflowCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("INSERT INTO workflows (name, description) VALUES (?, ?)", 
                   (workflow.name, workflow.description))
    db.commit()
    wf_id = cursor.lastrowid
    return {"id": wf_id, "name": workflow.name, "description": workflow.description, "steps": []}

@app.get("/api/workflows", response_model=List[schemas.Workflow])
def get_workflows(skip: int = 0, limit: int = 100, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM workflows LIMIT ? OFFSET ?", (limit, skip))
    workflows = [dict(row) for row in cursor.fetchall()]
    return workflows

@app.post("/api/workflows/{workflow_id}/steps", response_model=schemas.Step)
def create_step(workflow_id: int, step: schemas.StepCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("INSERT INTO steps (workflow_id, name, step_type) VALUES (?, ?, ?)",
                   (workflow_id, step.name, step.step_type))
    db.commit()
    return {"id": cursor.lastrowid, "workflow_id": workflow_id, "name": step.name, "step_type": step.step_type, "rules": []}

@app.get("/api/workflows/{workflow_id}/steps", response_model=List[schemas.Step])
def get_steps(workflow_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM steps WHERE workflow_id = ?", (workflow_id,))
    steps = [dict(row) for row in cursor.fetchall()]
    for step in steps:
        cursor.execute("SELECT * FROM rules WHERE step_id = ? ORDER BY priority DESC", (step['id'],))
        step['rules'] = [dict(row) for row in cursor.fetchall()]
    return steps

@app.post("/api/steps/{step_id}/rules", response_model=schemas.Rule)
def create_rule(step_id: int, rule: schemas.RuleCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("INSERT INTO rules (step_id, condition, priority, next_step_id) VALUES (?, ?, ?, ?)",
                   (step_id, rule.condition, rule.priority, rule.next_step_id))
    db.commit()
    return {"id": cursor.lastrowid, "step_id": step_id, "condition": rule.condition, "priority": rule.priority, "next_step_id": rule.next_step_id}

@app.post("/api/workflows/{workflow_id}/execute", response_model=schemas.Execution)
def execute_wf(workflow_id: int, request: schemas.ExecuteRequest, db: sqlite3.Connection = Depends(get_db)):
    try:
        ex_id = execution.execute_workflow(db, workflow_id, request.start_step_id, request.data)
        
        cursor = db.cursor()
        cursor.execute("SELECT * FROM executions WHERE id = ?", (ex_id,))
        ex_row = dict(cursor.fetchone())
        
        cursor.execute("SELECT * FROM execution_logs WHERE execution_id = ?", (ex_id,))
        logs = []
        for row in cursor.fetchall():
            log_dict = dict(row)
            log_dict['evaluated_rules'] = json.loads(log_dict['evaluated_rules']) if log_dict['evaluated_rules'] else []
            logs.append(log_dict)
            
        ex_row['logs'] = logs
        return ex_row
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
        
@app.get("/api/executions/{execution_id}", response_model=schemas.Execution)
def get_execution(execution_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM executions WHERE id = ?", (execution_id,))
    ex_row = cursor.fetchone()
    if not ex_row:
        raise HTTPException(status_code=404, detail="Execution not found")
        
    ex_row = dict(ex_row)
    cursor.execute("SELECT * FROM execution_logs WHERE execution_id = ?", (execution_id,))
    logs = []
    for row in cursor.fetchall():
        log_dict = dict(row)
        log_dict['evaluated_rules'] = json.loads(log_dict['evaluated_rules']) if log_dict['evaluated_rules'] else []
        logs.append(log_dict)
        
    ex_row['logs'] = logs
    return ex_row
