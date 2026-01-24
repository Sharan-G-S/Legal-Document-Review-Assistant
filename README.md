# Legal Document Review Assistant
# Sharan G S

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)

An AI-powered legal document review assistant that automates document analysis, highlights key clauses, assesses risks, and provides actionable insights. Built with Flask, spaCy, and modern web technologies.

## 🌟 Features

### AI-Powered Analysis
- **Clause Detection**: Automatically identifies and categorizes legal clauses (confidentiality, liability, termination, payment, IP, dispute resolution, etc.)
- **Risk Assessment**: Evaluates document risk with detailed scoring and severity levels (Low, Medium, High, Critical)
- **Key Terms Extraction**: Extracts important entities, dates, monetary values, and parties
- **Document Summarization**: Generates executive summaries with document type, purpose, and key points
- **Issue Identification**: Flags vague language, one-sided terms, unlimited obligations, and missing clauses

### Professional Features
- **Multi-Format Support**: Process PDF and DOCX documents
- **PDF Report Generation**: Export comprehensive analysis reports
- **Modern UI/UX**: Professional legal-themed interface with dark mode
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Real-time Processing**: Live progress tracking during analysis

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Modern web browser

### Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd "/Users/sharan/Downloads/Legal Document Review Assistant"
   ```

2. **Install Python dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Download spaCy language model**
   ```bash
   python -m spacy download en_core_web_sm
   ```

### Running the Application

1. **Start the Backend Server**
   ```bash
   cd backend
   python app.py
   ```
   The API will be available at `http://localhost:5000`

2. **Start the Frontend (in a new terminal)**
   ```bash
   cd frontend
   python -m http.server 8080
   ```
   Open your browser to `http://localhost:8080`

## 📖 Usage

1. **Upload Document**: Click the upload area or drag and drop a PDF/DOCX legal document
2. **Wait for Analysis**: The AI will process the document (typically 10-30 seconds)
3. **Review Results**: Examine detected clauses, risk assessment, and recommendations
4. **Export Report**: Download a professional PDF report of the analysis

## 🏗️ Architecture

```
Legal Document Review Assistant/
├── backend/
│   ├── app.py                 # Flask application entry point
│   ├── config.py              # Configuration management
│   ├── requirements.txt       # Python dependencies
│   ├── ai/                    # AI/ML modules
│   │   ├── clause_detector.py      # Clause detection engine
│   │   ├── risk_analyzer.py        # Risk assessment engine
│   │   ├── key_terms_extractor.py  # Key terms extraction
│   │   └── summarizer.py           # Document summarization
│   ├── api/                   # REST API endpoints
│   │   └── routes.py
│   ├── models/                # Data models
│   │   └── models.py
│   ├── services/              # Business logic
│   │   ├── document_processor.py   # Main processing pipeline
│   │   └── text_extractor.py       # Text extraction
│   └── utils/                 # Utilities
│       └── pdf_generator.py        # PDF report generation
└── frontend/
    ├── index.html             # Main HTML structure
    ├── css/
    │   └── styles.css         # Professional styling
    └── js/
        └── app.js             # Application logic
```

## 🔌 API Endpoints

### Document Management
- `POST /api/upload` - Upload and process document
- `GET /api/documents` - List all processed documents
- `GET /api/document/<id>` - Get complete document analysis

### Analysis Results
- `GET /api/document/<id>/clauses` - Get detected clauses
- `GET /api/document/<id>/risks` - Get risk assessment
- `GET /api/document/<id>/summary` - Get document summary

### Export & Stats
- `POST /api/export/<id>` - Export analysis as PDF
- `GET /api/stats` - Get overall statistics
- `GET /api/docs` - API documentation

## 🎨 UI Features

- **Professional Legal Theme**: Deep blue and gold color palette
- **Dark Mode**: Toggle between light and dark themes
- **Glassmorphism Effects**: Modern, premium design aesthetics
- **Responsive Layout**: Adapts to all screen sizes
- **Smooth Animations**: Polished user experience
- **Risk Visualization**: Color-coded risk levels and badges

## 🧠 AI Capabilities

### Clause Categories Detected
- Confidentiality / Non-Disclosure
- Limitation of Liability
- Termination Conditions
- Payment Terms
- Intellectual Property
- Dispute Resolution / Arbitration
- Force Majeure
- Warranties and Representations
- Assignment Rights
- Governing Law and Jurisdiction

### Risk Factors Analyzed
- Unfavorable or one-sided terms
- Missing essential clauses
- Vague or ambiguous language
- Unusual or extreme obligations
- Unlimited liability exposure
- Perpetual or indefinite terms

## 🛠️ Technology Stack

**Backend:**
- Flask 3.0.0 - Web framework
- spaCy 3.7.2 - NLP and entity recognition
- scikit-learn 1.3.2 - TF-IDF and ML utilities
- PyPDF2 & pdfplumber - PDF text extraction
- python-docx - DOCX processing
- ReportLab - PDF report generation

**Frontend:**
- Vanilla JavaScript (ES6+)
- Modern CSS with CSS Variables
- Google Fonts (Inter, Playfair Display)
- Responsive Grid & Flexbox layouts

## 📊 Sample Analysis Output

```json
{
  "document_type": "Non-Disclosure Agreement (NDA)",
  "overall_risk_level": "medium",
  "overall_risk_score": 45.2,
  "clauses_detected": 12,
  "high_risk_clauses": 2,
  "missing_clauses": ["Dispute Resolution/Arbitration"],
  "key_recommendations": [
    "Review liability limitations carefully",
    "Add dispute resolution mechanism",
    "Clarify termination notice period"
  ]
}
```

## 🔒 Privacy & Security

- **Local Processing**: All document analysis happens locally on your server
- **No External APIs**: No documents are sent to third-party services
- **Data Control**: You maintain full control over your documents and analysis results
- **Secure Storage**: Documents and results are stored in local directories


## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Built with Flask and spaCy
- Inspired by the need for accessible legal document analysis
- Designed for legal professionals, businesses, and individuals

## 📧 Support

For questions or support, please open an issue in the repository.

Made with 💚 from Sharan G S
