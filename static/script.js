// Function to open specific tab
function openTab(tabName) {
    const tabs = document.getElementsByClassName('tab-content');
    for (let i = 0; i < tabs.length; i++) {
        tabs[i].style.display = i === 0 ? 'block' : 'none'; // Default to first tab
    }
    document.getElementById(tabName).style.display = 'block';
    const buttons = document.getElementsByClassName('tab-button');
    for (let button of buttons) {
        button.style.backgroundColor = '';
    }
    event.target.style.backgroundColor = '#ddd';
}

// Initialize first tab on load
window.onload = function() {
    openTab('text-to-image');
};

// API request function
async function fetchApi(endpoint, data, method = 'POST', file = null) {
    const url = `/${endpoint}`;
    const options = {
        method: method,
        headers: {
            'Content-Type': file ? 'multipart/form-data' : 'application/json',
        },
    };

    if (file) {
        const formData = new FormData();
        formData.append('resume', file);
        formData.append('job_desc', data.job_desc);
        options.body = formData;
    } else {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'API request failed');
        return result;
    } catch (error) {
        return { error: error.message };
    }
}

// Text-to-Image
function generateImage() {
    const prompt = document.getElementById('image-prompt').value;
    fetchApi('api/text-to-image', { prompt })
        .then(result => {
            const resultDiv = document.getElementById('image-result');
            if (result.error) {
                resultDiv.innerHTML = `<p>Error: ${result.error}</p>`;
            } else if (result.url) {
                const link = document.createElement('a');
                link.href = result.url;
                link.download = 'generated_image.png';
                link.innerHTML = 'Download Image';
                resultDiv.innerHTML = '';
                resultDiv.appendChild(link);
            }
        });
}

// Text-to-Audio
function generateAudio() {
    const text = document.getElementById('audio-text').value;
    const lang = document.getElementById('audio-lang').value;
    fetchApi('api/text-to-audio', { text, lang })
        .then(result => {
            const resultDiv = document.getElementById('audio-result');
            if (result.error) {
                resultDiv.innerHTML = `<p>Error: ${result.error}</p>`;
            } else if (result.url) {
                const link = document.createElement('a');
                link.href = result.url;
                link.download = 'output.mp3';
                link.innerHTML = 'Download Audio';
                resultDiv.innerHTML = '';
                resultDiv.appendChild(link);
            }
        });
}

// Summarization
function summarizeText() {
    const text = document.getElementById('summary-text').value;
    const sentences = document.getElementById('summary-sentences').value;
    fetchApi('api/summarize', { text, sentences })
        .then(result => {
            const resultDiv = document.getElementById('summary-result');
            if (result.error) {
                resultDiv.innerHTML = `<p>Error: ${result.error}</p>`;
            } else {
                resultDiv.innerHTML = `<p>Summary: ${result.summary.join(' ')}</p>`;
            }
        });
}

// Code Debugger
function debugCode() {
    const code = document.getElementById('code-input').value;
    fetchApi('api/debug', { code })
        .then(result => {
            const resultDiv = document.getElementById('code-result');
            if (result.error) {
                resultDiv.innerHTML = `<p>Error: ${result.error}</p>`;
            } else {
                resultDiv.innerHTML = `<p>Issues: ${result.issues}</p><p>Explanation: ${result.explanation}</p>`;
            }
        });
}

// ATS Score Checker
function checkAtsScore() {
    const resumeInput = document.getElementById('resume-upload');
    const jobDesc = document.getElementById('job-desc').value;
    const file = resumeInput.files[0];
    if (!file || !jobDesc) {
        document.getElementById('ats-result').innerHTML = '<p>Please upload a resume and enter a job description.</p>';
        return;
    }
    fetchApi('api/ats-score', { job_desc: jobDesc }, 'POST', file)
        .then(result => {
            const resultDiv = document.getElementById('ats-result');
            if (result.error) {
                resultDiv.innerHTML = `<p>Error: ${result.error}</p>`;
            } else {
                resultDiv.innerHTML = `<p>ATS Score: ${result.score}</p><p>Matching Keywords: ${result.matches.join(', ')}</p>`;
            }
        });
}
