import os
import time
import requests
from firestore_utils import update_job_status_in_firestore

RUNPOD_STATUS_URL = os.getenv("RUNPOD_STATUS_URL")

polling_active = True
job_status = ''

def update_job_status(status):
    global job_status
    print("update_job_status: ",status)
    job_status = status 

def get_job_status():
    global job_status
    return job_status

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
