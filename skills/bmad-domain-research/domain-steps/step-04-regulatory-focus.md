# Domain Research Step 4: Regulatory Focus Analysis

## MANDATORY EXECUTION RULES (READ FIRST):

- 🛑 NEVER generate content without web search verification - regulations change frequently
- 📖 CRITICAL: ALWAYS read the complete step file before taking any action
- 🔄 CRITICAL: When loading next step with 'C', ensure the entire file is read before proceeding
- ✅ FOCUS EXCLUSIVELY on regulatory and compliance analysis
- 🌐 WEB SEARCH MANDATORY - verify all regulatory information against current official sources
- 📝 WRITE CONTENT TO DOCUMENT IMMEDIATELY during generation
- ✅ YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with `{communication_language}`

## EXECUTION PROTOCOLS:

- 🎯 Conduct parallel web searches for applicable regulations, standards, and compliance frameworks
- 📊 Aggregate findings with source citations (prefer official government/standards body sources)
- ⚠️ Present [C] continue option after content generation
- 💾 ONLY proceed to next step when user chooses C
- 📖 Update frontmatter `stepsCompleted: [1, 2, 3, 4]` before loading next step
- 🚫 FORBIDDEN to load next step until C is selected

## CONTEXT BOUNDARIES:

- **Research topic = "{{research_topic}}"**
- **Research goals = "{{research_goals}}"**
- Build on competitive analysis from step 3
- Focus: regulations, compliance frameworks, industry standards, data protection, licensing

## YOUR TASK:

Conduct comprehensive regulatory and compliance analysis for **{{research_topic}}** using current web-verified data.

## REGULATORY ANALYSIS:

### 1. Conduct Web Research

Run parallel web searches to gather current data on:
- Applicable laws and regulations (by jurisdiction if relevant)
- Industry standards and certifications
- Compliance frameworks (ISO, SOC, GDPR, CCPA, sector-specific)
- Data privacy and protection obligations
- Licensing and permitting requirements
- Enforcement bodies and recent enforcement actions
- Upcoming regulatory changes

### 2. Generate Regulatory Analysis Content

Write directly to the research document:

```markdown
## Regulatory Environment: {{research_topic}}

### Regulatory Overview

[Summary of the regulatory landscape - heavily regulated, emerging regulation, self-regulated, etc.]

### Applicable Regulations

| Regulation/Law | Jurisdiction | Key Requirements | Enforcement Body |
|----------------|-------------|-----------------|-----------------|
| [Name]         | [Region]    | [requirements]  | [body]          |

*Sources: [Official government/regulatory URLs]*

### Industry Standards & Certifications

- **[Standard Name]**: [what it covers, who requires it]
- **[Certification]**: [requirements and benefits]

### Data Protection & Privacy Requirements

[GDPR, CCPA, sector-specific data rules applicable to this domain]

### Compliance Frameworks

[ISO standards, SOC requirements, industry-specific frameworks]

### Licensing & Permitting

[Required licenses, permits, or registrations to operate in this space]

### Risk Assessment

| Risk Area | Severity | Likelihood | Mitigation Approach |
|-----------|---------|------------|---------------------|
| [Area]    | High/Med/Low | High/Med/Low | [approach] |

### Upcoming Regulatory Changes

[Known pending regulations or enforcement trends to watch]

**Analysis Date:** {{date}}
```

### 3. Present Continue Option

After writing content to document:

"**Regulatory Analysis Complete.**

I've documented the applicable regulations, compliance requirements, and risk landscape for **{{research_topic}}**.

**Ready to proceed to Technical Trends Analysis?**
[C] Continue - Analyze technology trends"

### 4. Handle Continue Selection

#### If 'C' (Continue):

- Update frontmatter: `stepsCompleted: [1, 2, 3, 4]`
- Load: `./step-05-technical-trends.md`

## SUCCESS METRICS:

✅ Current regulations identified with proper citations
✅ Industry standards and best practices documented
✅ Compliance frameworks clearly mapped
✅ Data protection requirements thoroughly analyzed
✅ Licensing requirements captured
✅ Risk assessment completed
✅ Content written to document immediately
✅ [C] continue option presented after content generation
✅ Proper routing to step-05

## FAILURE MODES:

❌ Citing outdated regulations without web verification
❌ Missing official source citations
❌ Not writing content to document during generation
❌ Omitting data privacy requirements
❌ Not routing to step-05 after user confirmation

❌ **CRITICAL**: Reading only partial step file
❌ **CRITICAL**: Proceeding with 'C' without fully reading the next step file

## NEXT STEP:

After user selects 'C', load `./step-05-technical-trends.md`.
