// Chat history storage
let chatHistory = [];

// DOM Elements
const uploadForm = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const fileName = document.getElementById('fileName');
const uploadBtn = document.getElementById('uploadBtn');
const uploadStatus = document.getElementById('uploadStatus');
const uploadSection = document.getElementById('uploadSection');
const questionSection = document.getElementById('questionSection');
const questionForm = document.getElementById('questionForm');
const questionInput = document.getElementById('questionInput');
const askBtn = document.getElementById('askBtn');
const answerSection = document.getElementById('answerSection');
const answerText = document.getElementById('answerText');
const contextInfo = document.getElementById('contextInfo');
const resetBtn = document.getElementById('resetBtn');
const chatHistorySection = document.getElementById('chatHistory');
const chatMessages = document.getElementById('chatMessages');

// Update file name display when file is selected
fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        fileName.textContent = file.name;
    } else {
        fileName.textContent = 'Choose PDF file...';
    }
});

// Handle file upload
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const file = fileInput.files[0];
    if (!file) {
        showStatus('Please select a PDF file', 'error');
        return;
    }

    // Show loading state
    setLoading(uploadBtn, true);
    uploadStatus.textContent = '';
    uploadStatus.className = 'status-message';

    try {
        const formData = new FormData();
        formData.append('file', file);
        
        // Add API keys if they exist in the form (for users without server keys)
        const unstructuredKey = document.getElementById('unstructuredKey');
        const groqKey = document.getElementById('groqKey');
        const googleKey = document.getElementById('googleKey');
        
        if (unstructuredKey) {
            if (!unstructuredKey.value || !groqKey.value || !googleKey.value) {
                showStatus('❌ Please enter all three API keys', 'error');
                setLoading(uploadBtn, false);
                return;
            }
            formData.append('unstructured_api_key', unstructuredKey.value);
            formData.append('groq_api_key', groqKey.value);
            formData.append('google_api_key', googleKey.value);
        }

        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            showStatus(
                `✅ ${data.message}\n\nProcessed: ${data.stats.total_chunks} chunks (${data.stats.text_chunks} texts, ${data.stats.images} images, ${data.stats.tables} tables)`,
                'success'
            );
            
            // Show question section
            setTimeout(() => {
                questionSection.style.display = 'block';
                questionSection.scrollIntoView({ behavior: 'smooth' });
            }, 500);
        } else {
            showStatus(`❌ Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showStatus(`❌ Error: ${error.message}`, 'error');
    } finally {
        setLoading(uploadBtn, false);
    }
});

// Handle question submission
questionForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const question = questionInput.value.trim();
    if (!question) {
        return;
    }

    // Show loading state
    setLoading(askBtn, true);

    try {
        const response = await fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question })
        });

        const data = await response.json();

        if (data.success) {
            // Display answer
            displayAnswer(data.answer, data.context);

            // Add to chat history
            addToChatHistory(question, data.answer);

            // Clear input
            questionInput.value = '';
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    } finally {
        setLoading(askBtn, false);
    }
});

// Handle reset
resetBtn.addEventListener('click', async () => {
    if (!confirm('Are you sure you want to reset? This will clear the current document and chat history.')) {
        return;
    }

    try {
        const response = await fetch('/reset', {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            // Reset UI
            questionSection.style.display = 'none';
            answerSection.style.display = 'none';
            chatHistorySection.style.display = 'none';
            uploadStatus.textContent = '';
            uploadStatus.className = 'status-message';
            fileInput.value = '';
            fileName.textContent = 'Choose PDF file...';
            questionInput.value = '';
            chatHistory = [];
            
            // Scroll to top
            uploadSection.scrollIntoView({ behavior: 'smooth' });
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
});

// Helper Functions
function showStatus(message, type) {
    uploadStatus.textContent = message;
    uploadStatus.className = `status-message ${type}`;
}

function setLoading(button, isLoading) {
    if (isLoading) {
        button.disabled = true;
        button.classList.add('loading');
        button.querySelector('.spinner').style.display = 'inline-block';
        button.querySelector('.btn-text').style.opacity = '0';
    } else {
        button.disabled = false;
        button.classList.remove('loading');
        button.querySelector('.spinner').style.display = 'none';
        button.querySelector('.btn-text').style.opacity = '1';
    }
}

function displayAnswer(answer, context) {
    // Show answer section
    answerSection.style.display = 'block';
    
    // Display answer text
    answerText.textContent = answer;

    // Display context information
    let contextHTML = '';
    
    if (context.texts && context.texts.length > 0) {
        contextHTML += '<div style="margin-bottom: 1rem;">';
        contextHTML += `<strong>Text chunks used: ${context.texts.length}</strong>`;
        contextHTML += '</div>';
        
        context.texts.forEach((text, index) => {
            contextHTML += `
                <div class="context-item">
                    <div><strong>Chunk ${index + 1}</strong> (Page <span class="page-number">${text.page_number}</span>)</div>
                    <div style="margin-top: 0.5rem; font-size: 0.85rem; color: var(--text-secondary);">
                        ${text.text.substring(0, 200)}${text.text.length > 200 ? '...' : ''}
                    </div>
                </div>
            `;
        });
    }

    if (context.images && context.images.length > 0) {
        contextHTML += `<div style="margin-top: 1rem; margin-bottom: 0.5rem;"><strong>Images used: ${context.images.length}</strong></div>`;
        
        context.images.forEach((image) => {
            contextHTML += `
                <div class="context-item" style="text-align: center;">
                    <div><strong>Image ${image.index}</strong></div>
                    <div style="margin-top: 0.5rem;">
                        <img src="data:image/jpeg;base64,${image.image_base64}" 
                             alt="Context Image ${image.index}" 
                             style="max-width: 100%; max-height: 400px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />
                    </div>
                </div>
            `;
        });
    }

    contextInfo.innerHTML = contextHTML;

    // Scroll to answer
    answerSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function addToChatHistory(question, answer) {
    chatHistory.push({ question, answer, timestamp: new Date() });

    // Show chat history section
    chatHistorySection.style.display = 'block';

    // Update chat messages
    const messageHTML = `
        <div class="chat-message question">
            <div class="chat-message-label">Question</div>
            <div class="chat-message-text">${escapeHtml(question)}</div>
        </div>
        <div class="chat-message answer">
            <div class="chat-message-label">Answer</div>
            <div class="chat-message-text">${escapeHtml(answer)}</div>
        </div>
    `;

    chatMessages.innerHTML = messageHTML + chatMessages.innerHTML;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize
console.log('Multi-Modal RAG System loaded');
