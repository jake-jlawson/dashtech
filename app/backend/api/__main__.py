from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
import uvicorn, argparse, asyncio
from contextlib import asynccontextmanager
from core.llm import LLMClient


app = FastAPI()

# Add CORS middleware to allow requests from Tauri frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:1420",  # Vite dev server
        "https://tauri.localhost",  # Tauri production
        "tauri://localhost",  # Tauri custom protocol
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup & Shutdown Methods
async def initialise_llm():
    """Background task to initialise connection to LLM"""
    try:
        print("Starting LLM initialization...", flush=True)
        app.state.llm_client = LLMClient(
            base_url="http://localhost:11434",
            model="gpt-oss:20b",
            keep_alive="30m",
            timeout=None
        )
        # Try to warmup but don't block if Ollama is not available
        try:
            await asyncio.wait_for(app.state.llm_client.warmup(), timeout=5.0)
            app.state.llm_ready = True
            print("LLM initialization completed", flush=True)
        except asyncio.TimeoutError:
            print("LLM warmup timed out - Ollama may not be running", flush=True)
            app.state.llm_ready = False
        except Exception as warmup_error:
            print(f"LLM warmup failed: {warmup_error}", flush=True)
            app.state.llm_ready = False
    except Exception as e:
        print(f"LLM initialization failed: {e}", flush=True)
        app.state.llm_ready = False


# startup and shutdown methods
@app.on_event("startup")
async def startup_event():
    await initialise_llm()


@app.on_event("shutdown")
async def shutdown_event():
    await app.state.llm_client.close()
    print("LLM connection closed", flush=True)





app.include_router(router)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--db", type=str, help="Database path (optional)")
    args = p.parse_args()

    print(f"Starting FastAPI server on port {args.port}")
    if args.db:
        print(f"Database path: {args.db}")
    
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="info")

if __name__ == "__main__":
    main()