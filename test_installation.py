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
    required_packages = [
        'flask',
        'langchain',
        'langchain_groq',
        'langchain_google_genai',
        'chromadb',
        'unstructured',
        'PIL',
    ]
    
    all_ok = True
    for package in required_packages:
        try:
            __import__(package)
            print_status(f"Package '{package}' installed", "OK")
        except ImportError:
            print_status(f"Package '{package}' NOT installed", "ERROR")
            all_ok = False
    
    return all_ok

def check_env_file():
    """Check if .env file exists and has required keys"""
    if not os.path.exists('.env'):
        print_status(".env file NOT found", "ERROR")
        return False
    
    print_status(".env file found", "OK")
    
    # Read .env file
    with open('.env', 'r') as f:
        content = f.read()
    
    required_keys = ['GROQ_API_KEY', 'GOOGLE_API_KEY']
    all_ok = True
    
    for key in required_keys:
        if key in content:
            # Check if value is set (not empty)
            for line in content.split('\n'):
                if line.startswith(key):
                    value = line.split('=', 1)[1].strip()
                    if value and value != 'your_groq_api_key_here' and value != 'your_google_api_key_here':
                        print_status(f"{key} is set", "OK")
                    else:
                        print_status(f"{key} is NOT set (empty or default value)", "WARN")
                        all_ok = False
                    break
        else:
            print_status(f"{key} NOT found in .env", "ERROR")
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
    files = [
        'app.py',
        'rag_processor.py',
        'config.py',
        'requirements.txt',
        'templates/index.html',
        'static/css/style.css',
        'static/js/main.js'
    ]
    
    all_ok = True
    for file in files:
        if os.path.exists(file):
            print_status(f"File '{file}' exists", "OK")
        else:
            print_status(f"File '{file}' NOT found", "ERROR")
            all_ok = False
    
    return all_ok

def check_poppler():
    """Check if Poppler is installed"""
    import subprocess
    
    # First, add local Poppler to PATH if it exists
    local_poppler = r"C:\Users\Khush\OneDrive\Desktop\Agile Interview\poppler\poppler-24.08.0\Library\bin"
    if os.path.exists(local_poppler):
        os.environ["PATH"] = local_poppler + os.pathsep + os.environ.get("PATH", "")
        print_status(f"Found local Poppler at: {local_poppler}", "OK")
    
    try:
        result = subprocess.run(['pdfinfo', '-v'], capture_output=True, text=True)
        if result.returncode == 0:
            print_status("Poppler is installed and working", "OK")
            return True
        else:
            print_status("Poppler NOT found in PATH", "WARN")
            return False
    except FileNotFoundError:
        print_status("Poppler NOT found", "WARN")
        print(f"  Local path checked: {local_poppler}")
        print("  Download from: https://github.com/oschwartz10612/poppler-windows/releases/")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("Multi-Modal RAG Flask App - Installation Verification")
    print("=" * 60)
    print()
    
    checks = {
        "Python Version": check_python_version(),
        "Required Packages": check_imports(),
        "Environment File": check_env_file(),
        "Directories": check_directories(),
        "Files": check_files(),
        "Poppler": check_poppler()
    }
    
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_passed = all(checks.values())
    
    if all_passed:
        print("✓ All checks passed! You're ready to run the application.")
        print()
        print("To start the app, run:")
        print("  python app.py")
    else:
        print("⚠ Some checks failed. Please fix the issues above.")
        print()
        failed_checks = [name for name, passed in checks.items() if not passed]
        print("Failed checks:")
        for check in failed_checks:
            print(f"  - {check}")
    
    print()
    print("=" * 60)

if __name__ == '__main__':
    main()
