# Teaching Style Configuration Guide

This guide explains how to configure and use the Teaching Philosophy system in Curriculum Curator.

## Understanding Teaching Styles

Curriculum Curator recognizes 9 distinct teaching styles, each with unique characteristics that influence content generation:

### 1. Traditional Lecture
**Best for:** Large classes, foundational knowledge
- Highly structured content
- Clear information delivery
- Limited student interaction
- Formal academic tone

### 2. Constructivist
**Best for:** Deep understanding, critical thinking
- Discovery-based learning
- Open-ended questions
- High student reflection
- Multiple perspectives

### 3. Direct Instruction
**Best for:** Skill acquisition, procedures
- Step-by-step guidance
- Clear objectives
- Frequent practice
- Immediate feedback

### 4. Inquiry-Based
**Best for:** Research skills, scientific thinking
- Question-driven
- Student investigation
- Hypothesis testing
- Evidence-based conclusions

### 5. Flipped Classroom
**Best for:** Active learning, application
- Pre-class preparation
- In-class activities
- Collaborative work
- Problem-solving focus

### 6. Project-Based
**Best for:** Real-world application, teamwork
- Authentic projects
- Extended timelines
- Interdisciplinary
- Student ownership

### 7. Competency-Based
**Best for:** Professional training, certification
- Skill mastery focus
- Self-paced progress
- Clear benchmarks
- Performance assessment

### 8. Culturally Responsive
**Best for:** Diverse classrooms, inclusion
- Multiple perspectives
- Cultural relevance
- Inclusive examples
- Community connections

### 9. Mixed Approach
**Best for:** Flexible teaching, varied content
- Combines methods
- Adaptive to needs
- Balanced approach
- Context-dependent

## Initial Setup

### Teaching Style Questionnaire

When you first use Curriculum Curator, you'll answer 5 questions:

1. **How do you prefer to structure your class sessions?**
   - Influences: structure_preference, interaction_level

2. **How much student interaction do you typically encourage?**
   - Influences: interaction_level, student_centered

3. **How do you integrate technology in teaching?**
   - Influences: technology_integration

4. **What's your preferred assessment style?**
   - Influences: assessment_frequency, student_centered

5. **Which teaching methodology resonates most?**
   - Influences: overall style selection

### Manual Configuration

You can also set your teaching style directly:

```python
# In your user profile
user.teaching_philosophy = "constructivist"
```

Or via the web interface:
1. Go to Settings
2. Click "Teaching Philosophy"
3. Select your preferred style
4. Save changes

## How Teaching Style Affects Content

### Content Structure

#### High Structure (Traditional, Direct)
```markdown
# Lesson: Introduction to Functions

## Learning Objectives
1. Define what a function is
2. Identify function components
3. Write simple functions

## 1. Definition
A function is...

## 2. Components
### 2.1 Function Name
### 2.2 Parameters
### 2.3 Return Value

## Summary
- Key point 1
- Key point 2
```

#### Low Structure (Constructivist, Inquiry)
```markdown
# Exploring Functions

*What patterns do you notice in these code examples?*

```python
greet("Alice")
calculate_area(5, 10)
find_maximum([3, 7, 2, 9])
```

*Before reading further, try to identify what these have in common...*

## Your Investigation
Experiment with the code above. What happens when you...
```

### Interaction Prompts

#### High Interaction (Flipped, Project-Based)
- "Discuss with a partner..."
- "In your group, design..."
- "Share your solution with..."
- "Peer review the following..."

#### Low Interaction (Traditional, Direct)
- "Note the following..."
- "Observe that..."
- "The key principle is..."
- "Remember to..."

### Assessment Integration

#### Continuous (Competency, Flipped)
- Self-check questions throughout
- Practice problems after each concept
- Reflection prompts
- Progress indicators

#### Summative (Traditional, Direct)
- End-of-unit tests
- Comprehensive reviews
- Final projects
- Formal evaluations

## Advanced Configuration

### Per-Course Settings

Different courses may need different approaches:

```yaml
# Course-specific overrides
courses:
  intro_programming:
    teaching_style: direct_instruction
    indicators:
      structure_preference: 9
      technology_integration: 7
  
  advanced_algorithms:
    teaching_style: inquiry_based
    indicators:
      student_centered: 8
      collaboration_emphasis: 6
```

### Custom Style Blends

Create your own teaching style blend:

```python
from core.teaching_philosophy import TeachingStyleIndicators

custom_style = TeachingStyleIndicators(
    interaction_level=7,
    structure_preference=5,
    student_centered=8,
    technology_integration=9,
    assessment_frequency="high",
    collaboration_emphasis=6
)

# Save as custom profile
user.custom_teaching_style = custom_style
```

### Contextual Adaptation

The system can adapt based on content type:

```python
# Different styles for different materials
style_mapping = {
    "lecture": "traditional_lecture",
    "workshop": "constructivist",
    "lab": "inquiry_based",
    "project": "project_based"
}
```

## Prompt Engineering by Style

### How Prompts Are Modified

#### Base Prompt
```
Create educational content about {topic} for {audience}.
```

#### Traditional Lecture Enhancement
```
Create educational content about {topic} for {audience}.

Structure the content with:
- Clear learning objectives at the start
- Organized sections with numbered headings
- Comprehensive coverage of all aspects
- Formal academic language
- Summary points at the end
- Limited interactive elements
```

#### Constructivist Enhancement
```
Create educational content about {topic} for {audience}.

Design the content to:
- Start with thought-provoking questions
- Include exploration activities
- Present multiple perspectives
- Encourage student reflection
- Use open-ended scenarios
- Build on prior knowledge
```

