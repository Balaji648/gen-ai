// Toggle burger menu
function toggleMenu() {
    const navLinks = document.querySelector('.nav-links');
    navLinks.classList.toggle('active');
}

// Toggle dark mode
function toggleTheme() {
    document.body.classList.toggle('dark-mode');
    const themeButton = document.querySelector('.theme-toggle button');
    if (document.body.classList.contains('dark-mode')) {
        themeButton.innerHTML = '<i class="fas fa-sun"></i> Light Mode';
    } else {
        themeButton.innerHTML = '<i class="fas fa-moon"></i> Dark Mode';
    }
}

// Show loading spinner
function showSpinner(tab) {
    const spinner = document.querySelector(`#${tab}-result .spinner`);
    spinner.style.display = 'block';
}

// Hide loading spinner
function hideSpinner(tab) {
    const spinner = document.querySelector(`#${tab}-result .spinner`);
    spinner.style.display = 'none';
}

// Clear tab inputs and results
function clearTab(tab) {
    if (tab === 'image') {
        document.getElementById('image-prompt').value = '';
        document.getElementById('image-result').innerHTML = '<div class="spinner" style="display: none;"></div>';
    } else if (tab === 'audio') {
        document.getElementById('audio-text').value = '';
        document.getElementById('audio-lang').value = 'en';
        document.getElementById('audio-result').innerHTML = '<div class="spinner" style="display: none;"></div>';
    } else if (tab === 'summary') {
        document.getElementById('summary-text').value = '';
        document.getElementById('summary-sentences').value = '2';
        document.getElementById('summary-result').innerHTML = '<div class="spinner" style="display: none;"></div>';
    } else if (tab === 'code') {
        document.getElementById('code-input').value = '';
        document.getElementById('code-result').innerHTML = '<div class="spinner" style="display: none;"></div>';
    } else if (tab === 'ats') {
        document.getElementById('resume-upload').value = '';
        document.getElementById('job-desc').value = '';
        document.getElementById('ats-result').innerHTML = '<div class="spinner" style="display: none;"></div>';
    }
}

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
    showSpinner('image');
    fetchApi('api/text-to-image', { prompt })
        .then(result => {
            hideSpinner('image');
            const resultDiv = document.getElementById('image-result');
            if (result.error) {
                resultDiv.innerHTML = `<p class="error">Error: ${result.error}</p>`;
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
    showSpinner('audio');
    fetchApi('api/text-to-audio', { text, lang })
        .then(result => {
            hideSpinner('audio');
            const resultDiv = document.getElementById('audio-result');
            if (result.error) {
                resultDiv.innerHTML = `<p class="error">Error: ${result.error}</p>`;
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
    showSpinner('summary');
    fetchApi('api/summarize', { text, sentences })
        .then(result => {
            hideSpinner('summary');
            const resultDiv = document.getElementById('summary-result');
            if (result.error) {
                resultDiv.innerHTML = `<p class="error">Error: ${result.error}</p>`;
            } else {
                resultDiv.innerHTML = `<p>Summary: ${result.summary.join(' ')}</p>`;
            }
        });
}

// Code Debugger
function debugCode() {
    const code = document.getElementById('code-input').value;
    showSpinner('code');
    fetchApi('api/debug', { code })
        .then(result => {
            hideSpinner('code');
            const resultDiv = document.getElementById('code-result');
            if (result.error) {
                resultDiv.innerHTML = `<p class="error">Error: ${result.error}</p>`;
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
        document.getElementById('ats-result').innerHTML = '<p class="error">Please upload a resume and enter a job description.</p>';
        return;
    }
    showSpinner('ats');
    fetchApi('api/ats-score', { job_desc: jobDesc }, 'POST', file)
        .then(result => {
            hideSpinner('ats');
            const resultDiv = document.getElementById('ats-result');
            if (result.error) {
                resultDiv.innerHTML = `<p class="error">Error: ${result.error}</p>`;
            } else {
                resultDiv.innerHTML = `<p>ATS Score: ${result.score}</p><p>Matching Keywords: ${result.matches.join(', ')}</p>`;
            }
        });
}
