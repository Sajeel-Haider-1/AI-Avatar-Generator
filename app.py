from flask import Flask, render_template_string, redirect, url_for, session
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import os
import gradio as gr
import threading
import base64
import io
import requests
from PIL import Image
import secrets

load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")
sdapi_url = os.getenv("SDAPI_URL")

app.config['GOOGLE_CLIENT_ID'] = os.getenv("GOOGLE_CLIENT_ID")
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv("GOOGLE_CLIENT_SECRET")
app.config['GOOGLE_DISCOVERY_URL'] = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    server_metadata_url=app.config['GOOGLE_DISCOVERY_URL'],
    client_kwargs={
        'scope': 'openid email profile',
    }
)

ALLOWED_USERS = os.getenv("ALLOWED_USERS", "").split(",")

def generate_nonce():
    return secrets.token_urlsafe(16)

@app.route('/')
def homepage():
    user = dict(session).get('user', None)
    return redirect(url_for('gradio_interface')) if user else redirect(url_for('login'))

@app.route('/login')
def login():
    redirect_uri = url_for('auth', _external=True)
    session['nonce'] = generate_nonce()
    return google.authorize_redirect(redirect_uri, nonce=session['nonce'])

@app.route('/auth')
def auth():
    try:
        token = google.authorize_access_token()
        user_info = google.parse_id_token(token, nonce=session.get('nonce'))
    except Exception as e:
        print(f"Error: {e}")
        return "Error during OAuth process", 500

    if 'email' not in user_info or user_info['email'] not in ALLOWED_USERS:
        return "Access Denied", 403

    session['user'] = user_info
    return redirect(url_for('gradio_interface'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

def create_gradio_interface():
    interface = gr.Interface(
        fn=output_window,
        inputs=[
            gr.Textbox(lines=1, placeholder="Prompt Text Here...", label="Prompt"),
            gr.Textbox(lines=1, placeholder="Negative Prompt Text Here...", label="Negative Prompt"),
            gr.Slider(1, 10, value=1, step=1, label="Number of Generations"),
            gr.Image(type="numpy", label="Pose Image (Optional)"),
            gr.Image(type="numpy", label="Face Swap Image (Optional)")
        ],
        outputs=[
            gr.Gallery(label="Generated Images"),
            gr.Textbox(label="Debug Info")
        ],
        live=False,
        title="AI Image Generator"
    )
    return interface

def output_window(prompt, negative_prompt, slider_value, pose_image, face_swap_image):
    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "seed": -1,
        "sampler_name": "DPM++ 2M Karras",
        "steps": 15,
        "cfg_scale": 7,
        "width": 512,
        "height": 768,
        "restore_faces": False,
        "n_iter": slider_value
    }

    if pose_image is not None:
        try:
            img = Image.fromarray(pose_image)
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_base64_control_net = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
        except Exception as e:
            print(e)
            img_base64_control_net = None

        args_control_net = [
            {
                "enabled": True,
                "image": img_base64_control_net,
                "module": "openpose",
                "model": "control_sd15_openpose [fef5e48e]",
            }
        ]

        payload["alwayson_scripts"] = {"controlnet": {"args": args_control_net}}

    if face_swap_image is not None:
        try:
            img = Image.fromarray(face_swap_image)
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_base64_reactor = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
        except Exception as e:
            print(e)
            img_base64_reactor = None

        args_reactor = [
            img_base64_reactor, #0
            True, #1 Enable ReActor
            '0', #2 Comma separated face number(s) from swap-source image
            '0', #3 Comma separated face number(s) for target image (result)
            'inswapper_128.onnx', #4 model path
            'CodeFormer', #4 Restore Face: None; CodeFormer; GFPGAN
            1, #5 Restore visibility value
            True, #7 Restore face -> Upscale
            '4x_NMKD-Superscale-SP_178000_G', #8 Upscaler (type 'None' if doesn't need), see full list here: http://127.0.0.1:7860/sdapi/v1/script-info -> reactor -> sec.8
            1.5, #9 Upscaler scale value
            1, #10 Upscaler visibility (if scale = 1)
            False, #11 Swap in source image
            True, #12 Swap in generated image
            1, #13 Console Log Level (0 - min, 1 - med or 2 - max)
            0, #14 Gender Detection (Source) (0 - No, 1 - Female Only, 2 - Male Only)
            0, #15 Gender Detection (Target) (0 - No, 1 - Female Only, 2 - Male Only)
            False, #16 Save the original image(s) made before swapping
            0.8, #17 CodeFormer Weight (0 = maximum effect, 1 = minimum effect), 0.5 - by default
            False, #18 Source Image Hash Check, True - by default
            False, #19 Target Image Hash Check, False - by default
            "CUDA", #20 CPU or CUDA (if you have it), CPU - by default
            True, #21 Face Mask Correction
            0, #22 Select Source, 0 - Image, 1 - Face Model, 2 - Source Folder
            "elena.safetensors", #23 Filename of the face model (from "models/reactor/faces"), e.g. elena.safetensors
            "", #24 The path to the folder containing source faces images
            None, #25 skip it for API
            True, #26 Randomly select an image from the path
            True, #27 Force Upscale even if no face found
            0.6, #28 Face Detection Threshold
            2, #29 Maximum number of faces to detect (0 is unlimited)
        ]

        payload["alwayson_scripts"] = {"reactor": {"args": args_reactor}}

    response = requests.post(sdapi_url + "/sdapi/v1/txt2img", json=payload)
    if response.status_code == 200:
        response_json = response.json()
        image_base64 = response_json['images'][0]
        return image_base64
    else:
        print("Request failed with status code:", response.status_code)
        return None

def launch_gradio_interface():
    interface = create_gradio_interface()
    interface.launch(server_name="0.0.0.0", server_port=7860, share=True, inbrowser=False, show_error=True, prevent_thread_lock=True)

@app.route('/gradio')
def gradio_interface():
    user = dict(session).get('user', None)
    if user:
        return render_template_string('<iframe src="http://127.0.0.1:7860" width="100%" height="100%"></iframe>')
    return redirect(url_for('login'))

if __name__ == "__main__":
    gradio_thread = threading.Thread(target=launch_gradio_interface)
    gradio_thread.start()
    app.run(host='0.0.0.0', port=8080, debug=False)
