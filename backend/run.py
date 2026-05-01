"""Punto de entrada local. Usa: python run.py"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",   # escucha en toda la red local
        port=8000,
        reload=True,       # quita reload=True en producción
    )
