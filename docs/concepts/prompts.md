# Prompts

Prompts are the instructions given to language models (LLMs) to generate educational content within the Curriculum Curator system.

## Overview

Prompts in Curriculum Curator are structured templates that guide LLMs to produce specific types of educational content. The system uses a prompt registry to organize and manage these templates, making them accessible across workflows.

## Prompt Templates

Prompt templates are stored as text files with special placeholders for dynamic content. These placeholders are replaced with actual values when the prompt is used in a workflow.

Example prompt template for generating a module outline:

```
Create a detailed outline for a module on {topic} appropriate for {learning_level} students.

The outline should include:
- Learning objectives (3-5)
- Key topics and subtopics (5-7)
- Suggested activities (2-3)
- Assessment methods

Format the outline with clear hierarchical structure using markdown syntax.
Ensure all content is factually accurate and pedagogically sound.
```

## Prompt Registry

The prompt registry is a central repository for all prompt templates in the system. It:

- Organizes prompts by category and purpose
- Provides versioning for prompt templates
- Allows sharing and reuse of effective prompts
- Supports loading prompts from files or embedded resources

## Prompt Parameters

Prompts can include parameters that are populated when the prompt is used:

- Topic parameters (e.g., "Machine Learning", "Ancient Rome")
- Learning level parameters (e.g., "beginner", "advanced")
- Format parameters (e.g., "outline", "detailed notes")
- Educational context parameters (e.g., "high school", "university")

## Interactive Prompt Editor

Curriculum Curator provides an interactive prompt editor that allows you to:

1. Create new prompt templates
2. Edit existing templates
3. Test prompts with sample parameters
4. Preview generated content
5. Save and version prompt templates

For more information, see the [Prompt Editor Guide](../guides/prompt-editor.md).

## Best Practices

When creating prompts for educational content:

- Be specific about the expected output format
- Include clear instructions about learning objectives
- Specify the target audience and their background knowledge
- Include guidelines for pedagogical approaches
- Request appropriate depth and breadth of coverage
- Specify any educational standards or frameworks to consider

## Prompt Categories

The system organizes prompts into several categories:

- **Course**: High-level course design prompts
- **Module**: Module and unit design prompts
- **Lecture**: Lecture content generation prompts
- **Assessment**: Quiz, test, and assessment prompts
- **Instructor**: Instructor guides and teaching notes
- **Worksheet**: Student activity and worksheet prompts

Each category has specialized prompts designed for specific educational content types.
