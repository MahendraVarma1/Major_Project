from flask import Flask, request, render_template
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, VideoUnavailable
import os
from openai import OpenAI

app = Flask(__name__)

# Directory for saving downloaded PDFs
PDF_DIR = "static/pdfs"
if not os.path.exists(PDF_DIR):
    os.makedirs(PDF_DIR)

# KlusterAI API configuration
KLUSTER_API_KEY = "2e734f4d-bbea-4905-8de2-6f56e47f362e"
BASE_URL = "https://api.kluster.ai/v1"

client = OpenAI(api_key=KLUSTER_API_KEY, base_url=BASE_URL)

# Function to fetch transcript
def fetch_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join([entry['text'] for entry in transcript])
        return text
    except TranscriptsDisabled:
        return "Transcripts are disabled for this video."
    except VideoUnavailable:
        return "The video is unavailable."
    except Exception as e:
        return str(e)

# Function to summarize text using KlusterAI
def summarize_text_with_kluster(text, request_type="5 bullet points"):
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"Please summarize the following text into {request_type}:\n{text}"}
    ]

    try:
        response = client.chat.completions.create(
            model="klusterai/Meta-Llama-3.1-8B-Instruct-Turbo",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# Route for home page
@app.route('/')
def home():
    return render_template("index.html")

# Route to handle transcript and summarization
@app.route('/summarize', methods=['POST'])
def summarize():
    url = request.form.get("url")
    action = request.form.get("action")  # Get action type from form submission

    if not url:
        return "Error: No URL provided.", 400

    # Extract video ID from URL
    try:
        video_id = url.split("v=")[-1].split("&")[0]
    except IndexError:
        return "Error: Invalid YouTube URL.", 400

    # Fetch transcript
    transcript = fetch_transcript(video_id)
    if "error" in transcript:
        return f"Error: {transcript}", 400

    # Map action to request types for summarization
    summarization_types = {
        "bullet_points": "5 bullet points",
        "summary": "summary of the text",
        "key_words": "key words",
        "questions": "questions that can be asked",
        "learnings": "things that can be learned"
    }
    request_type = summarization_types.get(action, "5 bullet points")  # Default to bullet points

    # Summarize transcript using KlusterAI
    summary = summarize_text_with_kluster(transcript, request_type)

    return f"<h1>Summary ({action.replace('_', ' ').title()}):</h1><p>{summary}</p>"

if __name__ == "__main__":
    app.run(debug=True)
