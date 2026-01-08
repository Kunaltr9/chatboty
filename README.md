Demo Chatbot

This is a minimal Flask-based demo chatbot using sentence-transformers for embeddings and scikit-learn for nearest-neighbor retrieval.

Quick start (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 in your browser.

Files:
- `app.py`: Flask app and retrieval logic
- `data.json`: sample documents
- `templates/index.html`: simple web UI
