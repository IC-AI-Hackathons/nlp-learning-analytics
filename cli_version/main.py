import datetime
import os
import re
import subprocess
import sys
from pathlib import Path
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    api_version="2024-12-01-preview",
    api_key=os.getenv("OPENAI_API_KEY"),
    azure_endpoint="https://esehackai2507.openai.azure.com/",
)

SWAGGER_PATH = "swagger.json"
GENERATED_DIR = Path("__generated")
GENERATED_DIR.mkdir(exist_ok=True)


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")


def generate_filename(query):
    base = slugify(query[:50]) or "plot"
    return GENERATED_DIR / f"{base}_{timestamp()}.py"


def load_api_spec(path):
    with open(path, "r") as f:
        return f.read()


def build_prompt(query: str, swagger: str) -> str:
    return f"""
You are a developer assistant.

You are given:
- A natural language user query asking to generate a Python script that uses an internal API and produces a graph.
- The Swagger JSON for the internal API.

You must respond by writing a complete Python program that:
- Fetches the required data using the API
- Extracts and processes the data
- Uses matplotlib or pandas to create a plot
- Follows the style and clarity of the code in the examples below
- Assumes authentication is via `HTTPBasicAuth`, with credentials and API base URL loaded from a `.env` file. The variables are called API_BASE_URL, API_USERNAME and API_PASSWORD. 

Extra information:
- Provide the output in pure text, without any MD formatting markers.
- We are typically interested in the 'staff' view of the data

The Swagger JSON:
{swagger}


The user query:
"{query}"

Respond with only the Python program.
"""


def ask_openai(query: str):
    swagger_text = load_api_spec(SWAGGER_PATH)
    prompt = build_prompt(query, swagger_text)

    print("Sending request to OpenAI...")
    response = client.chat.completions.create(
        model="o4-mini",
        messages=[
            {"role": "system", "content": "You are a helpful developer assistant."},
            {"role": "user", "content": prompt},
        ],
    )

    code = response.choices[0].message.content
    return code


def main():
    print("📝 Enter your query:")
    query = input("> ").strip()

    code = ask_openai(query)
    file_path = generate_filename(query)

    # Save file
    with open(file_path, "w") as f:
        f.write(code)

    print(f"\n✅ Python script saved to: {file_path}")

    # Run the generated file
    print(f"\n🚀 Running the generated script...\n")
    subprocess.run([sys.executable, str(file_path)], check=True)


if __name__ == "__main__":
    main()
