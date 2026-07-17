# Insta View

Fullstack loyiha — **FastAPI** (backend) + **React/Vite** (frontend).

## Tuzilishi

```
insta-view/
├── backend/          # FastAPI API
│   ├── app/
│   │   ├── main.py   # ilova kirish nuqtasi
│   │   └── config.py # sozlamalar (.env)
│   ├── requirements.txt
│   └── .env.example
└── frontend/         # React + Vite
    ├── src/
    └── package.json
```

## Ishga tushirish

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows (PowerShell: .venv\Scripts\Activate.ps1)
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload  # http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev                    # http://localhost:5173
```

Frontend `/api` so'rovlarini avtomatik backendga (`:8000`) yo'naltiradi.
