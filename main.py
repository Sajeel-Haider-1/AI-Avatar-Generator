import uvicorn
import httpx
import os
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from auth import get_current_user, set_user_email
from gradio_utils import create_gradio_interface

app = FastAPI()

RUNPOD_RUN_URL = os.getenv("RUNPOD_RUN_URL")
RUNPOD_TOKEN = os.getenv("RUNPOD_API_KEY")
RUNPOD_STATUS_URL = os.getenv("RUNPOD_STATUS_URL")
REDIRECT_URI = os.getenv("REDIRECT_URI")
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    token = request.query_params.get("access_token")
    print(f"Token in home: {token}")
    if token:
        try:
            await get_current_user(token)
            return RedirectResponse(url=f"/gradio?access_token={token}")
        except HTTPException:
            return RedirectResponse(url="/login")
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
    
    return RedirectResponse(url=f"/?access_token={access_token}")

def launch_gradio_interface():
    interface = create_gradio_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        inbrowser=False,
        show_error=True,
        prevent_thread_lock=True,
        max_threads=1 
    )
    return 

@app.get("/gradio", response_class=HTMLResponse)
async def gradio_interface(request: Request):
    access_token = request.query_params.get("access_token")
    print(f"Token in Gradio: {access_token}")  
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token missing",
        )
    user_info = await get_current_user(access_token)
    print("User info",user_info['email'])
    set_user_email(user_info['email'])
    launch_gradio_interface()
    gradio_url = "http://127.0.0.1:7860/"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gradio App</title>
    </head>
    <body>
        <h1>Gradio App</h1>
        <iframe src="{gradio_url}" style="width: 100%; height: 100vh; border: none;"></iframe>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
