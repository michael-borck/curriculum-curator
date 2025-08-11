# Getting Started with Curriculum Curator

This guide will help you get Curriculum Curator up and running on your system.

## Prerequisites

- Python 3.12 or higher
- pip (Python package manager)
- Git (for cloning the repository)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/curriculum-curator.git
cd curriculum-curator
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize Database

```bash
python -c "from core.database import init_db; init_db()"
```

### 5. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5001`

## First Steps

### 1. Create an Account

1. Navigate to `http://localhost:5001`
2. Click "Sign Up" in the navigation
3. Enter your details
4. Log in with your new credentials

### 2. Choose Your Mode

After logging in, you'll see two options:

#### Wizard Mode (Recommended for Beginners)
- Step-by-step guided process
- Clear instructions at each stage
- Best for first-time users

#### Expert Mode (For Power Users)
- All options on one page
- Faster workflow
- Requires familiarity with the system

### 3. Set Your Teaching Philosophy

The first time you create content, you'll be asked about your teaching style:

1. Answer 5 quick questions about your teaching approach
2. The system will detect your primary teaching style
3. This influences how content is generated
4. You can change this later in settings

### 4. Create Your First Course

#### In Wizard Mode:
1. **Step 1**: Enter course topic and audience
2. **Step 2**: Structure your course (weeks, topics)
3. **Step 3**: Select content types for each week
4. **Step 4**: Review and generate
5. **Step 5**: Download or refine content

#### In Expert Mode:
1. Fill out all course details in the form
2. Configure advanced options
3. Generate content
4. Use inline editing for refinements

## Configuration

### Environment Variables

```bash
# .env file
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///data/curriculum.db
CONTENT_DIR=data/courses
```

### Teaching Philosophy

You can manually set your teaching philosophy:

```python
# In settings or via API
teaching_style = "constructivist"  # or any of the 9 styles
```

### Plugin Configuration

Enable/disable validators and remediators:

```yaml
# config.yaml
validation:
  enabled:
    - readability
    - structure
    - grammar
    
remediation:
  auto_remediate: true
  enabled:
    - sentence_splitter
    - format_corrector
```

## Common Tasks

### Generate Course Materials

1. Create a new course
2. Define weekly structure
3. Select material types
4. Click "Generate"
5. Review and refine
6. Export when ready

### Use Custom Validators

1. Create validator in `plugins/validators/`
2. Restart the application
3. Enable in configuration
4. Validator runs automatically

### Export Content

Supported formats:
- Markdown (default)
- HTML
- PDF (requires wkhtmltopdf)
- DOCX
- LaTeX

### Manage Multiple Courses

- Dashboard shows all your courses
- Click course name to edit
- Archive completed courses
- Clone courses as templates

## Troubleshooting

### Application Won't Start

- Check Python version: `python --version`
- Ensure virtual environment is activated
- Verify all dependencies installed
- Check port 5001 is available

### Database Errors

- Run database initialization
- Check write permissions on data directory
- Verify DATABASE_URL in environment

### Content Generation Issues

- Ensure LLM API keys are configured
- Check network connectivity
- Review logs for specific errors
- Verify teaching philosophy is set

### Plugin Not Loading

- Check plugin has proper metadata
- Verify no import errors
- Review plugin logs
- Ensure plugin is in correct directory

## Next Steps

- Read about [Teaching Styles](teaching-styles.md)
- Learn to [Create Custom Validators](custom-validators.md)
- Explore [Advanced Configuration](../reference/configuration.md)
- Review [Architecture](../concepts/architecture.md)

## Getting Help

- Check the [FAQ](faq.md)
- Review [Common Issues](troubleshooting.md)
- Submit issues on GitHub
- Join our community forum