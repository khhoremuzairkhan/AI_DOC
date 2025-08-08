# 🤖 AI PDF Document Generator

A powerful web application that generates professional PDF documents (cover letters, resumes, proposals, letters) using AI technology.

## ✨ Features

- 📄 **Multiple Document Types**: Cover letters, resumes, business proposals, formal letters
- 🤖 **AI-Powered Generation**: Uses advanced language models for content creation
- 📱 **User-Friendly Interface**: Clean, intuitive Streamlit web interface
- 📥 **Instant PDF Download**: Generate and download PDFs immediately
- 🔄 **Preview Mode**: Preview content before generating PDF
- 🆓 **Free to Use**: Works with free API tiers and template mode

## 🚀 Live Demo

**Deployed on Streamlit Cloud:** [Your App URL Here]

## 🏃‍♂️ Quick Start

### Option 1: Try Online
Just visit the live demo link above - no installation required!

### Option 2: Run Locally
```bash
git clone https://github.com/yourusername/ai-pdf-generator
cd ai-pdf-generator
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 📋 Requirements

- Python 3.8+
- Streamlit
- ReportLab
- Requests

## 🔧 Setup for Enhanced AI Features

The app works out of the box with template mode. For advanced AI generation:

1. Get a free API key from [Groq](https://console.groq.com) (recommended - very fast)
2. Add to Streamlit Cloud secrets or local `.streamlit/secrets.toml`:

```toml
GROQ_TOKEN = "your_groq_api_key_here"
```

## 📖 How to Use

1. **Select Document Type**: Choose from Cover Letter, Resume, Business Proposal, or Formal Letter
2. **Enter Requirements**: Provide detailed information about what you want in your document
3. **Preview Content**: Click "Preview Content" to see the generated text
4. **Generate PDF**: Click "Generate PDF" to create and download your document

## 🌟 Example Prompts

**Cover Letter:**
> I'm applying for a Software Engineer position at Google. I have 5 years of Python experience, worked at startups, and am passionate about AI/ML.

**Resume:**
> Create a resume for John Smith, Software Engineer with 8 years experience. Skills: Python, JavaScript, React, AWS, Docker. Worked at TechCorp (2020-2024) as Senior Developer.

**Business Proposal:**
> Proposal for implementing AI chatbot solution for customer service. Current issues: long wait times, high support costs. Solution: 24/7 AI assistant.

## 🚀 Deploy Your Own

### Deploy to Streamlit Cloud (Free)
1. Fork this repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select this repository
5. Deploy!

### Deploy to Other Platforms
- **Heroku**: Use the included `Procfile`
- **Railway**: Use the Docker configuration
- **Render**: Deploy directly from GitHub

## 🛠️ Technology Stack

- **Frontend & Backend**: Streamlit (Python)
- **PDF Generation**: ReportLab
- **AI Integration**: Groq API / Hugging Face
- **Hosting**: Streamlit Community Cloud

## 📄 License

MIT License - Feel free to use and modify!

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 🐛 Issues

Found a bug or have a feature request? Please open an issue on GitHub.

## 📞 Support

- 📧 Email: your-email@example.com  
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions

---

⭐ **Star this repository if you find it useful!** ⭐