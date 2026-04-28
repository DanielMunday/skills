# Domain Research Step 5: Technical Trends Analysis

## MANDATORY EXECUTION RULES (READ FIRST):

- 🛑 NEVER generate content without web search verification - technology evolves rapidly
- 📖 CRITICAL: ALWAYS read the complete step file before taking any action
- 🔄 CRITICAL: When loading next step with 'C', ensure the entire file is read before proceeding
- ✅ FOCUS EXCLUSIVELY on emerging technologies and innovation patterns
- 🌐 WEB SEARCH MANDATORY - verify all technology trends against current sources
- 📝 WRITE CONTENT TO DOCUMENT IMMEDIATELY during generation
- ✅ YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with `{communication_language}`

## EXECUTION PROTOCOLS:

- 🎯 Conduct parallel web searches for AI/automation adoption, digital transformation, and future outlook
- 📊 Aggregate findings with source citations
- ⚠️ Present [C] continue option after content generation
- 💾 ONLY proceed to next step when user chooses C
- 📖 Update frontmatter `stepsCompleted: [1, 2, 3, 4, 5]` before loading next step
- 🚫 FORBIDDEN to load next step until C is selected

## CONTEXT BOUNDARIES:

- **Research topic = "{{research_topic}}"**
- **Research goals = "{{research_goals}}"**
- Build on regulatory analysis from step 4
- Focus: emerging technologies, digital transformation, innovation roadmaps, future projections

## YOUR TASK:

Conduct comprehensive technical trends analysis for **{{research_topic}}** using current web-verified data.

## TECHNICAL TRENDS ANALYSIS:

### 1. Conduct Web Research

Run parallel web searches to gather current data on:
- Emerging technologies impacting the domain (AI, automation, IoT, etc.)
- Current technology adoption rates and maturity levels
- Digital transformation initiatives by leading players
- R&D investment trends
- Technology-driven business model changes
- Future outlook and analyst projections (3-5 year horizon)
- Key innovation hubs and research centers

### 2. Generate Technical Trends Content

Write directly to the research document:

```markdown
## Technical Trends: {{research_topic}}

### Technology Landscape Overview

[Summary of how technology is reshaping this domain]

### Emerging Technologies

| Technology | Maturity Level | Adoption Rate | Impact Potential |
|-----------|---------------|--------------|-----------------|
| [Tech]    | Early/Growing/Mature | Low/Med/High | Transformative/Incremental |

*Sources: [URLs]*

### AI & Automation Impact

[How AI, ML, and automation are specifically affecting this domain - with current examples]

### Digital Transformation Trends

1. **[Trend 1]**: [description and evidence]
2. **[Trend 2]**: [description and evidence]
3. **[Trend 3]**: [description and evidence]

### R&D Investment Patterns

[Where companies and governments are investing in technology for this domain]

### Future Outlook (3-5 Year Horizon)

- **Short-term (1-2 years)**: [expected developments]
- **Medium-term (3-5 years)**: [projected changes]
- **Wild cards**: [disruptive possibilities]

### Implementation Opportunities & Challenges

**Opportunities:**
- [Opportunity 1]
- [Opportunity 2]

**Challenges:**
- [Challenge 1]
- [Challenge 2]

### Strategic Technology Recommendations

[Actionable guidance for technology adoption in this domain]

**Analysis Date:** {{date}}
```

### 3. Present Continue Option

After writing content to document:

"**Technical Trends Analysis Complete.**

I've documented emerging technologies, digital transformation patterns, and future outlook for **{{research_topic}}**.

**Ready to synthesize all research into the final report?**
[C] Continue - Synthesize research findings"

### 4. Handle Continue Selection

#### If 'C' (Continue):

- Update frontmatter: `stepsCompleted: [1, 2, 3, 4, 5]`
- Load: `./step-06-research-synthesis.md`

## SUCCESS METRICS:

✅ Emerging technologies identified with current data verification
✅ Digital transformation trends clearly documented with sources
✅ AI/automation impact specifically addressed
✅ Future outlook and projections analyzed
✅ Implementation opportunities and challenges mapped
✅ Strategic recommendations provided
✅ Content written to document immediately
✅ [C] continue option presented after content generation
✅ Proper routing to step-06

## FAILURE MODES:

❌ Citing outdated technology trends without verification
❌ Missing source citations
❌ Not writing content to document during generation
❌ Vague future projections without evidence base
❌ Not routing to step-06 after user confirmation

❌ **CRITICAL**: Reading only partial step file
❌ **CRITICAL**: Proceeding with 'C' without fully reading the next step file

## NEXT STEP:

After user selects 'C', load `./step-06-research-synthesis.md`.

This is the final data collection phase — step 6 synthesizes all findings into the complete research document.
