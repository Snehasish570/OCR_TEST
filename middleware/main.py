from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from time import time

app = FastAPI()

request_log = {}
RATE_LIMIT = 5      
WINDOW_TIME = 30     

@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    client_ip = request.client.host
    current_time = time()
    if client_ip not in request_log:
        request_log[client_ip] = []
    
    request_log[client_ip] = [t for t in request_log[client_ip] if current_time - t < WINDOW_TIME]

    if len(request_log[client_ip]) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Too Many Requests",
                "message": f"Rate limit exceeded. Try again after {int(WINDOW_TIME - (current_time - request_log[client_ip][0]))}s"
            }
        )

    request_log[client_ip].append(current_time)
    response = await call_next(request)
    return response

@app.get("/")
def home():
    return {"message": "Welcome to FastAPI custom rate limiter!"}

@app.get("/hello")
def hello():
    return {"message": "Hello, User! You are under custom rate limiting"}