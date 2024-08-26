from google.cloud import firestore
from auth import get_user_email

db = firestore.Client(project="jetrr-sajeel-haider-1")

def update_job_status_in_firestore(job_id, status):
    try:
        user_email = get_user_email()
        job_ref = db.collection(user_email).document(job_id)
        doc = job_ref.get()
        if doc.exists:
            job_ref.update({
                'status': status,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            print(f"Job {job_id} updated successfully.")
        else:
            print(f"Job {job_id} created")
            job_ref.set({
                'user_email': user_email,
                'job_id': job_id,
                'status': status,
                'created_at': firestore.SERVER_TIMESTAMP
            })
    except Exception as e:
        print(f"Error updating job status: {e}")

def get_user_jobs(user_email):
    jobs_ref = db.collection('jobs').where('user_email', '==', user_email)
    jobs = jobs_ref.stream()
    return [job.to_dict() for job in jobs]

