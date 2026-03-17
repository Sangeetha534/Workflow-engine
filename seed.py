import json
import requests
import time

API_BASE = "http://127.0.0.1:8001/api"

def create_expense_workflow():
    print("Creating Expense Approval Workflow...")
    
    # 1. Create Workflow
    wf_res = requests.post(f"{API_BASE}/workflows", json={
        "name": "Expense Approval",
        "description": "Auto-approve small expenses, manual review for large ones."
    })
    wf = wf_res.json()
    wf_id = wf['id']
    print(f"Created Workflow ID: {wf_id}")
    
    # 2. Create Steps
    steps = [
        {"name": "Submit Expense", "step_type": "start"}, # ID: 1
        {"name": "Auto Approved", "step_type": "end"},    # ID: 2
        {"name": "Manual Review", "step_type": "action"}, # ID: 3
        {"name": "Rejected", "step_type": "end"}          # ID: 4
    ]
    
    created_steps = {}
    for step in steps:
        res = requests.post(f"{API_BASE}/workflows/{wf_id}/steps", json=step)
        created = res.json()
        created_steps[created['name']] = created['id']
        print(f"Created Step '{created['name']}' with ID: {created['id']}")
        
    s_submit = created_steps["Submit Expense"]
    s_auto = created_steps["Auto Approved"]
    s_manual = created_steps["Manual Review"]
    s_rejected = created_steps["Rejected"]
    
    # 3. Create Rules
    rules = [
        # From Submit Expense -> Auto Approve if amount <= 100
        {
            "step_id": s_submit,
            "condition": "amount <= 100",
            "priority": 10,
            "next_step_id": s_auto
        },
        # From Submit Expense -> Manual Review if amount > 100
        {
            "step_id": s_submit,
            "condition": "amount > 100",
            "priority": 5,
            "next_step_id": s_manual
        },
        # Default rule for Submit Expense as a fallback
        {
            "step_id": s_submit,
            "condition": "DEFAULT",
            "priority": 0,
            "next_step_id": s_manual
        },
        # From Manual Review -> Reject if country != US
        {
            "step_id": s_manual,
            "condition": "country != 'US'",
            "priority": 10,
            "next_step_id": s_rejected
        },
        # Manual Review -> Auto (meaning approved by reviewer)
        {
            "step_id": s_manual,
            "condition": "department == 'Engineering'",
            "priority": 5,
            "next_step_id": s_auto
        },
        # Default rule for manual review
        {
            "step_id": s_manual,
            "condition": "DEFAULT",
            "priority": 0,
            "next_step_id": s_rejected
        }
    ]
    
    for rule in rules:
        step_id = rule.pop("step_id")
        requests.post(f"{API_BASE}/steps/{step_id}/rules", json=rule)
        print(f"Added rule: '{rule['condition']}' to Step ID {step_id}")
        
    print("\nSeed complete! You can now load this workflow in the UI.")

if __name__ == "__main__":
    try:
        # Check if backend is running
        requests.get(f"{API_BASE}/workflows")
        create_expense_workflow()
    except Exception as e:
        print("Could not connect to backend. Please ensure the FastAPI server is running.")
