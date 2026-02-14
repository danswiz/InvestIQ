# Executive Research Skill

## What It Does

This skill researches executives and generates comprehensive prep reports for consulting business development. It helps you prepare for meetings, pitches, or engagements with C-suite executives, VPs, directors, or key decision-makers.

## Installation

1. Copy the `executive-research.skill` file to your OpenClaw skills directory:
   ```bash
   cp executive-research.skill ~/.openclaw/skills/
   ```

2. Or extract to workspace skills:
   ```bash
   unzip executive-research.skill -d ~/.openclaw/workspace/skills/
   ```

3. Restart OpenClaw or reload skills

## How to Use

Simply ask me to research an executive:

- "Research John Smith at Acme Corp for my consulting pitch"
- "Generate a prep report for Sarah Johnson, VP Engineering at TechCo"
- "I have a meeting with the CFO of MegaCorp next week, help me prepare"
- "Create an executive briefing for Jane Doe, Chief Strategy Officer"

## What You'll Get

A comprehensive HTML report including:

✅ **Executive Summary** - One-paragraph overview  
✅ **Current Role & Responsibilities** - Title, scope, reporting structure  
✅ **Career Trajectory** - Timeline of previous roles and companies  
✅ **Educational Background** - Schools, degrees, notable programs  
✅ **Company Context** - Industry, size, recent strategic priorities, challenges  
✅ **Thought Leadership** - Interviews, podcasts, articles, speaking engagements  
✅ **Network & Connections** - Potential warm introduction paths  
✅ **Consulting Engagement Angles** - Value propositions, talking points, questions to ask  
✅ **Preparation Checklist** - Action items before your meeting  

## Research Coverage

The skill researches across:
- LinkedIn profiles and career history
- Company websites and executive bios
- News articles and press releases
- Podcast appearances and interviews
- Conference speaking history
- Thought leadership content
- Industry context and competitive landscape
- Network connections and introduction paths

## Helper Script

The skill includes a Python script for generating search queries:

```bash
python3 skills/executive-research/scripts/executive_research.py "Name" "Company" "Title"
```

This outputs:
- Curated search queries for web research
- Suggested report filename
- JSON output for programmatic use

## Report Format

Reports are generated as professional HTML documents with:
- Clean, readable styling
- Structured sections for easy scanning
- Tables for career timelines
- Highlighted boxes for key insights
- Preparation checkboxes
- Source attribution

## Example Output

See `assets/report-template.html` for the report structure template.

## Files Included

- `SKILL.md` - Main skill instructions and workflow
- `references/research-sources.md` - Research strategies and sources
- `scripts/executive_research.py` - Helper script for search queries
- `assets/report-template.html` - HTML report template

## Requirements

- OpenClaw with web_search and web_fetch tools enabled
- Internet connection for research
- Email capability (optional, for sending reports)

## License

Created for personal consulting business development use.