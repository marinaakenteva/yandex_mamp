import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.map_routes import router as map_router

app = FastAPI(title="Map Generator API")

app.include_router(map_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


def start() -> None:
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    start()