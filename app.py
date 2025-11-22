from flask import Flask, render_template, request, jsonify, session
import os
from werkzeug.utils import secure_filename
import uuid
from rag_processor import RAGProcessor
import base64

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global dictionary to store RAG processors per session
rag_processors = {}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle PDF upload and process it"""
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only PDF files are allowed'}), 400
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{filename}")
        file.save(filepath)
        
        # Initialize RAG processor
        rag_processor = RAGProcessor()
        
        # Process the PDF
        result = rag_processor.process_pdf(filepath)
        
        # Store processor for this session
        rag_processors[session_id] = rag_processor
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'PDF processed successfully',
            'stats': result
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/ask', methods=['POST'])
def ask_question():
    """Handle question answering"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        session_id = session.get('session_id')
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        if not session_id or session_id not in rag_processors:
            return jsonify({'error': 'No document loaded. Please upload a PDF first'}), 400
        
        # Get RAG processor for this session
        rag_processor = rag_processors[session_id]
        
        # Get answer
        result = rag_processor.answer_question(question)
        
        return jsonify({
            'success': True,
            'answer': result['response'],
            'context': {
                'texts': [{'text': text.text, 'page_number': text.metadata.page_number} 
                         for text in result['context']['texts']],
                'images': [{'image_base64': img, 'index': idx + 1} 
                          for idx, img in enumerate(result['context']['images'])],
                'images_count': len(result['context']['images'])
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/reset', methods=['POST'])
def reset_session():
    """Reset the current session"""
    try:
        session_id = session.get('session_id')
        
        if session_id:
            # Remove processor
            if session_id in rag_processors:
                del rag_processors[session_id]
            
            # Remove uploaded file
            upload_folder = app.config['UPLOAD_FOLDER']
            for file in os.listdir(upload_folder):
                if file.startswith(session_id):
                    os.remove(os.path.join(upload_folder, file))
            
            session.pop('session_id', None)
        
        return jsonify({'success': True, 'message': 'Session reset successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
