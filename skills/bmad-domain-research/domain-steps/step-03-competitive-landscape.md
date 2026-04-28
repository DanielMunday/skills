# Domain Research Step 3: Competitive Landscape Analysis

## MANDATORY EXECUTION RULES (READ FIRST):

- 🛑 NEVER generate content without web search verification - do NOT rely solely on training data
- 📖 CRITICAL: ALWAYS read the complete step file before taking any action
- 🔄 CRITICAL: When loading next step with 'C', ensure the entire file is read before proceeding
- ✅ FOCUS EXCLUSIVELY on competitive landscape analysis
- 🌐 WEB SEARCH MANDATORY - verify all competitive data against current public sources
- 📝 WRITE CONTENT TO DOCUMENT IMMEDIATELY during generation
- ✅ YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with `{communication_language}`

## EXECUTION PROTOCOLS:

- 🎯 Conduct parallel web searches for major players, market share, and competitive positioning
- 📊 Aggregate findings with source citations
- ⚠️ Present [C] continue option after content generation
- 💾 ONLY proceed to next step when user chooses C
- 📖 Update frontmatter `stepsCompleted: [1, 2, 3]` before loading next step
- 🚫 FORBIDDEN to load next step until C is selected

## CONTEXT BOUNDARIES:

- **Research topic = "{{research_topic}}"**
- **Research goals = "{{research_goals}}"**
- Build on industry analysis from step 2
- Focus: key players, market share, competitive strategies, barriers to entry

## YOUR TASK:

Conduct comprehensive competitive landscape analysis for **{{research_topic}}** using current web-verified data.

## COMPETITIVE LANDSCAPE ANALYSIS:

### 1. Conduct Web Research

Run parallel web searches to gather current data on:
- Major market players and their market share
- Key competitive differentiators
- Recent M&A activity and partnerships
- Barriers to entry and competitive moats
- Emerging challengers and disruptors
- Competitive strategies (pricing, product, distribution)

### 2. Generate Competitive Landscape Content

Write directly to the research document:

```markdown
## Competitive Landscape: {{research_topic}}

### Market Structure

[Description of market concentration - fragmented/consolidated, number of players]

### Key Players

| Company | Market Share | Key Strengths | Notable Products/Services |
|---------|-------------|---------------|--------------------------|
| [Name]  | [%]         | [strengths]   | [products]               |

*Sources: [URLs]*

### Competitive Dynamics

#### Market Leaders
[Analysis of top 2-3 players with strategic positioning]

#### Emerging Challengers
[New entrants and disruptors worth watching]

#### Competitive Strategies
- **Pricing**: [dominant pricing approaches]
- **Differentiation**: [how players differentiate]
- **Distribution**: [key channels and go-to-market approaches]

### Barriers to Entry

1. [Barrier 1 - capital, regulation, technology, etc.]
2. [Barrier 2]
3. [Barrier 3]

### Recent M&A & Partnerships

[Notable recent activity shaping competitive dynamics]

**Analysis Date:** {{date}}
```

### 3. Present Continue Option

After writing content to document:

"**Competitive Landscape Analysis Complete.**

I've documented the key players, market dynamics, and competitive strategies for **{{research_topic}}**.

**Ready to proceed to Regulatory Focus Analysis?**
[C] Continue - Analyze regulatory environment"

### 4. Handle Continue Selection

#### If 'C' (Continue):

- Update frontmatter: `stepsCompleted: [1, 2, 3]`
- Load: `./step-04-regulatory-focus.md`

## SUCCESS METRICS:

✅ Major players identified with verified market share data
✅ Competitive strategies clearly documented
✅ Barriers to entry analyzed
✅ Emerging challengers identified
✅ Recent M&A activity captured
✅ Content written to document immediately
✅ [C] continue option presented after content generation
✅ Proper routing to step-04

## FAILURE MODES:

❌ Relying on training data without web verification
❌ Missing source citations for competitive data
❌ Not writing content to document during generation
❌ Not routing to step-04 after user confirmation

❌ **CRITICAL**: Reading only partial step file
❌ **CRITICAL**: Proceeding with 'C' without fully reading the next step file

## NEXT STEP:

After user selects 'C', load `./step-04-regulatory-focus.md`.
