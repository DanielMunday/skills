# Domain Research Step 2: Industry Analysis

## MANDATORY EXECUTION RULES (READ FIRST):

- 🛑 NEVER generate content without web search verification - do NOT rely solely on training data
- 📖 CRITICAL: ALWAYS read the complete step file before taking any action
- 🔄 CRITICAL: When loading next step with 'C', ensure the entire file is read before proceeding
- ✅ FOCUS EXCLUSIVELY on industry/market analysis
- 🌐 WEB SEARCH MANDATORY - verify all market facts against current public sources
- 📝 WRITE CONTENT TO DOCUMENT IMMEDIATELY during generation, not after user confirmation
- ✅ YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with `{communication_language}`

## EXECUTION PROTOCOLS:

- 🎯 Conduct parallel web searches across market valuation, growth, segmentation, and trends
- 📊 Aggregate findings with source citations
- ⚠️ Present [C] continue option after content generation
- 💾 ONLY proceed to next step when user chooses C (Continue)
- 📖 Update frontmatter `stepsCompleted: [1, 2]` before loading next step
- 🚫 FORBIDDEN to load next step until C is selected

## CONTEXT BOUNDARIES:

- **Research topic = "{{research_topic}}"**
- **Research goals = "{{research_goals}}"**
- Conduct web-verified industry/market analysis
- Focus: market size, growth rates, segmentation, trends, and competitive dynamics

## YOUR TASK:

Conduct comprehensive industry analysis for **{{research_topic}}** using current web-verified data.

## INDUSTRY ANALYSIS:

### 1. Conduct Web Research

Run parallel web searches to gather current data on:
- Market size and valuation (current year)
- Market growth rate and CAGR projections
- Market segmentation (by product, region, end-user, etc.)
- Key market trends and drivers
- Industry evolution and historical context
- Major players and market share

### 2. Generate Industry Analysis Content

Write directly to the research document:

```markdown
## Industry Analysis: {{research_topic}}

### Market Overview

[Market size, valuation, and overall description - web verified]
*Source: [URL]*

### Market Size & Growth

- **Current Market Size**: [value and year]
- **Projected Size**: [value and year]
- **CAGR**: [percentage and period]

*Sources: [URLs]*

### Market Segmentation

[Key segments with descriptions and relative sizes]

### Industry Trends & Drivers

1. [Trend 1 - with evidence]
2. [Trend 2 - with evidence]
3. [Trend 3 - with evidence]

### Competitive Dynamics

[Overview of competitive landscape, number of players, concentration]

**Analysis Date:** {{date}}
```

### 3. Present Continue Option

After writing content to document:

"**Industry Analysis Complete.**

I've documented the market overview, size, segmentation, and key trends for **{{research_topic}}**.

**Ready to proceed to Competitive Landscape Analysis?**
[C] Continue - Analyze competitive landscape"

### 4. Handle Continue Selection

#### If 'C' (Continue):

- Update frontmatter: `stepsCompleted: [1, 2]`
- Load: `./step-03-competitive-landscape.md`

## SUCCESS METRICS:

✅ Market size verified with current web sources
✅ Growth rates and projections documented with citations
✅ Market segmentation clearly mapped
✅ Industry trends identified and explained
✅ Competitive dynamics overview provided
✅ Content written to document immediately
✅ [C] continue option presented after content generation
✅ Proper routing to step-03

## FAILURE MODES:

❌ Relying on training data without web verification
❌ Missing source citations for market data
❌ Not writing content to document during generation
❌ Presenting [C] before content is fully written
❌ Not routing to step-03 after user confirmation

❌ **CRITICAL**: Reading only partial step file
❌ **CRITICAL**: Proceeding with 'C' without fully reading the next step file

## NEXT STEP:

After user selects 'C', load `./step-03-competitive-landscape.md`.
