from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
import uvicorn, argparse, asyncio
from contextlib import asynccontextmanager
from core.llm import LLMClient, initialise_llm
from core.issue import IssueManager


"""
Lifespan for the app
"""
@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialise_llm(app)
    app.state.issue_manager = IssueManager()
    try:
        yield
    finally:
        if hasattr(app.state, "llm_client"):
            await app.state.llm_client.close()
        print("LLM connection closed", flush=True)


app = FastAPI(lifespan=lifespan)


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