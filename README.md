# 🎓 Curriculum Curator

> A pedagogically-aware course content platform that empowers educators to create, curate, and enhance educational materials aligned with their unique teaching philosophy.

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Node](https://img.shields.io/badge/node-18%2B-green)

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Development](#development)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## 🌟 Overview

Curriculum Curator is an AI-powered platform designed to revolutionize how educators create and manage course content. By aligning with nine different pedagogical philosophies and leveraging advanced language models, it helps teachers generate high-quality, pedagogically-sound educational materials at any scale - from entire syllabi to individual worksheets.

### Who is this for?

- **Educators** who want to save time while maintaining pedagogical integrity
- **Institutions** looking to standardize and improve course content quality
- **Instructional Designers** needing AI-assisted content creation tools
- **Training Organizations** requiring scalable content development

## 🚀 Key Features

### 🎯 Pedagogical Alignment
- **9 Teaching Philosophies**: Traditional, Inquiry-Based, Project-Based, Collaborative, Game-Based, Flipped, Differentiated, Constructivist, and Experiential
- **Philosophy Detection**: Questionnaire to identify your teaching style
- **Adaptive AI**: Content generation aligned to your pedagogical approach

### 🔄 Multi-Scale Workflows
- **Course Level**: Generate entire 12-week course structures
- **Week Level**: Develop weekly modules and assignments
- **Item Level**: Create individual lectures, worksheets, quizzes, or activities

### 🤖 AI-Powered Features
- **Content Generation**: Stream-based real-time content creation
- **Enhancement**: Improve existing materials with AI suggestions
- **Validation**: Automatic quality checks and pedagogical alignment
- **Multiple LLMs**: Support for OpenAI, Anthropic, and Google Gemini

### 🛠️ Content Management
- **Import/Export**: Support for DOCX, PPTX, PDF, and Markdown
- **Rich Text Editing**: Full-featured editor with tables, code blocks, and formatting
- **Drag-and-Drop**: Organize content with intuitive interfaces
- **Version Control**: Track changes and maintain content history

### 🧙 Dual Interface Modes
- **Wizard Mode**: Step-by-step guided experience for beginners
- **Expert Mode**: Power-user interface for efficient bulk operations

### 🔌 Extensibility
- **Plugin System**: Custom validators and remediators
- **API-First**: RESTful API for integrations
- **Modular Architecture**: Easy to extend and customize

## 👥 User Roles

### Lecturer/Creator
- **Permissions**: Create, edit, and manage their own courses and content
- **Features Access**: 
  - Full content creation suite (lectures, worksheets, quizzes)
  - AI generation and enhancement tools
  - Import/export functionality
  - Teaching philosophy customization
  - Personal dashboard with course analytics
- **Restrictions**: Can only see and edit their own content

### Administrator
- **Permissions**: Manage users and system configuration
- **Features Access**:
  - User management (add, remove, approve users)
  - Email whitelist configuration
  - System settings and LLM API configuration
  - Audit logs and system monitoring
  - Platform analytics and usage statistics
- **Restrictions**: No content creation or editing capabilities

### Future Roles (Planned)
- **Student**: View published content, submit assignments
- **Reviewer**: Validate and approve content before publication
- **Department Head**: Oversee multiple lecturers' content

## 💻 Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.12+)
- **Database**: SQLAlchemy with SQLite (PostgreSQL ready)
- **Authentication**: JWT with email whitelist
- **LLM Integration**: LangChain
- **File Processing**: python-docx, python-pptx, PyPDF2

### Frontend
- **Framework**: React 18 with Vite
- **Styling**: Tailwind CSS
- **Editor**: TipTap (rich text editing)
- **State Management**: Zustand
- **HTTP Client**: Axios
- **UI Components**: Lucide Icons

## 🏃 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/curriculum-curator.git
cd curriculum-curator
```

2. **Set up the backend**
```bash
./backend.sh
# Or manually:
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
uvicorn app.main:app --reload
```

3. **Set up the frontend**
```bash
# In a new terminal
./frontend.sh
# Or manually:
cd frontend
npm install
npm run dev
```

4. **Access the application**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Default Credentials
- Email: `test@example.com`
- Password: `test`

## 📁 Project Structure

```
curriculum-curator/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/       # API endpoints
│   │   │   └── deps.py       # Dependencies
│   │   ├── core/
│   │   │   ├── config.py     # Configuration
│   │   │   ├── database.py   # Database setup
│   │   │   └── security.py   # Auth utilities
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/
│   │   │   ├── llm_service.py
│   │   │   └── content_generator.py
│   │   ├── plugins/          # Extensible plugins
│   │   │   ├── validators/
│   │   │   └── remediators/
│   │   └── main.py          # FastAPI app
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Editor/      # Rich text editor
│   │   │   ├── Layout/      # Dashboard layout
│   │   │   └── Wizard/      # Guided workflows
│   │   ├── features/
│   │   │   ├── auth/        # Authentication
│   │   │   ├── courses/     # Course management
│   │   │   └── content/     # Content creation
│   │   ├── pages/           # Main pages
│   │   ├── services/        # API integration
│   │   └── stores/          # State management
│   ├── package.json
│   └── vite.config.js
│
├── docs/                     # Documentation
├── scripts/                  # Utility scripts
├── docker-compose.yml        # Container orchestration
└── README.md
```

## 🔧 Development

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Quality
```bash
# Backend
black app/
flake8 app/
mypy app/

# Frontend
npm run lint
npm run format
```

### Building for Production
```bash
# Backend
cd backend
pip install -r requirements-prod.txt

# Frontend
cd frontend
npm run build
# Output in dist/
```

## 📚 API Documentation

### Authentication
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=test@example.com&password=test
```

### Content Generation
```http
POST /api/llm/generate
Authorization: Bearer {token}
Content-Type: application/json

{
  "content_type": "lecture",
  "pedagogy_style": "inquiry-based",
  "context": {
    "topic": "Introduction to Python",
    "duration": "50 minutes",
    "objectives": ["Understand variables", "Write first program"]
  },
  "stream": true
}
```

### Course Management
```http
GET /api/courses
Authorization: Bearer {token}

POST /api/courses
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "Computer Science 101",
  "code": "CS101",
  "weeks": 12
}
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite:///./curriculum_curator.db

# LLM API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...

# Email Configuration (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Feature Flags
ENABLE_AI_FEATURES=true
ENABLE_FILE_UPLOAD=true
DEBUG=true
```

### Frontend Configuration

Create `.env.local` in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
VITE_ENABLE_AI_FEATURES=true
```

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build individually
docker build -t curriculum-curator-backend ./backend
docker build -t curriculum-curator-frontend ./frontend
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) and [React](https://react.dev/)
- AI powered by [LangChain](https://langchain.com/)
- Rich text editing by [TipTap](https://tiptap.dev/)
- Icons by [Lucide](https://lucide.dev/)

## 📞 Support

- 📧 Email: support@curriculumcurator.com
- 📖 Documentation: [docs.curriculumcurator.com](https://docs.curriculumcurator.com)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/curriculum-curator/issues)

---

Made with ❤️ by educators, for educators
# Repository Status
Current implementation: FastAPI + React full-stack application
