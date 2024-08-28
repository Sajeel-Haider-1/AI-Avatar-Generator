# AI-Avatar-Generator

AI avatar generator take prompts and pictures to generate avatar. Control the pose and number of generation of the avatar and also do face swaps for any image

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
  - [Running the Application](#running-the-application)
- [Configuration](#configuration)
- [Contact](#contact)

## Introduction

Welcome to the **AI Avatar Generator**! This project is designed to generate desired avatars from the prompts.

## Features

- **Prompts**: Write prompts explaining what kind of avatar you want.
- **Negative Prompts**: Add negative prompts that you dont want to see in your avatars.
- **Number of Generations**: Select the number of generations you want to be generated.
- **Pose Images**: Drop images to control the pose of the generated ones.
- **Face Swaps**: Drop images to swap the face from source to target images.
- **Save to GCS**: On one button click save the generated images to the google cloud storage (Buckets).

## Technologies Used

- **Frontend**: FastApi, Gradio
- **Backend**: WebUI txt2img Api with extensions ControlNet, Reactor
- **Storage**: Cloud Storage Buckets
- **Firestore**: Status updates
- **Deployment Frontend**: Docker, Google Cloud Run
- **Deployment Backend**: Docker, Runpod (Serverless Endpoint)

## Getting Started

### Prerequisites

- Python (v3 or later)
- Docker
- Google Cloud account

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Sajeel-Haider-1/AI-Avatar-Generator.git
   cd Image-Based_Search_Engine
   ```
2. **Setup Pulumi**:
   ```bash
    cd pulumi-infrastructure
    npm install
   ```
3. **Setup Frontend**:
   ```bash
   cd /AI-Avatar-Generator
   python -m venv venv
   venv/Scripts/activate
   pip install -r requirements.txt
   ```

### Usage

## Running the Application

# Backend

Deploy your webui docker image to Runpod

# Frontend

For running Pulumi

```bash
   pulumi up
```

For running Gradio

```bash
   uvicorn main:app --host 0.0.0.0 --port 8080
```

### Configuration

## FastApi (AI-Avatar-Generator/.env):

FLASK_SECRET_KEY=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
ALLOWED_USERS=
SDAPI_URL=
REDIRECT_URI=
BUCKET_NAME=
RUNPOD_API_KEY=
RUNPOD_RUN_URL=
RUNPOD_STATUS_URL=

## Pulumi (pulumi-infrastructure/.env):

PROJECT_ID=
LOCATION=
SERVICE_ACCOUNT=
ARTIFACT_REPO_NAME=
IMAGE_NAME=

### Contact

# For any inquiries, please contact sajeel@jetrr.com.
