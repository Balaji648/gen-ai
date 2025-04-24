from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import requests
from PIL import Image
from io import BytesIO, StringIO
import tempfile
import os
import logging
from gtts import gTTS
from pylint.lint import Run
from pylint.reporters.text import TextReporter
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from collections import Counter

# PyMuPDF
try:
    import fitz
except ImportError:
    fitz = None

app = Flask(__name__)
CORS(app)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure NLTK resources
nltk.download('punkt')
nltk.download('stopwords')

# Hugging Face API key (set your key here or from env)
hf_api_key = os.getenv("HF_API_KEY", "your_huggingface_token_here")

@app.route('/')
def home():
    return jsonify({"message": "AI Tools API is running"})

# ------------------ TEXT TO IMAGE ------------------ #
@app.route('/api/text-to-image', methods=['POST'])
def text_to_image():
    if not hf_api_key:
        return jsonify({"error": "Missing Hugging Face API key"}), 400

    prompt = request.json.get('prompt', 'A futuristic city')
    url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {hf_api_key}"}
    payload = {"inputs": prompt}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
            tmp.write(response.content)
            path = tmp.name

        return jsonify({
            "url": f"/api/preview-image?path={path}",
            "status": "success"
        })
    except Exception as e:
        logger.error(f"Text-to-Image error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/preview-image')
def preview_image():
    path = request.args.get('path')
    if os.path.exists(path):
        return send_file(path, mimetype='image/png')
    return jsonify({"error": "Image not found"}), 404

# ------------------ TEXT TO AUDIO ------------------ #
@app.route('/api/text-to-audio', methods=['POST'])
def text_to_audio():
    text = request.json.get('text', 'Hello world!')
    lang = request.json.get('lang', 'en')
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
            tts = gTTS(text=text, lang=lang)
            tts.save(tmp.name)
            path = tmp.name
        return jsonify({
            "url": f"/api/preview-audio?path={path}",
            "status": "success"
        })
    except Exception as e:
        logger.error(f"Text-to-Audio error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/preview-audio')
def preview_audio():
    path = request.args.get('path')
    if os.path.exists(path):
        return send_file(path, mimetype='audio/mp3')
    return jsonify({"error": "Audio not found"}), 404

# ------------------ SUMMARIZATION ------------------ #
@app.route('/api/summarize', methods=['POST'])
def summarize():
    text = request.json.get('text', '')
    summary_sentences = request.json.get('sentences', 2)

    if not text.strip():
        return jsonify({"error": "Text is empty"}), 400

    try:
        sentences = sent_tokenize(text)
        if len(sentences) <= summary_sentences:
            return jsonify({"summary": sentences})

        stop_words = set(stopwords.words("english"))
        words = [w.lower() for w in word_tokenize(text) if w.isalnum() and w.lower() not in stop_words]
        word_freq = Counter(words)

        sentence_scores = {
            i: sum(word_freq[w.lower()] for w in word_tokenize(sent) if w.lower() in word_freq)
            for i, sent in enumerate(sentences)
        }

        top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:summary_sentences]
        summary = [sentences[i] for i, _ in sorted(top_sentences)]
        return jsonify({"summary": summary})
    except Exception as e:
        logger.error(f"Summarization error: {e}")
        return jsonify({"error": str(e)}), 500

# ------------------ CODE DEBUGGER ------------------ #
@app.route('/api/debug', methods=['POST'])
def debug_code():
    code = request.json.get('code', '')
    try:
        with tempfile.NamedTemporaryFile(mode='w+', suffix=".py", delete=False) as tmp:
            tmp.write(code)
            path = tmp.name

        output = StringIO()
        reporter = TextReporter(output)
        Run([path, '--reports=n'], reporter=reporter, exit=False)
        result = output.getvalue()
        os.unlink(path)

        return jsonify({"issues": result or "No issues detected"})
    except Exception as e:
        logger.error(f"Code Debugger error: {e}")
        return jsonify({"error": str(e)}), 500

# ------------------ ATS SCORING ------------------ #
@app.route('/api/ats-score', methods=['POST'])
def ats_score():
    if not fitz:
        return jsonify({"error": "PyMuPDF not installed"}), 500
    if 'resume' not in request.files or not request.form.get('job_desc'):
        return jsonify({"error": "Missing resume or job description"}), 400

    try:
        resume = request.files['resume']
        job_desc = request.form['job_desc']

        pdf = fitz.open(stream=resume.read(), filetype='pdf')
        resume_text = ''.join([page.get_text() for page in pdf])
        resume_words = set(resume_text.lower().split())
        job_words = set(job_desc.lower().split())
        common = resume_words.intersection(job_words)
        score = min((len(common) / len(job_words)) * 100, 100)

        return jsonify({
            "score": f"{score:.2f}%",
            "matches": list(common)
        })
    except Exception as e:
        logger.error(f"ATS Score error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
