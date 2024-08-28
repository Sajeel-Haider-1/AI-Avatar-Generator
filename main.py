import uvicorn
import httpx
import os
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse,JSONResponse
from auth import get_current_user
from gradio_utils import create_gradio_interface
import gradio as gr

app = FastAPI()

RUNPOD_RUN_URL = os.getenv("RUNPOD_RUN_URL")
RUNPOD_TOKEN = os.getenv("RUNPOD_API_KEY")
RUNPOD_STATUS_URL = os.getenv("RUNPOD_STATUS_URL")
REDIRECT_URI = os.getenv("REDIRECT_URI")
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

gr_interface = create_gradio_interface()

gr.mount_gradio_app(app, gr_interface, path="/gradio")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    token = request.query_params.get("access_token")
    print(f"Token in home: {token}")
    if token:
        try:
            await get_current_user(token)
            return RedirectResponse(url=f"/gradio?access_token={token}")
        except HTTPException:
            return JSONResponse(
                content={"detail": "Invalid request. Account not allowed, try with a different email."},
            )
    else:
        return RedirectResponse(url="/login")

@app.get("/login")
async def login():
    auth_url = (
        f"https://accounts.google.com/o/oauth2/auth"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=openid%20email%20profile"
        f"&access_type=offline"
    )
    return RedirectResponse(auth_url)

@app.get("/callback")
async def callback(request: Request):
    try:
        code = request.query_params.get("code")
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code not found",
            )
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "redirect_uri": REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            token_response.raise_for_status()
            tokens = token_response.json()
            access_token = tokens["access_token"]
            print("Print Access",access_token)
            return RedirectResponse(url=f"/?access_token={access_token}")
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred. Please try again."},
        )
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
