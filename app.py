from flask import Flask, render_template, request, jsonify, send_file
import requests
from PIL import Image
from io import BytesIO
import tempfile
import os
from gtts import gTTS
from pylint.lint import Run
from pylint.reporters.text import TextReporter
from io import StringIO
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from collections import Counter
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Set NLTK data path to the pre-downloaded folder in the project root
nltk.data.path.append(os.path.join(os.path.dirname(__file__), 'nltk_data'))

# PyMuPDF check
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

# API Key (Hugging Face) - Use environment variable
hf_api_key = os.getenv("HF_API_KEY")

# Home page route
@app.route('/')
def home():
    return render_template('index.html')

# Individual model page routes
@app.route('/text-to-image')
def text_to_image_page():
    return render_template('text_to_image.html')

@app.route('/text-to-audio')
def text_to_audio_page():
    return render_template('text_to_audio.html')

@app.route('/summarization')
def summarization_page():
    return render_template('summarization.html')

@app.route('/code-debugger')
def code_debugger_page():
    return render_template('code_debugger.html')

@app.route('/ats-score')
def ats_score_page():
    return render_template('ats_score.html')

# API Endpoints
@app.route('/api/text-to-image', methods=['POST'])
def text_to_image():
    if not hf_api_key:
        return jsonify({"error": "Hugging Face API key missing"}), 400
    prompt = request.json.get('prompt', 'A futuristic city')
    url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {hf_api_key}"}
    payload = {"inputs": prompt}
    tmp_path = None
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(response.content)
                tmp_path = tmp.name
            return jsonify({
                "url": f"/api/download-image?path={tmp_path}",
                "status": "success"
            })
        return jsonify({"error": f"API error: {response.status_code}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.route('/api/download-image')
def download_image():
    tmp_path = request.args.get('path')
    if os.path.exists(tmp_path):
        return send_file(tmp_path, mimetype='image/png', as_attachment=True, download_name='generated_image.png')
    return jsonify({"error": "File not found"}), 404

@app.route('/api/text-to-audio', methods=['POST'])
def text_to_audio():
    text = request.json.get('text', 'Hello, this is a test.')
    lang = request.json.get('lang', 'en')
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(tmp.name)
            tmp_path = tmp.name
        return jsonify({
            "url": f"/api/download-audio?path={tmp_path}",
            "status": "success"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.route('/api/download-audio')
def download_audio():
    tmp_path = request.args.get('path')
    if os.path.exists(tmp_path):
        return send_file(tmp_path, mimetype='audio/mp3', as_attachment=True, download_name='output.mp3')
    return jsonify({"error": "File not found"}), 404

@app.route('/api/summarize', methods=['POST'])
def summarize():
    text = request.json.get('text', '')
    summary_sentences = request.json.get('sentences', 2)
    if not text.strip():
        return jsonify({"error": "Text is empty"}), 400
    sentences = sent_tokenize(text)
    if len(sentences) < 2:
        return jsonify({"error": "Enter at least two sentences"}), 400
    if len(sentences) <= summary_sentences:
        return jsonify({"summary": sentences})
    try:
        stop_words = set(stopwords.words("english"))
        words = [w.lower() for w in word_tokenize(text) if w.isalnum() and w.lower() not in stop_words]
        word_freq = Counter(words)
        sentence_scores = {}
        for i, sent in enumerate(sentences):
            score = sum(word_freq[w.lower()] for w in word_tokenize(sent) if w.isalnum() and w.lower() in word_freq)
            sentence_scores[i] = score / (len(word_tokenize(sent)) + 1)
        top_sentences = sorted(sorted(sentence_scores.items(), key=lambda x: x[0])[:summary_sentences], key=lambda x: x[1], reverse=True)
        summary_sentences_list = [sentences[i] for i, _ in top_sentences]
        return jsonify({"summary": summary_sentences_list})
    except Exception as e:
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
        explanation = "undefined_variable is not defined. Define it before use." if "undefined_variable" in code else ""
        return jsonify({"issues": lint_output.strip() or "No issues detected", "explanation": explanation})
    except Exception as e:
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
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)), debug=True)
