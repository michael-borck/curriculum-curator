# Module 3: Decision Trees & CART Fundamentals  
## Week 6: Data Analysis Fundamentals | Duration: 15 minutes

### Learning Objectives
After this module, you will be able to:
- [ ] Explain how decision trees split data to make predictions or classifications
- [ ] Understand CART (Classification and Regression Trees) principles conceptually
- [ ] Recognise when decision trees are appropriate for business problems
- [ ] Evaluate the advantages and limitations of tree-based approaches

---

## Section 1: Understanding Decision Trees Conceptually (6 minutes)

### What is a Decision Tree?

A decision tree is an AI technique that mimics human decision-making by asking a series of yes/no questions to reach a conclusion. Think of it as an automated version of the flowcharts managers use to make consistent business decisions.

**Business Analogy:**
Imagine you're CloudCore's customer success manager deciding how to respond to a support ticket:

```
Is the customer's contract value > $50,000?
├─ YES → Is it a technical issue?
│   ├─ YES → Assign to senior technical team (Priority: High)
│   └─ NO → Assign to account manager (Priority: Medium)  
└─ NO → Is it urgent?
    ├─ YES → Assign to standard support (Priority: Medium)
    └─ NO → Assign to junior support (Priority: Low)
```

A decision tree AI system automates this logic, making consistent decisions based on data patterns.

### How Decision Trees Learn from Data

**Step 1: Find the Best Question**
The algorithm examines all possible questions it could ask about the data:
- "Is customer satisfaction > 7.5?"
- "Is monthly usage > 100 hours?"  
- "Is the customer in the Enterprise segment?"

**Step 2: Choose the Most Informative Split**
It selects the question that best separates the data into distinct groups. For example, if asking "Is contract value > $50,000?" creates two groups where:
- High-value customers: 85% renewal rate
- Lower-value customers: 45% renewal rate

This question provides valuable information for predicting renewals.

**Step 3: Repeat for Each Branch**
The process continues for each resulting group, asking new questions until the groups become homogeneous enough to make confident predictions.

### CloudCore Example: Customer Churn Prediction

**Goal**: Predict which customers are likely to cancel their subscriptions

**Training Data**: Historical customer data with known outcomes (renewed/cancelled)

**Possible Decision Tree**:
```
Monthly Usage < 20 hours?
├─ YES → Satisfaction Score < 6?
│   ├─ YES → PREDICT: High Churn Risk (85% likely to cancel)
│   └─ NO → Support Tickets > 5?
│       ├─ YES → PREDICT: Medium Risk (60% likely to cancel)
│       └─ NO → PREDICT: Low Risk (25% likely to cancel)
└─ NO → Contract Value > $100,000?
    ├─ YES → PREDICT: Very Low Risk (5% likely to cancel)
    └─ NO → PREDICT: Low Risk (20% likely to cancel)
```

**Business Value**: This tree gives CloudCore's team clear, actionable rules for identifying at-risk customers and prioritising retention efforts.

---

## Section 2: CART - Classification and Regression Trees (4 minutes)

### What Makes CART Special?

CART is a specific algorithm for building decision trees that can handle both:
- **Classification**: Predicting categories (Will customer churn? Yes/No)
- **Regression**: Predicting numbers (What will customer lifetime value be?)

### The CART Process

**1. Binary Splits Only**
CART always asks yes/no questions, creating exactly two branches at each step. This simplicity makes trees easier to interpret and less prone to overfitting.

**2. Best Split Selection**
For **Classification**: CART chooses splits that create the "purest" groups (e.g., one group is 90% "No Churn", the other is 80% "Churn")

For **Regression**: CART chooses splits that minimise prediction errors (e.g., one group averages $45K lifetime value with low variation, the other averages $120K with low variation)

**3. Stopping Criteria**
CART stops growing the tree when:
- Groups become sufficiently pure
- Further splits don't improve predictions significantly
- Minimum group size is reached (prevents overfitting)

### CloudCore CART Examples

#### Classification Example: Support Ticket Priority
```
Issue affects > 50 users?
├─ YES → CLASSIFY: High Priority
└─ NO → Customer pays > $10K/month?
    ├─ YES → CLASSIFY: Medium Priority  
    └─ NO → CLASSIFY: Low Priority
```

#### Regression Example: Response Time Prediction
```
Ticket category = "Technical"?
├─ YES → Customer tier = "Enterprise"?
│   ├─ YES → PREDICT: 2.5 hours average response
│   └─ NO → PREDICT: 8.5 hours average response
└─ NO → PREDICT: 4.2 hours average response
```

---

## Section 3: When to Choose Decision Trees (3 minutes)

### Decision Trees Excel When:

**✅ Interpretability Matters**
- Managers need to understand and explain decisions
- Regulatory compliance requires transparent reasoning
- Team members need to follow consistent decision rules

