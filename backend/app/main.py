from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(title=settings.app_name, debug=settings.debug)

# React frontend bilan bog'lanish uchun CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Insta View API ishlayapti 🚀"}


@app.get("/api/health")
def health():
    return {"status": "ok"}
