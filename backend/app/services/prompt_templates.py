"""
Prompt template management system for LLM generation
"""

import json
from typing import Any

from jinja2 import Environment, meta


class PromptTemplate:
    """Base class for prompt templates with variable substitution"""

    def __init__(
        self, template: str, description: str = "", variables: list[str] | None = None
    ):
        """
        Initialize a prompt template

        Args:
            template: Jinja2 template string
            description: Human-readable description of the template
            variables: List of expected variables (for validation)
        """
        self.template = template
        self.description = description
        self.env = Environment()
        self.compiled = self.env.from_string(template)

        # Extract variables from template if not provided
        if variables is None:
            ast = self.env.parse(template)
            self.variables = list(meta.find_undeclared_variables(ast))
        else:
            self.variables = variables

    def render(self, **kwargs) -> str:
        """Render the template with provided variables"""
        # Check for missing required variables
        missing = set(self.variables) - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing required template variables: {missing}")

        return self.compiled.render(**kwargs)

    def preview(self, sample_data: dict[str, Any] | None = None) -> str:
        """Preview the template with sample data"""
        if sample_data is None:
            sample_data = {var: f"<{var}>" for var in self.variables}
        return self.render(**sample_data)


class PromptTemplateLibrary:
    """Library of reusable prompt templates"""

    @staticmethod
    def unit_structure_generation() -> PromptTemplate:
        """Template for generating unit structure from wizard decisions"""
        template = """You are an expert curriculum designer specializing in {{ pedagogy_approach }} learning approaches.

Create a comprehensive unit structure for the following course:

## Unit Information
- **Name**: {{ unit_name }}
- **Code**: {{ unit_code }}
- **Duration**: {{ duration_weeks }} weeks
- **Student Level**: {{ student_level }}
- **Delivery Mode**: {{ delivery_mode }}
- **Unit Type**: {{ unit_type }}

## Pedagogical Context
- **Teaching Approach**: {{ pedagogy_approach }}
- **Weekly Structure**: {{ weekly_structure }}
- **Assessment Strategy**: {{ assessment_strategy }} ({{ assessment_count }} assessments)
- **Include Formative Assessment**: {{ include_formative }}
- **Learning Outcome Focus**: {{ outcome_focus }}
- **Number of Learning Outcomes**: {{ num_learning_outcomes }}

## Instructions
Generate a detailed unit structure following these guidelines:

1. **Learning Outcomes** ({{ num_learning_outcomes }}):
   - Write clear, measurable learning outcome statements
   - Use action verbs aligned with Bloom's taxonomy
   - Focus on {{ outcome_focus }}
   - Ensure outcomes are achievable within {{ duration_weeks }} weeks

2. **Weekly Topics**:
   {% if pedagogy_approach == 'flipped' %}
   - For each week, create 2-4 bite-sized pre-class modules (15-30 minutes each)
   - Include videos, readings, and self-check activities
   {% elif pedagogy_approach == 'traditional' %}
   - For each week, create one comprehensive topic
   - Structure for {{ weekly_structure }}
   {% elif pedagogy_approach == 'project-based' %}
   - Organize topics around project milestones
   - Include project work sessions and check-ins
   {% endif %}
   - Week 1 should be introduction/orientation
   - Week {{ duration_weeks }} should include review/consolidation

3. **Assessments**:
   - Design {{ assessment_count }} assessments following {{ assessment_strategy }} strategy
   - Ensure weights sum to 100%
   - Distribute due dates appropriately across the semester
   {% if include_formative %}
   - Include regular formative (ungraded) assessments for student feedback
   {% endif %}

## Output Format
You must respond with valid JSON matching this exact schema:
{{ json_schema }}

Ensure all fields are properly filled with relevant, pedagogically-sound content."""

        return PromptTemplate(
            template=template,
            description="Generate complete unit structure from wizard decisions",
            variables=[
                "unit_name",
                "unit_code",
                "duration_weeks",
                "student_level",
                "delivery_mode",
                "unit_type",
                "pedagogy_approach",
                "weekly_structure",
                "assessment_strategy",
                "assessment_count",
                "include_formative",
                "outcome_focus",
                "num_learning_outcomes",
                "json_schema",
            ],
        )

    @staticmethod
    def learning_outcomes_refinement() -> PromptTemplate:
        """Template for refining learning outcomes"""
        template = """As an expert in curriculum design and Bloom's taxonomy, refine these learning outcomes:

## Current Learning Outcomes
{% for outcome in current_outcomes %}
{{ loop.index }}. {{ outcome }}
{% endfor %}

## Context
- **Unit**: {{ unit_name }}
- **Level**: {{ student_level }}
- **Focus**: {{ outcome_focus }}

## Requirements
1. Ensure each outcome starts with a measurable action verb
2. Align with appropriate Bloom's taxonomy level for {{ student_level }}
3. Make outcomes specific, measurable, achievable, relevant, and time-bound (SMART)
4. Ensure progression from lower to higher-order thinking skills

## Action Verb Guide by Bloom's Level
- **Remember**: define, list, identify, name, recall
- **Understand**: explain, describe, summarize, interpret, classify
- **Apply**: demonstrate, implement, solve, use, execute
- **Analyze**: compare, contrast, examine, differentiate, organize
- **Evaluate**: assess, critique, justify, defend, appraise
- **Create**: design, construct, develop, formulate, produce

Provide refined learning outcomes with clear action verbs and measurable criteria."""

        return PromptTemplate(
            template=template,
            description="Refine and improve learning outcomes",
            variables=[
                "current_outcomes",
                "unit_name",
                "student_level",
                "outcome_focus",
            ],
        )

    @staticmethod
    def lecture_content_generation() -> PromptTemplate:
        """Template for generating lecture content"""
        template = """You are an expert educator creating a {{ duration_minutes }}-minute lecture using {{ pedagogy }} approach.

## Lecture Topic
{{ topic }}

## Learning Outcomes to Address
{% for outcome in learning_outcomes %}
- {{ outcome }}
{% endfor %}

## Student Level
{{ student_level }}

## Requirements
1. Create engaging content appropriate for {{ student_level }} students
2. Follow {{ pedagogy }} pedagogical principles
{% if include_activities %}
3. Include interactive activities every 10-15 minutes
{% endif %}
{% if include_examples %}
4. Provide relevant, real-world examples
{% endif %}
5. Structure content for a {{ duration_minutes }}-minute session

## {{ pedagogy }} Approach Guidelines
{% if pedagogy == 'traditional' %}
- Clear introduction, body, and conclusion
- Direct instruction with structured explanations
- Practice problems with guided solutions
{% elif pedagogy == 'flipped' %}
- Focus on application and problem-solving
- Assume students have completed pre-class materials
- Emphasize collaborative activities
{% elif pedagogy == 'problem-based' %}
- Start with a compelling problem or scenario
- Guide students through problem-solving process
- Connect theory to practical application
{% endif %}

Generate comprehensive lecture content with clear sections, timing, and activities."""

        return PromptTemplate(
            template=template,
            description="Generate lecture content based on pedagogy and outcomes",
            variables=[
                "topic",
                "duration_minutes",
                "learning_outcomes",
                "pedagogy",
                "include_activities",
                "include_examples",
                "student_level",
            ],
        )

    @staticmethod
    def quiz_generation() -> PromptTemplate:
        """Template for generating quiz questions"""
        template = """Create {{ num_questions }} quiz questions on "{{ topic }}" for {{ student_level }} students.

## Learning Outcomes to Assess
{% for outcome in learning_outcomes %}
- {{ outcome }}
{% endfor %}

## Question Requirements
- **Bloom's Levels**: {{ bloom_levels | join(', ') }}
- **Question Types**: {{ question_types | join(', ') }}
- **Difficulty**: {{ difficulty }}

## Question Distribution Guidelines
1. Align questions with specified Bloom's taxonomy levels
2. For multiple choice: provide 4 options with plausible distractors
3. Include clear, unambiguous wording
4. Avoid negative phrasing unless essential
5. Provide explanations for correct answers

## Output Format
Generate questions in JSON format with:
- Question text
- Type (multiple_choice, true_false, short_answer)
- Options (for multiple choice)
- Correct answer
- Explanation
- Bloom's level
- Points value

Ensure questions progressively assess understanding from basic recall to higher-order thinking."""

        return PromptTemplate(
            template=template,
            description="Generate quiz questions aligned with learning outcomes",
            variables=[
                "topic",
                "num_questions",
                "learning_outcomes",
                "bloom_levels",
                "question_types",
                "difficulty",
                "student_level",
            ],
        )

    @staticmethod
    def assessment_rubric_generation() -> PromptTemplate:
        """Template for generating assessment rubrics"""
        template = """Create a detailed rubric for the following assessment:

## Assessment Details
- **Name**: {{ assessment_name }}
- **Type**: {{ assessment_type }}
- **Weight**: {{ weight }}%
- **Unit**: {{ unit_name }}

## Learning Outcomes to Assess
{% for outcome in learning_outcomes %}
- {{ outcome }}
{% endfor %}

## Rubric Requirements
1. Create 4-5 assessment criteria aligned with learning outcomes
2. Define 4 performance levels: Excellent, Good, Satisfactory, Needs Improvement
3. Provide specific, observable descriptors for each level
4. Include point values or percentages
5. Ensure criteria are measurable and objective

## Structure
For each criterion:
- Name and description
- Weight (percentage of total)
- Performance level descriptors
- Common mistakes to avoid
- Feedback suggestions

Generate a comprehensive rubric that promotes fair, consistent grading."""

        return PromptTemplate(
            template=template,
            description="Generate detailed assessment rubrics",
            variables=[
                "assessment_name",
                "assessment_type",
                "weight",
                "unit_name",
                "learning_outcomes",
            ],
        )

    @staticmethod
    def case_study_generation() -> PromptTemplate:
        """Template for generating case studies"""
        template = """Develop a case study for {{ unit_name }} that demonstrates real-world application.

## Topic Focus
{{ topic }}

## Learning Outcomes to Address
{% for outcome in learning_outcomes %}
- {{ outcome }}
{% endfor %}

## Context
- **Student Level**: {{ student_level }}
- **Industry/Field**: {{ industry }}
- **Complexity**: {{ complexity }}

## Case Study Requirements
1. **Scenario**: Create a realistic, engaging scenario
2. **Background**: Provide necessary context and data
3. **Challenge**: Present a problem requiring analysis and decision-making
4. **Questions**: Develop 5-7 thought-provoking questions
5. **Resources**: Include relevant data, charts, or supplementary materials

## Question Types to Include
- Comprehension questions (understanding the situation)
- Analysis questions (identifying key issues)
- Application questions (proposing solutions)
- Evaluation questions (assessing alternatives)
- Synthesis questions (integrating concepts)

Generate a complete case study with teaching notes and suggested solutions."""

        return PromptTemplate(
            template=template,
            description="Generate case studies for problem-based learning",
            variables=[
                "unit_name",
                "topic",
                "learning_outcomes",
                "student_level",
                "industry",
                "complexity",
            ],
        )


# Utility functions
def get_template(template_name: str) -> PromptTemplate:
    """Get a template by name from the library"""
    library = PromptTemplateLibrary()
    template_map = {
        "unit_structure": library.unit_structure_generation,
        "learning_outcomes": library.learning_outcomes_refinement,
        "lecture": library.lecture_content_generation,
        "quiz": library.quiz_generation,
        "rubric": library.assessment_rubric_generation,
        "case_study": library.case_study_generation,
    }

    if template_name not in template_map:
        raise ValueError(
            f"Template '{template_name}' not found. Available: {list(template_map.keys())}"
        )

    return template_map[template_name]()


def prepare_unit_structure_prompt(context: dict[str, Any], json_schema: dict) -> str:
    """
    Prepare a complete prompt for unit structure generation

    Args:
        context: Context dictionary from wizard decisions
        json_schema: JSON schema for expected output structure

    Returns:
        Rendered prompt ready for LLM
    """
    template = PromptTemplateLibrary.unit_structure_generation()

    # Add JSON schema as formatted string
    context["json_schema"] = json.dumps(json_schema, indent=2)

    return template.render(**context)
