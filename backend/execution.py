import sqlite3
import json
from . import schemas
from .engine import evaluate_condition

def execute_workflow(db: sqlite3.Connection, workflow_id: int, start_step_id: int, data: dict) -> int:
    cursor = db.cursor()
    cursor.execute("SELECT id FROM workflows WHERE id = ?", (workflow_id,))
    if not cursor.fetchone():
        raise ValueError("Workflow not found")
    
    cursor.execute("INSERT INTO executions (workflow_id, status) VALUES (?, ?)", (workflow_id, "running"))
    db.commit()
    execution_id = cursor.lastrowid

    current_step_id = start_step_id
    step_count = 0
    max_steps = 100 # prevent infinite loops

    while current_step_id and step_count < max_steps:
        step_count += 1
        
        cursor.execute("SELECT * FROM steps WHERE id = ?", (current_step_id,))
        step = cursor.fetchone()
        
        if not step:
            _log_and_stop(db, execution_id, current_step_id, "error - step not found")
            break
        
        # Evaluate rules for current step
        cursor.execute("SELECT * FROM rules WHERE step_id = ? ORDER BY priority DESC", (current_step_id,))
        rules = cursor.fetchall()
        
        matched_rule = None
        evaluated_rules_log = []
        
        for rule in rules:
            is_match = evaluate_condition(rule['condition'], data)
            evaluated_rules_log.append({
                "condition": rule['condition'],
                "result": is_match
            })
            if is_match:
                matched_rule = rule
                break
        
        next_step_id = matched_rule['next_step_id'] if matched_rule else None
        
        # Log this step transition
        cursor.execute('''
            INSERT INTO execution_logs (execution_id, step_name, evaluated_rules, next_step, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            execution_id,
            step['name'],
            json.dumps(evaluated_rules_log),
            str(next_step_id) if next_step_id else None,
            "completed" if next_step_id else "ended"
        ))
        db.commit()

        if not next_step_id:
            cursor.execute("UPDATE executions SET status = ? WHERE id = ?", ("completed", execution_id))
            db.commit()
            break
            
        current_step_id = next_step_id

    if step_count >= max_steps:
        cursor.execute("UPDATE executions SET status = ? WHERE id = ?", ("error - loop detected", execution_id))
        db.commit()
    
    return execution_id
    
def _log_and_stop(db: sqlite3.Connection, execution_id: int, step_id: int, status: str):
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO execution_logs (execution_id, step_name, evaluated_rules, next_step, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        execution_id,
        f"Unknown step {step_id}",
        json.dumps([]),
        None,
        status
    ))
    cursor.execute("UPDATE executions SET status = ? WHERE id = ?", (status, execution_id))
    db.commit()
