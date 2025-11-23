"""
Test script to verify installation and configuration
Run this before starting the Flask app to check if everything is set up correctly
"""

import sys
import os

def print_status(message, status):
    """Print colored status message"""
    if status == "OK":
        print(f"✓ {message}")
    elif status == "WARN":
        print(f"⚠ {message}")
    else:
        print(f"✗ {message}")

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print_status(f"Python version: {version.major}.{version.minor}.{version.micro}", "OK")
        return True
    else:
        print_status(f"Python version too old: {version.major}.{version.minor}.{version.micro} (need 3.9+)", "ERROR")
        return False

def check_imports():
    """Check if required packages are installed"""
    required_packages = {
        'flask': 'Flask web framework',
        'langchain_unstructured': 'LangChain Unstructured integration',
        'langchain_groq': 'LangChain Groq integration',
        'langchain_google_genai': 'LangChain Google Gemini integration',
        'langchain_chroma': 'LangChain ChromaDB integration',
        'langchain_core': 'LangChain core library',
        'chromadb': 'ChromaDB vector store'
    }
    
    all_ok = True
    for package, description in required_packages.items():
        try:
            __import__(package)
            print_status(f"Package '{package}' installed ({description})", "OK")
        except ImportError:
            print_status(f"Package '{package}' NOT installed - {description}", "ERROR")
            all_ok = False
    
    return all_ok

def check_env_file():
    """Check if .env file exists and has required keys"""
    if not os.path.exists('.env'):
        print_status(".env file NOT found", "ERROR")
        print("  Create a .env file with your API keys:")
        print("  UNSTRUCTURED_API_KEY=your_key")
        print("  GROQ_API_KEY=your_key")
        print("  GOOGLE_API_KEY=your_key")
        return False
    
    print_status(".env file found", "OK")
    
    # Read .env file
    with open('.env', 'r') as f:
        content = f.read()
    
    required_keys = {
        'UNSTRUCTURED_API_KEY': 'https://unstructured.io',
        'GROQ_API_KEY': 'https://console.groq.com',
        'GOOGLE_API_KEY': 'https://aistudio.google.com/app/apikey'
    }
    
    all_ok = True
    
    for key, url in required_keys.items():
        if key in content:
            # Check if value is set (not empty)
            for line in content.split('\n'):
                if line.startswith(key):
                    value = line.split('=', 1)[1].strip() if '=' in line else ''
                    placeholder_values = ['your_key', 'your_api_key_here', 'your_unstructured_api_key_here', 
                                        'your_groq_api_key_here', 'your_google_api_key_here']
                    if value and value not in placeholder_values:
                        print_status(f"{key} is set", "OK")
                    else:
                        print_status(f"{key} is NOT set (empty or default value)", "ERROR")
                        print(f"  Get your key from: {url}")
                        all_ok = False
                    break
        else:
            print_status(f"{key} NOT found in .env", "ERROR")
            print(f"  Get your key from: {url}")
            all_ok = False
    
    return all_ok

def check_directories():
    """Check if required directories exist"""
    directories = ['templates', 'static', 'static/css', 'static/js']
    all_ok = True
    
    for directory in directories:
        if os.path.exists(directory):
            print_status(f"Directory '{directory}' exists", "OK")
        else:
            print_status(f"Directory '{directory}' NOT found", "ERROR")
            all_ok = False
    
    # Check uploads directory (should be auto-created)
    if not os.path.exists('uploads'):
        print_status("'uploads' directory will be created on first run", "WARN")
    else:
        print_status("'uploads' directory exists", "OK")
    
    return all_ok

def check_files():
    """Check if required files exist"""
    files = {
        'app.py': 'Main Flask application',
        'rag_processor.py': 'RAG processing logic',
        'config.py': 'Configuration settings',
        'requirements.txt': 'Python dependencies',
        'templates/index.html': 'Main HTML template',
        'static/css/style.css': 'CSS styles',
        'static/js/main.js': 'Frontend JavaScript'
    }
    
    all_ok = True
    for file, description in files.items():
        if os.path.exists(file):
            print_status(f"File '{file}' exists ({description})", "OK")
        else:
            print_status(f"File '{file}' NOT found - {description}", "ERROR")
            all_ok = False
    
    return all_ok

def check_internet_connection():
    """Check if internet connection is available"""
    import socket
    try:
        # Try to connect to Google DNS
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        print_status("Internet connection available", "OK")
        return True
    except OSError:
        print_status("No internet connection detected", "ERROR")
        print("  Cloud APIs require internet connection!")
        return False

def check_api_accessibility():
    """Check if API endpoints are accessible"""
    import urllib.request
    
    apis = {
        'Unstructured API': 'https://api.unstructuredapp.io',
        'Groq API': 'https://api.groq.com',
        'Google API': 'https://generativelanguage.googleapis.com'
    }
    
    accessible_count = 0
    for name, url in apis.items():
        try:
            urllib.request.urlopen(url, timeout=5)
            print_status(f"{name} is reachable", "OK")
            accessible_count += 1
        except Exception as e:
            error_str = str(e)[:60]
            # 404 errors are actually OK - it means the server is up but requires auth
            if "404" in error_str or "401" in error_str or "403" in error_str:
                print_status(f"{name} is reachable (auth required)", "OK")
                print(f"  Note: {error_str}")
                accessible_count += 1
            else:
                print_status(f"{name} connection check failed", "WARN")
                print(f"  Note: {error_str}")
                print(f"  This is OK if you have internet - API will work with valid keys")
    
    # Consider it OK if at least one API is reachable
    return accessible_count > 0

def main():
    """Main test function"""
    print("=" * 70)
    print("Multi-Modal RAG Flask App - Installation Verification (Cloud-Based)")
    print("=" * 70)
    print()
    
    print("📋 Checking Prerequisites...")
    print("-" * 70)
    
    checks = {
        "Python Version": check_python_version(),
        "Required Packages": check_imports(),
        "Environment File": check_env_file(),
        "Project Directories": check_directories(),
        "Project Files": check_files(),
        "Internet Connection": check_internet_connection(),
        "API Reachability (optional)": check_api_accessibility()
    }
    
    print()
    print("=" * 70)
    print("📊 Summary")
    print("=" * 70)
    
    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    
    print(f"\nPassed: {passed}/{total} checks")
    print()
    
    if all(checks.values()):
        print("✅ All checks passed! You're ready to run the application.")
        print()
        print("🚀 To start the app, run:")
        print("   python app.py")
        print()
        print("📝 Then open your browser to: http://localhost:5000")
        print()
        print("💡 Tips:")
        print("   - Upload a small PDF first to test (1-5 pages)")
        print("   - Check console for processing progress")
        print("   - First upload takes longer (model loading)")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print()
        failed_checks = [name for name, passed in checks.items() if not passed]
        print("❌ Failed checks:")
        for check in failed_checks:
            print(f"   - {check}")
        print()
        print("📖 See README.md for detailed setup instructions")
    
    print()
    print("=" * 70)
    print()
    print("ℹ️  Important Notes:")
    print("   • This application uses cloud APIs only")
    print("   • No local dependencies (Poppler, Tesseract) required!")
    print("   • API reachability warnings are normal - APIs work with valid keys")
    print("   • 404/403 errors on API checks = server is up, just needs authentication")
    print()
    print("=" * 70)

if __name__ == '__main__':
    main()
