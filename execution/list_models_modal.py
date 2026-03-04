import modal
import os

app = modal.App("list-models")
image = modal.Image.debian_slim().pip_install("google-genai")

@app.function(image=image, secrets=[modal.Secret.from_name("bot-secrets")])
def list_m():
    from google import genai
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    models = list(client.models.list())
    for m in models:
        print(m.name)

@app.local_entrypoint()
def run():
    list_m.remote()
