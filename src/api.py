import os
import sys
import asyncio
import subprocess
import json
from fastapi import FastAPI, BackgroundTasks, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

app = FastAPI(title="TrafficRadius Prospect Audit Generator")

# Build absolute paths for static elements
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "output")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")

class AuditRequest(BaseModel):
    domain: str
    company_name: str

# In-memory "database" to track status and logs
jobs = {}
job_logs = {}
history_store = []

async def run_audit_job(job_id: str, domain: str, company: str):
    """Background task to run the pipeline visually via subprocess."""
    jobs[job_id]["status"] = "running"
    jobs[job_id]["message"] = "Starting audit pipeline..."
    job_logs[job_id] = []
    
    # The instruction implies the script path and cwd might change relative to BASE_DIR
    # Assuming the user wants to run the script from the parent directory (where .env is)
    # and the script itself is now in a 'src' subdirectory relative to that parent.
    # This means BASE_DIR is 'api', and the script is in 'src' relative to the project root.
    project_root_dir = os.path.join(BASE_DIR, "..")
    script_path = os.path.join(project_root_dir, "src", "langgraph_orchestrator.py")
    
    try:
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-u", script_path, domain, company,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=project_root_dir, # Run from the project root directory
            env=env
        )
        
        while True:
            try:
                line = await asyncio.wait_for(process.stdout.readline(), timeout=15.0)
                if not line:
                    break
                decoded_line = line.decode('utf-8').strip()
                if decoded_line:
                    job_logs[job_id].append(decoded_line)
            except asyncio.TimeoutError:
                # This timeout is for the subprocess stdout, not for the SSE client.
                # The log streaming function handles SSE keep-alives.
                # We just continue waiting for output from the subprocess.
                pass # No action needed here, just prevent the loop from breaking
                
        await process.wait()
        
        if process.returncode == 0:
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["message"] = "Audit completed successfully."
        else:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["message"] = f"Pipeline failed with exit code {process.returncode}"
            
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = f"Pipeline failed: {str(e)}"

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serves the main frontend UI."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/start-audit")
async def start_audit(domain: str = Form(...), company: str = Form(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    import uuid
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "starting", "message": "Initializing...", "domain": domain}
    job_logs[job_id] = ["Initializing LangGraph Orchestrator..."]
    
    background_tasks.add_task(run_audit_job, job_id, domain, company)
    return JSONResponse({"job_id": job_id})

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        return JSONResponse({"error": "Job not found"}, status_code=404)
    return JSONResponse(jobs[job_id])

@app.get("/api/stream-logs/{job_id}")
async def stream_logs(job_id: str):
    """Server-Sent Events endpoint for real-time terminal logs."""
    async def log_generator():
        last_idx = 0
        while True:
            if job_id not in job_logs:
                yield f"data: {{\"log\": \"[System Error] Job context lost.\"}}\n\n"
                break
                
            current_logs = job_logs[job_id]
            if last_idx < len(current_logs):
                for i in range(last_idx, len(current_logs)):
                    yield f"data: {json.dumps({'log': current_logs[i]})}\n\n"
                last_idx = len(current_logs)
            
            # Check if job is done
            if job_id in jobs and jobs[job_id]["status"] in ["completed", "failed"]:
                # Yield any final logs that might have slipped through
                if last_idx < len(job_logs[job_id]):
                    for i in range(last_idx, len(job_logs[job_id])):
                        yield f"data: {json.dumps({'log': job_logs[job_id][i]})}\n\n"
                yield f"data: {{\"done\": true, \"status\": \"{jobs[job_id]['status']}\"}}\n\n"
                break
                
            await asyncio.sleep(0.5)
            
    return StreamingResponse(log_generator(), media_type="text/event-stream")

@app.get("/api/history")
async def get_history():
    """Returns the history of completed audits from the vault."""
    archives_dir = os.path.join(OUTPUT_DIR, "archives")
    if not os.path.exists(archives_dir):
        return JSONResponse({"history": []})
        
    history = []
    for folder in os.listdir(archives_dir):
        meta_path = os.path.join(archives_dir, folder, "metadata.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r") as f:
                    history.append(json.load(f))
            except Exception:
                pass
                
    # Sort newest first
    history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return JSONResponse({"history": history})

if __name__ == "__main__":
    import uvicorn
    # Create static dir if not exists
    os.makedirs(STATIC_DIR, exist_ok=True)
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
