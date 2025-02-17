from flask import Flask, request, render_template
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, VideoUnavailable
import os
import requests

app = Flask(__name__)

# Directory for saving downloaded PDFs
PDF_DIR = "static/pdfs"
if not os.path.exists(PDF_DIR):
    os.makedirs(PDF_DIR)

# DeepSeek API configuration
DEEPSEEK_API_KEY = "sk-0356ccfc16224023b3817f1e9b461f75"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"  

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

# Function to summarize text using DeepSeek API
def summarize_text_with_deepseek(text, request_type="5 bullet points"):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Please summarize the following text into {request_type}:\n{text}"}
        ],
        "stream": False
    }
    response = requests.post(DEEPSEEK_API_URL, json=data, headers=headers)
    if response.status_code == 200:
        response_data = response.json()
        return response_data['choices'][0]['message']['content']
    else:
        return f"Error: {response.status_code} - {response.text}"

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

    # Summarize transcript using DeepSeek API
    summary = summarize_text_with_deepseek(transcript, request_type)

    return f"<h1>Summary ({action.replace('_', ' ').title()}):</h1><p>{summary}</p>"

if __name__ == "__main__":
    app.run(debug=True) 
