from flask import Flask, request, render_template, redirect, url_for, session
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, VideoUnavailable
import os
from openai import OpenAI

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed for session management

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
        return "error: Transcripts are disabled for this video."
    except VideoUnavailable:
        return "error: The video is unavailable."
    except Exception as e:
        return f"error: {str(e)}"

# Function to summarize text using KlusterAI
def summarize_text_with_kluster(text, request_type):
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
        return f"error: {str(e)}"

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
        return render_template("index.html", error="No URL provided.")

    # Extract video ID from URL
    try:
        video_id = url.split("v=")[-1].split("&")[0]
    except IndexError:
        return render_template("index.html", error="Invalid YouTube URL.")

    # Fetch transcript
    transcript = fetch_transcript(video_id)
    if transcript.startswith("error:"):
        return render_template("index.html", error=transcript.replace("error: ", ""))

    # Map action to request types for summarization
    summarization_types = {
        "bullet_points": "5 bullet points",
        "summary": "summary of the text",
        "key_words": "key words",
        "questions": "questions that can be asked",
        "learnings": "things that can be learned"
    }
    request_type = summarization_types.get(action, "5 bullet points")

    # Summarize transcript using KlusterAI
    summary = summarize_text_with_kluster(transcript, request_type)
    
    if summary.startswith("error:"):
        return render_template("index.html", error=summary.replace("error: ", ""))

    # Format summary based on action
    summary_title = action.replace("_", " ").title()
    
    # Format bullet points properly if the response contains them
    if action == "bullet_points":
        summary = "\n".join([f"• {point.strip()}" for point in summary.split("\n")])

    # Store summary in session and redirect to /result
    session['summary'] = summary
    session['summary_title'] = summary_title
    return redirect(url_for('result'))

# Route to display summary on a new page
@app.route('/result')
def result():
    summary = session.get('summary', None)
    summary_title = session.get('summary_title', None)

    if not summary:
        return redirect(url_for('home'))  # Redirect back if no summary is found

    return render_template("result.html", summary=summary, summary_title=summary_title)

if __name__ == "__main__":
    app.run(debug=True)
