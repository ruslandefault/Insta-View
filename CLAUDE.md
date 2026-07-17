# Insta View — Claude Code yo'riqnomasi

## Loyiha haqida
Fullstack ilova: **FastAPI** backend + **React (Vite)** frontend.

## Texnologiyalar
- **Backend:** Python 3.11+, FastAPI, Uvicorn, Pydantic v2, pydantic-settings
- **Frontend:** React 18, Vite 6
- **OS:** Windows (PowerShell)

## Loyiha tuzilishi
- `backend/app/main.py` — FastAPI ilovasi va endpointlar
- `backend/app/config.py` — sozlamalar (`.env` orqali)
- `backend/requirements.txt` — Python paketlari
- `frontend/src/` — React komponentlari
- `frontend/vite.config.js` — Vite + `/api` proxy → `localhost:8000`

## Buyruqlar

### Backend
```bash
cd backend
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm run dev
```

## Qoidalar / konvensiyalar
- Backend port: **8000**, Frontend port: **5173**
- Frontend backendga faqat `/api/...` prefiksi orqali murojaat qiladi (Vite proxy).
- Yangi API endpointlar `/api/...` ostida bo'lsin.
- Maxfiy qiymatlar faqat `.env` da (git'ga tushmaydi). `.env.example` ni yangilab turing.
- Kod izohlari va commit xabarlari o'zbek tilida bo'lishi mumkin.

## Muhim
- `.env` faylini HECH QACHON commit qilmang.
- Python kodda Pydantic v2 sintaksisidan foydalaning (v1 emas).
