from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from langchain.document_loaders import WebBaseLoader, SitemapLoader
from langchain.vectorstores import FAISS
import requests
import json
from tenacity import retry, stop_after_attempt, wait_exponential

GEMINI_API_URL = "https://gemini.api.endpoint"
API_KEY = "AIzaSyBChI0wzUmPRFUnCeU0b-JJI8P-Bxax2rY"

app = Flask(__name__)
api = Api(app)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_gemini_api(user_message):
    try:
        data = {
            "prompt": user_message,
            "max_tokens": 100
        }

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(GEMINI_API_URL, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Error during Gemini API call: {e}")
        raise

def create_vectorstore():
    loader = WebBaseLoader("https://brainlox.com/courses/category/technical")
    documents = loader.load()

    db = FAISS.from_documents(documents, embeddings=None)
    db.save_local("faiss_index")
    print("Vectorstore created and saved.")

try:
    db = FAISS.load_local("faiss_index", embeddings=None)
    print("Vectorstore loaded from disk.")
except:
    create_vectorstore()
    db = FAISS.load_local("faiss_index", embeddings=None)

class ChatbotResource(Resource):
    def post(self):
        try:
            user_message = request.json.get("message")
            if not user_message:
                return jsonify({"error": "Message is required"}), 400

            response = call_gemini_api(user_message)

            return jsonify({"response": response}), 200

        except Exception as e:
            print(f"An error occurred: {e}")
            return jsonify({"error": "An error occurred"}), 500

api.add_resource(ChatbotResource, "/api/chat")

if __name__ == "__main__":
    app.run(debug=True)
