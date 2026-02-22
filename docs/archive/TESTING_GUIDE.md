# Testing Guide for Curriculum Curator

## Setup

1. **Activate the virtual environment**:
   ```bash
   source .venv/bin/activate  # or use uv if you prefer
   ```

2. **Install/update dependencies** (if needed):
   ```bash
   uv pip install -e .
   # or
   pip install -e .
   ```

## Testing the Plugin System

### 1. Test Plugin Discovery

Run the plugin test script to verify plugins are loading:

```bash
python test_plugins.py
```

Expected output:
- List of discovered validators (including `readability`)
- List of discovered remediators (including `sentence_splitter`)
- Validation results on test content
- Remediation results if issues are found

### 2. Test the Web Application

Start the development server:

```bash
python run_dev.py
# or
python app.py
```

Then open http://localhost:5000 in your browser.

### 3. Manual Testing Workflow

1. **Upload a document**:
   - Click the upload area
   - Select `test_files/test_content.md` or any .docx/.pptx file
   - You should see "File Uploaded Successfully"

2. **Analyze content**:
   - Click "🔍 Analyze Content"
   - You should see:
     - Content Analysis Results (learning objectives, quality metrics)
     - Validation Results (from plugins)

3. **Check validation results**:
   - Look for readability warnings (long sentences)
   - Check for any other validation issues
   - Each issue should show severity, message, and suggestions

4. **Test API endpoints**:
   - http://localhost:5000/api/plugins/validators - List validators
   - http://localhost:5000/api/plugins/remediators - List remediators
   - http://localhost:5000/health - Health check

## Testing with Different Content

### Example with readability issues:

Create a file with problematic content:

```markdown
# Test Document

This is an extraordinarily long sentence that demonstrates the kind of problematic writing 
that the readability validator should catch because it contains far too many words and 
ideas crammed into a single grammatical structure which makes it very difficult for 
readers to parse and understand the meaning effectively.

## Learning Objectives

Students will understand concepts.

## Content

Here is some content without proper examples or activities.
```

### Expected Plugin Behavior:

1. **ReadabilityValidator** should catch:
   - Long sentences (>25 words average)
   - Low readability scores
   - Complex sentence structures

2. **SentenceSplitter** remediator should:
   - Split sentences at conjunctions
   - Maintain meaning while improving readability

## Troubleshooting

### If plugins aren't loading:

1. Check that `__init__.py` files exist in all plugin directories
2. Verify the plugin has proper metadata defined
3. Check console for import errors

### If validation isn't running:

1. Ensure `textstat` is installed: `pip install textstat`
2. Check that async functions are properly awaited
3. Look for errors in the browser console or server logs

### Common issues:

- **ModuleNotFoundError**: Make sure you're in the virtual environment
- **Import errors**: Check that all plugin files have correct imports
- **No validators found**: Verify plugin discovery path is correct

## Adding New Plugins

To test plugin extensibility:

1. Create a new validator in `plugins/validators/quality/`:
   ```python
   from plugins.validators.base import BaseValidator, ValidationResult, ValidationIssue
   
   class MyValidator(BaseValidator):
       metadata = PluginMetadata(
           name="my_validator",
           version="1.0.0",
           description="My custom validator",
           author="Me",
           category="validators"
       )
       
       async def validate(self, content, context=None):
           # Your validation logic
           return ValidationResult(valid=True, issues=[])
   ```

2. Restart the server and check if it appears in the API

## Performance Testing

For larger documents:

1. Try uploading a multi-page Word document
2. Check analysis time
3. Monitor memory usage
4. Verify all content is processed

The plugin system is designed to handle documents up to several thousand words efficiently.