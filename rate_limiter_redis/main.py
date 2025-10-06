
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis 
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
from fastapi.requests import Request

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Welcome! FastAPI with Rate Limiter is running 🚀"}



@app.on_event("startup")
async def startup():
    # Connect to Redis running locally (port 6379)
    r = redis.from_url("redis://localhost", encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(r)



@app.get("/limited", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def limited_endpoint():
    return {"message": "You can only access this endpoint 5 times per minute."}


@app.get("/burst", dependencies=[Depends(RateLimiter(times=2, seconds=10))])
async def burst_endpoint():
    return {"message": "This endpoint allows 2 requests every 10 seconds."}

@app.get("/other",dependencies=[Depends(RateLimiter(times=1,seconds=2))])
async def other_endpoint():
    return {"message":"This endpoint allows 1 request every 2 seconds."}



@app.exception_handler(HTTP_429_TOO_MANY_REQUESTS)
async def rate_limit_exceeded_handler(request: Request, exc):
    return JSONResponse(
        status_code=HTTP_429_TOO_MANY_REQUESTS,
        content={"error": "Rate limit exceeded. Please try again later."},
    )



