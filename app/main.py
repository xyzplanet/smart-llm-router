from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
import uvicorn
from fastapi import FastAPI
from app.router.proxy import router as proxy_router
from app.core.config import settings
from app.router.llm import router as llm_router

# Initialize application middleware core
app = FastAPI(title="Local AI Smart Gateway")

# Include your existing proxy router
app.include_router(proxy_router)

# Mount the operational proxy routing module
app.include_router(llm_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
    

if __name__ == "__main__":
    # Launch the Uvicorn ASGI Web Server locally on Port 8000
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)