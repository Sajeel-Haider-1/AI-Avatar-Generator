import os
import io
import random
from google.cloud import storage
from PIL import Image
from auth import get_user_email

def upload_to_gcs(bucket_name, blob_name, image):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    if isinstance(image, tuple):
        image_path = image[0]
        image = Image.open(image_path)

    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    blob.upload_from_string(img_byte_arr, content_type='image/png')
    blob.make_public()

    return blob.public_url

def save_images_to_gcs(images):
    print(images)
    user_email = get_user_email()
    bucket_name = os.getenv("BUCKET_NAME")
    public_urls = []
    
    for image in images:
        unique_id = random.randint(100000, 999999)
        blob_name = f"{user_email}/generated_image_{unique_id}.png"
        public_url = upload_to_gcs(bucket_name, blob_name, image)
        public_urls.append(public_url)

    return public_urls
