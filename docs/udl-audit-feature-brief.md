# UDL Audit Feature Brief

## Background

This brief captures a potential collaboration with Luke Butcher (School of Management and Marketing,
Curtin University) around an iSoLT grant proposal focused on Universal Design for Learning (UDL)
and Assessment 2030 (A2030). Luke has developed a prototype mapping of UDL Guidelines 3.0 to A2030
assessment lanes. The proposal is to explore whether Curriculum Curator can realise his vision as a
working tool, either by extending the existing platform or informing a new purpose-built tool.

**Luke's four goals for the tool:**

1. Make staff more familiar with UDL guidelines and why UDL matters
2. Help staff identify areas in their curriculum where they are already doing UDL well
3. Help staff identify areas in their curriculum where UDL improvement is needed
4. Suggest small, incremental steps forward

The grant would involve Luke (UDL/curriculum expertise), Michael (AI/platform), and Jolyon from
Teaching Support (implementation and UC guidance).

---

## Luke's Prototype Table

Luke has mapped specific A2030 assessment types to UDL 3.0 guidelines with concrete harmful and
helpful practice examples. This is the core data structure to implement.

| Assessment (A2030 Lane) | UDL Principle | UDL Guideline | UDL Checkpoint | Harmful Practice | Helpful Practice |
|---|---|---|---|---|---|
| Lane 1: Interactive Oral (Collaborative) | Action and Expression | Interaction | 4.1 Vary and honor the methods for response, navigation, and movement | Enforce one-size-fits-all classroom positioning; prevent additional presentation time for those with CAPs | Allow students to adjust physical environment (flexible seating, lighting); embed flexibility in means of presentation including digitally (rate, timing, speed) |
| Lane 1: Interactive Oral (Collaborative) | Representation | Language and Symbols | 2.4 Address biases in the use of language and symbols | No consideration of ableist or discriminatory language; not identifying how culture may influence presentation content and delivery | Acknowledge different cultures in the room; recognise students presenting in a second+ language; enable closed captioning |
| Lane 1: Interactive Oral (Collaborative) | Engagement | Sustaining Effort and Persistence | 8.3 Foster collaboration, interdependence, and collective learning | Failure to address how students can ask for help; ignoring socially shared regulation of learning | Establish group agreements; identify team roles and collaborative learning goals; intentionally develop communities of learning |
| Lane 2: Field Journal with Media Analysis | Representation | Building Knowledge | 3.3 Cultivate multiple ways of knowing and making meaning | Implying (not explicit) effective sequences; ignoring holistic and interconnected indigenous knowledge systems | Progressive disclosure of chunked information; support diversity of cognitive approaches to enhance comprehension |
| Lane 2: Field Journal with Media Analysis | Action and Expression | Expression and Communication | 5.2 Use multiple tools for construction, composition, and creativity | Preventing students from using emerging/innovative tools; failing to teach foundational principles that transfer across tools | Enable diversity of analytical and reflective tools; develop competencies for responsible Gen-AI use; evaluate students' critique of tools |
| Lane 2: Field Journal with Media Analysis | Engagement | Welcoming Interests and Identities | 7.3 Nurture joy and play | Preventing time for imagination, experimentation, and wonder; limiting broad sensory and temporal engagement | Foster a mindset of playfulness; require experimentation across physical and digital spaces; incorporate diverse artistic experiences (music, film, visual, AI-generated) |

Source: Luke Butcher prototype document (provided as Just_table.docx).
Full UDL Guidelines 3.0: https://udlguidelines.cast.org/

---

## Mapping to Existing Curriculum Curator Features

Curriculum Curator already covers significant ground:

| Luke's vision | Existing capability |
|---|---|
| UDL audit against guidelines | UDL cheatsheet already in app (location TBC - check data/ or frontend) |
| Whole-of-curriculum scope | Multi-scale workflows: 12-week units, modules, individual materials |
| Accreditation alignment | Curtin GC1-GC6 and AACSB AoL mapping already built |
| AI-assisted improvement suggestions | AI enhancement and content generation (LiteLLM, Ollama, Anthropic, OpenAI) |
| Identify gaps and suggest steps | Plugin system for validators and remediators (planned, not yet built) |
| Privacy-first / local deployment | Ollama backend, Docker, locally deployable |

---

## Suggested Implementation Directions

### 1. Extend the UDL cheatsheet data

The existing UDL cheatsheet should be extended (or replaced) with Luke's structured data model:

```
Assessment type (A2030 lane)
  UDL Principle (Engagement / Representation / Action and Expression)
    UDL Guideline (e.g. Interaction, Language and Symbols)
      Checkpoint (e.g. 4.1)
        Harmful practices (list)
        Helpful practices (list)
```

This could live as a JSON or YAML file in `data/` and be loaded by the backend.

### 2. UDL Audit workflow (new feature)

A new workflow that walks a staff member through their unit/assessment and:

- Asks which A2030 assessment lane applies
- Surfaces the relevant UDL checkpoints
- Asks the user to self-assess (doing well / needs work / not applicable)
- Generates a summary report with the helpful practice suggestions for identified gaps

This maps naturally to the existing plugin validator architecture.

### 3. AI-assisted UDL suggestions

Use the existing LLM service to generate contextualised suggestions. Given:
- The unit description / learning outcomes
- The assessment type
- The identified UDL gaps

...ask the LLM to suggest specific, incremental improvements grounded in the helpful practices list.

### 4. UDL alignment view

A dashboard view showing a unit's UDL coverage across the three principles (Engagement,
Representation, Action and Expression), similar to the existing Learning Outcome Hierarchy view.

---

## Data File to Add

Save Luke's original prototype as:

```
data/udl-a2030-mapping.json   (structured version of the table above)
docs/udl-a2030-prototype.docx (Luke's original file for reference)
```

---

## Effort Estimate

Rough estimate for a working prototype sufficient to demonstrate to Luke:

- Extend UDL data structure: 0.5 days
- UDL audit workflow (basic, no AI): 1 day
- AI-assisted suggestions integration: 1 day
- Basic coverage dashboard: 0.5 days

**Total: ~3 days for a demonstrable prototype**

---

## Context Links

- Luke's email proposing the collaboration: kept in Michael's email
- UDL Guidelines 3.0: https://udlguidelines.cast.org/
- iSoLT grant: Curtin internal grant, call expected end of 2026
- Collaborators: Luke Butcher (UDL), Jolyon (Teaching Support)
- Related: FLX project (Faculty of Business and Law digital transformation) - discuss in person
