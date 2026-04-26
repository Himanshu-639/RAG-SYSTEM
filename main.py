import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import ollama
from sklearn.metrics.pairwise import cosine_similarity
import requests
import json

load_dotenv()

dataset = []

with open("cat-facts.txt", "r", encoding="utf-8") as file:
    dataset = file.readlines()
    print(f"Loaded cat-facts.txt with {len(dataset)}")

EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'

VECTOR_DB = []

def add_chunk_to_database(chunk):
    embedding = ollama.embed(model = EMBEDDING_MODEL, input= chunk)['embeddings'][0]
    VECTOR_DB.append((chunk, embedding))

for i, chunk in enumerate(dataset):
    add_chunk_to_database(chunk)
    print(f"Added chunk {i+1}/{len(dataset)} to database.")

def retrieve(query, top_n=3):
    query_embedding = ollama.embed(EMBEDDING_MODEL, input= query)['embeddings'][0]
    similarities = []
    for chunk, embedding in VECTOR_DB:
        similarity = cosine_similarity([query_embedding], [embedding])[0][0]
        similarities.append((chunk, similarity))
    similarities.sort(key=lambda x:x[1], reverse=True)
    return similarities[:top_n]

input_query = input("Ask me anything : ")
retrieved_knowledge = retrieve(input_query)

print('Retrieved Knowledge : ')
for chunk, similarity in retrieved_knowledge:
    print(f" - (similarity : {similarity:.2f}) {chunk}")

'''

def generate():
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemma-4-26b-a4b-it"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=input_query),
            ],
        ),
    ]
    tools = [
        types.Tool(googleSearch=types.GoogleSearch(
        )),
    ]
    generate_content_config = types.GenerateContentConfig(
        tools=tools,
        system_instruction=[
            types.Part.from_text(text=f"""You are a helpful chatbot.
Use only the following pieces of context to answer the question. Don't make up any new information:
{'\\n'.join([f' - {chunk}' for chunk, similarity in retrieved_knowledge])}"""),
        ],
    )

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if text := chunk.text:
            print(text, end="")

print("your Answer")

'''

def generate():
    url = "http://localhost:11434/api/generate"

    payload = {
        "model": "gemma4:e2b",
        "prompt": input_query,
    }

    try:
        response = requests.post(url, json = payload, stream=True)

        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    generated_text = data.get("response", "No response")
                    print(generated_text)
            print()
        else:
            print(f"Status Code : {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("Connection Error ")
    except Exception as e:
        print(f" Error {e}")

generate()