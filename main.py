
from fastapi import FastAPI
import gradio as gr
import os 

app = FastAPI()

# Define your Gradio interface
def greet(name):
    return f"Hello {name}!"

gr_interface = gr.Interface(fn=greet, inputs="text", outputs="text")

# Mount Gradio app at a specific path
gr.mount_gradio_app(app, gr_interface, path="/gradio")

# Define a FastAPI route
@app.get("/")
def read_main():
    return {"message": "Welcome to the FastAPI app!"}

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
