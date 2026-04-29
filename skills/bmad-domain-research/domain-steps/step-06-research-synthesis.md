# Domain Research Step 6: Research Synthesis & Completion

## MANDATORY EXECUTION RULES (READ FIRST):

- 🛑 NEVER finalize without web-verifying any claims that may have changed since earlier steps
- 📖 CRITICAL: ALWAYS read the complete step file before taking any action
- ✅ FOCUS EXCLUSIVELY on synthesizing all previous research into a coherent final document
- 🌐 WEB SEARCH as needed to validate and fill gaps before final synthesis
- 📝 WRITE SYNTHESIZED CONTENT TO DOCUMENT
- ✅ YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with `{communication_language}`

## EXECUTION PROTOCOLS:

- 🎯 Review all previously appended content from steps 1-5
- 📊 Synthesize cross-cutting themes and strategic insights
- ⚠️ Present [C] Complete option after synthesis
- 💾 Execute `workflow.on_complete` upon user selecting [C] Complete
- 📖 Update frontmatter `stepsCompleted: [1, 2, 3, 4, 5, 6]`
- 🚫 FORBIDDEN to mark complete until C is selected

## CONTEXT BOUNDARIES:

- **Research topic = "{{research_topic}}"**
- **Research goals = "{{research_goals}}"**
- All previous steps completed - synthesize into final authoritative document
- This is the terminal step of the domain research workflow

## YOUR TASK:

Synthesize all domain research findings into a comprehensive, professionally-structured final report for **{{research_topic}}**.

## RESEARCH SYNTHESIS:

### 1. Review All Research Content

Review all content appended from steps 1-5:
- Industry analysis (market size, segmentation, trends)
- Competitive landscape (key players, dynamics, barriers)
- Regulatory environment (regulations, standards, compliance)
- Technical trends (emerging tech, digital transformation, future outlook)

Identify cross-cutting themes, contradictions, and gaps requiring additional web verification.

### 2. Generate Synthesis Content

Write directly to the research document:

```markdown
## Executive Summary

### Key Findings

**{{research_topic}}** research reveals:

1. **Market Opportunity**: [synthesized market insight]
2. **Competitive Dynamics**: [synthesized competitive insight]
3. **Regulatory Context**: [synthesized regulatory insight]
4. **Technology Trajectory**: [synthesized technology insight]

### Strategic Implications

[3-5 high-impact strategic implications drawn from cross-cutting analysis]

### Critical Risks

[Top 3 risks identified across all research dimensions]

---

## Strategic Recommendations

### Immediate Actions (0-6 months)

1. [Recommendation 1 - grounded in research]
2. [Recommendation 2]
3. [Recommendation 3]

### Medium-Term Priorities (6-18 months)

1. [Recommendation 1]
2. [Recommendation 2]

### Long-Term Strategic Considerations

1. [Consideration 1]
2. [Consideration 2]

---

## Research Methodology

**Research Type:** Domain Research
**Research Topic:** {{research_topic}}
**Research Goals:** {{research_goals}}
**Date Completed:** {{date}}
**Researcher:** {{user_name}}

**Sources Consulted:** [aggregate source count from all steps]

**Methodology:**
- Web-verified facts from current public sources
- Multi-source validation for critical claims
- Six-phase structured research pipeline (scope → industry → competitive → regulatory → technical → synthesis)

---

## Appendices

### Appendix A: Source Index

[Consolidated list of all sources cited across all research sections]

### Appendix B: Glossary

[Domain-specific terms and definitions]

### Appendix C: Research Limitations

[Gaps, caveats, and areas where additional research is recommended]
```

### 3. Present Completion Option

After writing synthesis to document:

"**Research Synthesis Complete.**

The comprehensive domain research report for **{{research_topic}}** is now finalized, covering:

✅ Industry Analysis
✅ Competitive Landscape
✅ Regulatory Environment
✅ Technical Trends
✅ Executive Summary & Strategic Recommendations

**Select [C] to complete and save the research.**
[C] Complete Research"

### 4. Handle Completion

#### If 'C' (Complete):

- Update frontmatter: `stepsCompleted: [1, 2, 3, 4, 5, 6]`
- Update frontmatter: `lastStep: 6`
- Execute `{workflow.on_complete}` if configured
- Confirm to user: "Domain research for **{{research_topic}}** is complete. Your research document has been saved."

## SUCCESS METRICS:

✅ Compelling executive summary with key findings
✅ Comprehensive strategic recommendations grounded in research
✅ Cross-cutting themes synthesized across all research dimensions
✅ Complete methodology documentation
✅ Source index consolidated
✅ Research limitations acknowledged
✅ [C] Complete option presented
✅ Frontmatter updated to reflect completion
✅ on_complete hook executed if configured

## FAILURE MODES:

❌ Executive summary that merely restates section content without synthesis
❌ Recommendations not grounded in specific research findings
❌ Missing source index
❌ Not executing on_complete hook
❌ Not updating frontmatter to stepsCompleted: [1,2,3,4,5,6]

❌ **CRITICAL**: Reading only partial step file
❌ **CRITICAL**: Marking complete without user selecting [C]

## COMPLETION:

This is the terminal step. After user selects [C], the domain research workflow is complete.