**✅ Mixed Data Types**
- Combining numerical data (revenue, usage hours) with categories (region, product type)
- No complex data preprocessing required

**✅ Non-Linear Relationships**
- When relationships aren't straight lines (e.g., high-value customers behave differently than medium-value ones)
- Complex interactions between variables

**✅ Business Rule Generation**
- Creating automated decision processes
- Replacing subjective human judgment with consistent logic

### CloudCore Scenarios Perfect for Decision Trees:

1. **Customer Success Intervention Rules**
   - When should account managers reach out proactively?
   - What type of support should different customer segments receive?

2. **Sales Lead Qualification**
   - Which leads should sales reps prioritise?
   - What engagement strategy fits different prospect types?

3. **Resource Allocation Decisions**
   - How many support staff are needed based on ticket volume and complexity?
   - Which regions deserve increased marketing investment?

### Limitations to Consider:

**⚠️ Overfitting Risk**
- Complex trees may memorise training data rather than learning general patterns
- Solution: Limit tree depth and require minimum group sizes

**⚠️ Instability**
- Small changes in data can create very different trees
- Solution: Use ensemble methods like Random Forest (covered in Week 8)

**⚠️ Bias Toward Simple Splits**
- May miss complex patterns that require multiple variables simultaneously
- Solution: Combine with other techniques or use advanced ensemble methods

---

## Section 4: Advanced Concepts (Optional - For Curious Learners) (2 minutes)

*Note: This section provides additional depth for students wanting to understand more technical aspects, but is not required for workshop success.*

### Information Gain and Gini Impurity

**Information Gain**: Measures how much uncertainty is reduced by asking a particular question
- Higher information gain = better split
- Mathematical basis for CART's split selection

**Gini Impurity**: Measures how "mixed" a group is
- Pure group (all same outcome): Gini = 0
- Completely mixed group: Gini = 0.5
- CART aims to minimise weighted Gini impurity after splits

### Pruning Techniques

**Pre-pruning**: Stop growing the tree early based on criteria like:
- Maximum depth reached
- Minimum samples per leaf
- Minimum improvement threshold

**Post-pruning**: Build full tree, then remove branches that don't improve validation performance
- More computationally expensive but often produces better results

---

## Knowledge Check

**Question 1**: CloudCore wants to create an automated system for routing support tickets to the right team. They have historical data showing which team successfully resolved each type of ticket. Is this classification or regression?

<details>
<summary>Answer</summary>
**Classification.** They're predicting categories (which team: Technical, Billing, Account Management, etc.) based on ticket characteristics.
</details>

**Question 2**: A decision tree for predicting customer lifetime value shows this split: "Monthly usage > 50 hours?" Left branch predicts $75,000, right branch predicts $125,000. What does this tell us about CloudCore's customers?

<details>
<summary>Answer</summary>
High-usage customers (>50 hours/month) tend to have significantly higher lifetime value ($125K vs $75K). This suggests usage intensity is a strong predictor of customer value, which should inform CloudCore's customer success and retention strategies.
</details>

**Question 3**: Why might CloudCore prefer decision trees over more complex AI techniques for customer churn prediction?

<details>
<summary>Answer</summary>
**Interpretability:** Customer success teams can understand and explain why the system flagged specific customers as at-risk, enabling targeted interventions. The tree provides clear business rules that teams can follow and modify as needed.
</details>

---

## Preparing for Module 4: Clustering & NLP Preview

In Module 4, you'll explore two more AI techniques that CloudCore could use:

**Clustering**: Discovering natural customer segments without predefined categories
**NLP**: Analysing customer feedback and support tickets for sentiment and topics

Think about these questions as you prepare for the final module:
- How might clustering help CloudCore understand their customer base differently than classification?
- What insights could CloudCore gain from automatically analysing the text in support tickets and customer feedback?

---

## Module Summary

### Key Takeaways
- **Decision trees** automate human decision-making logic through sequential yes/no questions
- **CART** handles both classification (categories) and regression (numbers) with binary splits
- **Interpretability** is a major advantage - business teams can understand and trust the decisions
- **Best for** mixed data types, business rule generation, and scenarios requiring explanation

### Workshop Preparation
You now understand how decision trees work conceptually and when they're appropriate for business problems. In the workshop, you'll see how these concepts apply to CloudCore's real business scenarios and explore how different techniques complement each other.

---

## Module Completion Checklist

Before moving to Module 4, ensure you:
- [ ] Understand how decision trees ask questions to make predictions
- [ ] Know the difference between classification and regression trees
- [ ] Can identify when decision trees are appropriate for business problems
- [ ] Appreciate both the advantages and limitations of tree-based approaches

---

*Module 3 Complete | Next: Module 4 - Introduction to Clustering & NLP Preview*  
*Estimated completion time: 15 minutes*