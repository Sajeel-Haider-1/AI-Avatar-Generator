from runpod_utils import update_job_status, get_job_status
from gcs_utils import save_images_to_gcs
from firestore_utils import update_job_status_in_firestore
from auth import get_user_email
import requests
import os
from PIL import Image
import io
import base64
import time 
import gradio as gr
from io import BytesIO

RUNPOD_RUN_URL = os.getenv("RUNPOD_RUN_URL")
RUNPOD_TOKEN = os.getenv("RUNPOD_API_KEY")
RUNPOD_STATUS_URL = os.getenv("RUNPOD_STATUS_URL")
REDIRECT_URI = os.getenv("REDIRECT_URI")

def process_images(image_list):
    processed_images = []
    for image_binary in image_list:
        try:
            img = Image.open(io.BytesIO(image_binary))
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
            processed_images.append(img_base64)
        except Exception as e:
            print(f"Error processing image:", e)
            continue
    return processed_images

def prepare_payload(prompt, negative_prompt, slider_value, pose_images, face_swap_images):
    payload = {
        "input": {
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
    }

    if pose_images:
        control_net_args = []
        for img in pose_images:
            args = {
                "enabled": True,
                "image": img,
                "module": "openpose",
                "model": "control_sd15_openpose [fef5e48e]",
            }
            control_net_args.append(args)
        payload["input"]["alwayson_scripts"] = {"controlnet": {"args": control_net_args}}

    if face_swap_images:
        reactor_args = []
        for img in face_swap_images:
            args = [
                img,  # 0
                True,  # 1 Enable ReActor
                '0',  # 2 Comma separated face number(s) from swap-source image
                '0',  # 3 Comma separated face number(s) for target image (result)
                'inswapper_128.onnx',  # 4 model path
                'CodeFormer',  # 5 Restore Face: None; CodeFormer; GFPGAN
                1,  # 6 Restore visibility value
                True,  # 7 Restore face -> Upscale
                '4x_NMKD-Superscale-SP_178000_G',  # 8 Upscaler
                1.5,  # 9 Upscaler scale value
                1,  # 10 Upscaler visibility (if scale = 1)
                False,  # 11 Swap in source image
                True,  # 12 Swap in generated image
                1,  # 13 Console Log Level
                0,  # 14 Gender Detection (Source)
                0,  # 15 Gender Detection (Target)
                False,  # 16 Save the original image(s) before swapping
                0.8,  # 17 CodeFormer Weight
                False,  # 18 Source Image Hash Check
                False,  # 19 Target Image Hash Check
                "CUDA",  # 20 CPU or CUDA
                True,  # 21 Face Mask Correction
                0,  # 22 Select Source (0 - Image, 1 - Face Model, 2 - Source Folder)
                "elena.safetensors",  # 23 Filename of the face model
                "C:\PATH_TO_FACES_IMAGES",  # 24 The path to the folder containing source faces images
                None,  # 25 skip it for API
                True,  # 26 Randomly select an image from the path
                True,  # 27 Force Upscale even if no face found
                0.6,  # 28 Face Detection Threshold
                2,  # 29 Maximum number of faces to detect (0 is unlimited)
            ]
            reactor_args.append(args)
        payload["input"]["alwayson_scripts"] = {"reactor": {"args": args}}

    return payload

def poll_job_status(status_id, headers):
    global polling_active
    while polling_active:
        try:
            response_image = requests.get(f"{RUNPOD_STATUS_URL}{status_id}", headers=headers)
            if response_image.status_code == 200:
                job_status = response_image.json()
                print(job_status)
                update_job_status(job_status["status"])
                
                if job_status["status"] in ['COMPLETED', 'FAILED']:
                    polling_active = False

                update_job_status_in_firestore(status_id, job_status["status"])
            else:
                print(f"Failed to fetch job status: {response_image.status_code}")
        except Exception as e:
            print(f"Error polling job status: {e}")
        time.sleep(5) 

    return response_image

def fetch_images_from_response(response_image):
    generated_images = []
    if "output" in response_image.json() and "images" in response_image.json()["output"]:
        image_base64_list = response_image.json()["output"]["images"]
        for image_base64 in image_base64_list:
            try:
                if not image_base64.startswith("data:image/png;base64,"):
                    image_base64 = "data:image/png;base64," + image_base64
                image_data = base64.b64decode(image_base64.split(",")[1])
                image = Image.open(BytesIO(image_data))
                generated_images.append(image)
            except Exception as e:
                print("Error decoding image:", e)
    return generated_images

def output_window(prompt, negative_prompt, slider_value, pose_images, face_swap_images):
    global polling_active
    polling_active = True

    pose_image_base64 = process_images(pose_images) if pose_images else None
    face_swap_image_base64 = process_images(face_swap_images) if face_swap_images else None

    payload = prepare_payload(prompt, negative_prompt, slider_value, pose_image_base64, face_swap_image_base64)

    headers = {
        "Authorization": f"Bearer {RUNPOD_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(RUNPOD_RUN_URL, json=payload, headers=headers)
        if response.status_code == 200:
            status_id = response.json().get("id")
            response_image = poll_job_status(status_id, headers)

            if response_image and response_image.status_code == 200:
                generated_images = fetch_images_from_response(response_image)
                return generated_images, f"Generated Payload: {payload}"

        else:
            print(f"API request failed: {response.text}")
    except Exception as e:
        print(f"Error during API call: {e}")

    return [], "No images generated."

def create_gradio_interface():
    with gr.Blocks() as interface:
        with gr.Row():
            with gr.Column():
                prompt = gr.Textbox(lines=1, placeholder="Prompt Text Here...", label="Prompt")
                negative_prompt = gr.Textbox(lines=1, placeholder="Negative Prompt Text Here...", label="Negative Prompt")
                slider_value = gr.Slider(1, 10, value=1, step=1, label="Number of Generations")
                pose_images = gr.Files(file_count="multiple", type="binary", label="Pose Images (Optional)")
                face_swap_images = gr.Files(file_count="multiple", type="binary", label="Face Swap Images (Optional)")
                
                process_button = gr.Button("Generate Images")
                update_button = gr.Button("Update Status")
                save_button = gr.Button("Save Images to GCS")
            
            with gr.Column():
                generated_images = gr.Gallery(label="Generated Images")
                debug_info = gr.Textbox(label="Debug Info")
                job_status_textbox = gr.Textbox(label="Job Status", placeholder="Waiting for job status updates...", interactive=False)

        process_button.click(output_window, 
                             inputs=[prompt, negative_prompt, slider_value, pose_images, face_swap_images], 
                             outputs=[generated_images, debug_info])
        
        update_button.click(fn=get_job_status, inputs=[], outputs=job_status_textbox)

        save_button.click(save_images_to_gcs, inputs=[generated_images], outputs=[gr.Textbox(label="Public URLs")])

    return interface
