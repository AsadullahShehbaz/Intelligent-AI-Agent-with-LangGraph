# 🚀 Setup Guide - Authentication & File Upload

## 📦 Step 1: Install Required Packages

```bash
# PDF and document processing
pip install PyPDF2 python-docx

# Text processing
pip install langchain-text-splitters

# Translation (already have this if you added translation)
pip install googletrans==4.0.0-rc1

# Wikipedia (already have this)
pip install wikipedia
```

## 📁 Step 2: Project Structure

Your project should look like this:

```
your_project/
├── frontend.py                 # ✅ Replace with new version
├── agent.py                    # Keep existing
├── tools.py                    # ✅ Updated with document tool
├── memory.py                   # Keep existing
├── config.py                   # ✅ Add new config lines
├── auth.py                     # ✅ NEW FILE
├── document_analyzer.py        # ✅ NEW FILE
├── uploads/                    # Will be created automatically
├── users.db                    # Will be created automatically
└── checkpoints.db              # Existing
```

## ⚙️ Step 3: Update config.py

Add these lines to your `config.py`:

```python
# ============ Authentication ============
PASSWORD_SALT = "your_secret_salt_change_this_123456"  # CHANGE THIS!

# ============ File Upload ============
UPLOAD_FOLDER = "uploads"
MAX_FILE_SIZE_MB = 10
ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt']
```

## 🎯 Step 4: Create New Files

### 4.1 Create `auth.py`
Copy the complete authentication system code into `auth.py`

### 4.2 Create `document_analyzer.py`
Copy the complete document analyzer code into `document_analyzer.py`

### 4.3 Replace `frontend.py`
Replace your existing `frontend.py` with the new version that includes authentication

### 4.4 Update `tools.py`
Add the import and export for `ask_document` tool

## 🧪 Step 5: Test the System

### 5.1 Run the Application

```bash
streamlit run frontend.py
```

### 5.2 Create Your First Account

1. Click "📝 Sign Up"
2. Choose username (min 3 chars)
3. Enter email
4. Create password (min 6 chars)
5. Click "✅ Create Account"

### 5.3 Login

1. Enter your username and password
2. Click "🚀 Login"

### 5.4 Test File Upload

1. Click "Browse files" in sidebar
2. Upload a PDF, DOCX, or TXT file
3. Wait for "Document uploaded successfully!" message
4. Ask questions like:
   - "What is this document about?"
   - "Summarize the main points"
   - "Find information about [topic]"

## 🎨 Features You Now Have

### ✅ User Authentication
- [x] Sign up with username, email, password
- [x] Secure login with session management
- [x] Password hashing (SHA256)
- [x] Session expiry (7 days)
- [x] Logout functionality

### ✅ Document Analysis
- [x] Upload PDF, DOCX, TXT files
- [x] Automatic text extraction
- [x] Intelligent chunking
- [x] Vector storage in Qdrant
- [x] Semantic search
- [x] Ask questions about documents
- [x] View all uploaded documents
- [x] Delete documents

### ✅ User Isolation
- [x] Each user sees only their conversations
- [x] Each user sees only their documents
- [x] Secure data separation

### ✅ Enhanced Tools
- [x] Web Search
- [x] Calculator
- [x] YouTube Transcripts
- [x] Stock Prices
- [x] Wikipedia
- [x] Weather (wttr.in)
- [x] Translation (50+ languages)
- [x] **Document Q&A** ⭐ NEW!

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'PyPDF2'"
**Solution:**
```bash
pip install PyPDF2
```

### Issue: "ModuleNotFoundError: No module named 'docx'"
**Solution:**
```bash
pip install python-docx
```

### Issue: "No text found in document"
**Solution:**
- Make sure PDF is not scanned/image-based
- Try a different PDF with selectable text

### Issue: "Session expired" after login
**Solution:**
- Check that `users.db` has write permissions
- Make sure datetime is correctly imported

### Issue: Documents not showing up
**Solution:**
- Check Qdrant is running
- Verify `QDRANT_URL` and `QDRANT_API_KEY` in config
- Check `uploads/` folder exists and has write permissions

## 📊 Usage Examples

### Document Q&A Examples

```
User uploads "Python_Tutorial.pdf"

User: "What topics are covered in this document?"
Bot: "Based on your document Python_Tutorial.pdf, it covers: 
1. Variables and data types
2. Control flow (if/else, loops)
3. Functions and modules..."

User: "Explain the section about functions"
Bot: "According to chunk 5 of Python_Tutorial.pdf, functions are 
defined using the def keyword..."

User: "Give me code examples from the document"
Bot: "Here are the code examples found in your document: ..."
```

### Multi-Document Search

```
User uploads: "Report_Q1.pdf", "Report_Q2.pdf", "Summary.docx"

User: "What were the sales figures across all reports?"
Bot: "Based on your documents:
- Q1 Report: $1.2M
- Q2 Report: $1.5M
- Summary mentions total of $2.7M..."
```

## 🔐 Security Best Practices

1. **Change Password Salt**
   ```python
   # In config.py - use a random string
   PASSWORD_SALT = "use_a_random_string_here_min_32_chars"
   ```

2. **Use Environment Variables** (Production)
   ```python
   import os
   PASSWORD_SALT = os.environ.get("PASSWORD_SALT")
   ```

3. **Enable HTTPS** (Production)
   - Use SSL certificates
   - Deploy behind reverse proxy (Nginx)

4. **Regular Backups**
   ```bash
   # Backup databases
   cp users.db users_backup_$(date +%Y%m%d).db
   cp checkpoints.db checkpoints_backup_$(date +%Y%m%d).db
   ```

## 📈 Next Steps

Now that you have authentication and document analysis:

1. **Add Rate Limiting** - Prevent abuse
2. **Add Subscription Tiers** - Free vs Pro features
3. **Add Usage Dashboard** - Show document count, message count
4. **Add Batch Upload** - Upload multiple files at once
5. **Add OCR** - For scanned PDFs (use `pdf2image` + `pytesseract`)
6. **Add Document Preview** - Show document chunks in UI
7. **Add Citation** - Show which part of document was used

## 🎉 You're Ready!

Your AI Assistant now has:
- ✅ Multi-user support
- ✅ Secure authentication
- ✅ Document upload & analysis
- ✅ 8 powerful tools
- ✅ Conversation history
- ✅ Export functionality

Run `streamlit run frontend.py` and enjoy! 🚀