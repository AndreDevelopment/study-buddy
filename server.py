import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import your chunking/storage functions and agent executor
from ingestion import load_and_split_notes, store_chunks_in_vector_db
from agent import agent_executor

app = FastAPI()

# Enable CORS so your React/Vue frontend can talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "./notes"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class QueryRequest(BaseModel):
    question: str

@app.post("/upload")
async def upload_notes(file: UploadFile = File(...)):
    """Receives a note file, saves it to the notes directory, and re-indexes the DB."""
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Run your ingestion pipeline dynamically on the new file
        chunks = load_and_split_notes()
        if chunks:
            store_chunks_in_vector_db(chunks)
            
        return {"message": f"Successfully uploaded and indexed '{file.filename}'!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
def ask_agent(request: QueryRequest):
    """Sends a user query to the LangGraph agent and returns the response."""
    try:
        response = agent_executor.invoke({
            "messages": [("human", request.question)]
        })
        answer = response["messages"][-1].content
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))