#### Project-Based Enhancement
```
Create educational content about {topic} for {audience}.

Frame the content around:
- A real-world project scenario
- Clear project deliverables
- Team collaboration opportunities
- Milestone checkpoints
- Authentic assessment criteria
- Cross-disciplinary connections
```

## Teaching Style Indicators

### Understanding the Metrics

Each style is characterized by 6 indicators:

1. **Interaction Level (0-10)**
   - 0: Pure lecture, no interaction
   - 5: Some Q&A and discussion
   - 10: Constant peer interaction

2. **Structure Preference (0-10)**
   - 0: Completely flexible/emergent
   - 5: Loose framework
   - 10: Rigid structure

3. **Student-Centered (0-10)**
   - 0: Teacher drives everything
   - 5: Shared control
   - 10: Students lead learning

4. **Technology Integration (0-10)**
   - 0: No technology use
   - 5: Basic tools (slides, LMS)
   - 10: Cutting-edge tech integration

5. **Assessment Frequency**
   - Low: Major tests only
   - Medium: Regular quizzes
   - High: Continuous assessment

6. **Collaboration Emphasis (0-10)**
   - 0: Individual work only
   - 5: Occasional group work
   - 10: Always collaborative

### Indicator Profiles by Style

```python
# Traditional Lecture
indicators = {
    "interaction_level": 2,
    "structure_preference": 9,
    "student_centered": 2,
    "technology_integration": 3,
    "assessment_frequency": "low",
    "collaboration_emphasis": 1
}

# Flipped Classroom
indicators = {
    "interaction_level": 8,
    "structure_preference": 6,
    "student_centered": 7,
    "technology_integration": 8,
    "assessment_frequency": "high",
    "collaboration_emphasis": 7
}
```

## Practical Examples

### Example 1: Math Lesson

#### Traditional Approach
```markdown
# Lesson 5: Quadratic Equations

## Objectives
- Define quadratic equations
- Apply the quadratic formula
- Solve word problems

## 5.1 Definition
A quadratic equation is an equation of the form ax² + bx + c = 0...

## 5.2 The Quadratic Formula
x = (-b ± √(b² - 4ac)) / 2a

## 5.3 Examples
### Example 1: Solve x² + 5x + 6 = 0
```

#### Constructivist Approach
```markdown
# Discovering Patterns in Parabolas

## A Ball's Journey
Imagine throwing a ball upward. Sketch its path.

*What mathematical relationship might describe this path?*

## Exploration Station
Using the graphing tool, plot these equations:
- y = x²
- y = x² + 2
- y = x² - 3

*What patterns emerge? Discuss with your partner.*
```

### Example 2: History Lesson

#### Inquiry-Based Approach
```markdown
# The Mystery of the Lost Colony

## Your Mission
You're a detective investigating the disappearance of the Roanoke colony.

## Evidence Files
- Document A: Governor's last letter
- Document B: Native American accounts
- Document C: Archaeological findings

## Investigation Questions
1. What theories can you develop?
2. Which evidence supports each theory?
3. What additional evidence would help?
```

#### Direct Instruction Approach
```markdown
# The Roanoke Colony: 1587-1590

## Learning Goals
By the end of this lesson, you will:
1. Identify when Roanoke was established
2. Name key figures involved
3. List three theories about its disappearance

## Step 1: Background
In 1587, John White led 115 colonists...
```

## Troubleshooting

### Content Doesn't Match Style

**Problem:** Generated content seems generic
**Solution:** 
- Verify teaching style is set correctly
- Check if LLM prompts include style parameters
- Review style indicators for accuracy

### Style Detection Issues

**Problem:** Detected style doesn't match teaching approach
**Solution:**
- Retake questionnaire with more thought
- Manually override detected style
- Create custom style blend

### Inconsistent Results

**Problem:** Content varies too much
**Solution:**
- Use consistent context parameters
- Save successful prompts as templates
- Lock style for specific courses

## Best Practices

### 1. Know Your Context
- Consider class size
- Account for student background
- Factor in available technology
- Think about time constraints

### 2. Be Flexible
- No style fits all situations
- Adjust based on topic
- Consider mixing approaches
- Respond to student needs

### 3. Iterate and Improve
- Track what works
- Gather student feedback
- Refine your indicators
- Share successful patterns

### 4. Document Preferences
- Save effective prompts
- Note style combinations
- Record context factors
- Build template library

## Integration with Other Features

### Validators by Style

Different validators activate based on teaching style:

```python
style_validators = {
    "traditional_lecture": [
        "structure_validator",
        "completeness_checker",
        "formal_tone_validator"
    ],
    "constructivist": [
        "open_ended_validator",
        "reflection_checker",
        "perspective_validator"
    ],
    "project_based": [
        "authenticity_validator",
        "collaboration_checker",
        "milestone_validator"
    ]
}
```

### Export Formats by Style

Preferred export formats vary:

```python
style_exports = {
    "traditional_lecture": ["pdf", "pptx"],
    "flipped_classroom": ["html", "video_script"],
    "project_based": ["markdown", "rubric"],
    "competency_based": ["checklist", "badge_criteria"]
}
```

## Future Enhancements

### Planned Features
- AI-powered style recommendation
- Style effectiveness analytics
- Peer style sharing marketplace
- Dynamic style adaptation

### Research Integration
- Link to education research
- Evidence-based refinements
- Outcome tracking
- Best practice updates

## Additional Resources

- [Teaching Philosophy Concepts](../concepts/teaching-philosophy.md)
- [Architecture Overview](../concepts/architecture.md)
- [Creating Custom Validators](custom-validators.md)
- [Configuration Reference](../reference/configuration.md)