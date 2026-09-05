from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

class EmailAlreadyExistsException(Exception):
    pass

class UserNameAlreadyExistsException(Exception): 
    pass

@app.exception_handler(EmailAlreadyExistsException)
async def email_already_exists(request: Request, exc: EmailAlreadyExistsException):
    return JSONResponse(status_code=409, content={"detail": str(exc)})

@app.exception_handler(EmailAlreadyExistsException)
async def username_already_exists(request: Request, exc: UserNameAlreadyExistsException):
    return JSONResponse(status_code=409, content={"detail": str(exc)})