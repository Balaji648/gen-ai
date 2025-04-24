from flask import Flask, render_template, request, jsonify, send_file
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
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

nltk.data.path.append(os.path.join(os.path.dirname(__file__), 'nltk_data'))
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    logger.info("NLTK data loaded successfully")
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

try:
    import fitz  # PyMuPDF
    logger.info("PyMuPDF loaded successfully")
except ImportError:
    fitz = None
    logger.warning("PyMuPDF not installed - ATS Score will not work")

hf_api_key = os.getenv("HF_API_KEY")
if not hf_api_key:
    logger.warning("HF_API_KEY not set - Text-to-Image will fail")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/text-to-image', methods=['POST'])
def text_to_image():
    if not hf_api_key:
        return jsonify({"error": "Hugging Face API key missing"}), 400

    prompt = request.json.get('prompt', 'A futuristic city')
    url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {hf_api_key}"}
    payload = {"inputs": prompt}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        img_data = response.content
        img_base64 = base64.b64encode(img_data).decode('utf-8')
        return jsonify({"status": "success", "image_base64": img_base64})
    except Exception as e:
        logger.error(f"Text-to-Image error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/text-to-audio', methods=['POST'])
def text_to_audio():
    text = request.json.get('text', 'Hello, this is a test.')
    lang = request.json.get('lang', 'en')
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tts = gTTS(text=text, lang=lang)
            tts.save(tmp.name)
            with open(tmp.name, 'rb') as f:
                audio_base64 = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(tmp.name)
        return jsonify({"status": "success", "audio_base64": audio_base64})
    except Exception as e:
        logger.error(f"Text-to-Audio error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/summarize', methods=['POST'])
def summarize():
    text = request.json.get('text', '')
    summary_sentences = request.json.get('sentences', 2)
    if not text.strip():
        return jsonify({"error": "Text is empty"}), 400
    try:
        sentences = sent_tokenize(text)
        if len(sentences) < 2:
            return jsonify({"error": "Enter at least two sentences"}), 400
        if len(sentences) <= summary_sentences:
            return jsonify({"summary": sentences})
        stop_words = set(stopwords.words("english"))
        words = [w.lower() for w in word_tokenize(text) if w.isalnum() and w.lower() not in stop_words]
        word_freq = Counter(words)
        sentence_scores = {}
        for i, sent in enumerate(sentences):
            score = sum(word_freq[w.lower()] for w in word_tokenize(sent) if w.isalnum() and w.lower() in word_freq)
            sentence_scores[i] = score / (len(word_tokenize(sent)) + 1)
        top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:summary_sentences]
        summary_sentences_list = [sentences[i] for i, _ in sorted(top_sentences)]
        return jsonify({"summary": summary_sentences_list})
    except Exception as e:
        logger.error(f"Summarization error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/debug', methods=['POST'])
def debug_code():
    code = request.json.get('code', '')
    try:
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as tmp:
            tmp.write(code)
            tmp_path = tmp.name
        output = StringIO()
        reporter = TextReporter(output)
        Run([tmp_path, "--reports=n"], reporter=reporter, exit=False)
        lint_output = output.getvalue()
        output.close()
        os.unlink(tmp_path)
        return jsonify({"issues": lint_output.strip() or "No issues detected"})
    except Exception as e:
        logger.error(f"Code Debugger error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ats-score', methods=['POST'])
def ats_score():
    if not fitz:
        return jsonify({"error": "PyMuPDF not installed"}), 400
    if 'resume' not in request.files or not request.form.get('job_desc'):
        return jsonify({"error": "Missing resume or job description"}), 400

    resume = request.files['resume']
    job_desc = request.form['job_desc']
    try:
        pdf = fitz.open(stream=resume.read(), filetype="pdf")
        resume_text = "".join(page.get_text() for page in pdf)
        resume_words = set(resume_text.lower().split())
        job_words = set(job_desc.lower().split())
        common = resume_words.intersection(job_words)
        score = min(len(common) / len(job_words) * 100, 100)
        return jsonify({"score": f"{score:.2f}%", "matches": list(common)})
    except Exception as e:
        logger.error(f"ATS Score error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)), debug=True)
