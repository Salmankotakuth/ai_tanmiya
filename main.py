from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers (to be implemented in /app/api/*)
from app.api import (
    meeting_controller,
    score_controller,
    prediction_controller,
    report_controller,
    pdf_controller,
)
from app.utils import http_client

# ---------------------------
# FastAPI App
# ---------------------------
app = FastAPI(
    title="Tanmiya AI Backend",
    version="1.0.0",
    description="AI-powered scoring and reporting system for Tanmiya.",
)

# ---------------------------
# Startup & Shutdown Events
# ---------------------------
@app.on_event("startup")
async def startup_event():
    await http_client.init()   # initializes global HTTP client

@app.on_event("shutdown")
async def shutdown_event():
    await http_client.close()  # closes global HTTP client

# ---------------------------
# CORS (minimal & safe)
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Change to specific domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Routers
# ---------------------------
app.include_router(meeting_controller.router, prefix="/meetings", tags=["Meetings"])
app.include_router(score_controller.router, prefix="/scores", tags=["Scores"])
app.include_router(prediction_controller.router, prefix="/predictions", tags=["Predictions"])
app.include_router(report_controller.router, prefix="/reports", tags=["Reports"])
app.include_router(pdf_controller.router, prefix="/pdf", tags=["PDF"])

# ---------------------------
# Health Check
# ---------------------------
@app.get("/healthz", tags=["Health"])
async def healthz():
    return {"status": "ok"}


@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to the Tanmiya AI Backend API!"}


# ---------------------------------------------------------------------
# Run with: uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
# ---------------------------------------------------------------------

# ---------------------------
# Local run helper
# ---------------------------
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)