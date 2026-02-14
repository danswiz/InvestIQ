---
name: executive-research
description: Research executives and generate comprehensive prep reports for consulting business development. Use when preparing for meetings, pitches, or engagements with C-suite executives, VPs, directors, or key decision-makers. Triggers on requests like "research executive", "prep report for [name]", "executive briefing", "consulting prep for [person]", or any request to gather intelligence on business leaders before an engagement.
---

# Executive Research & Consulting Prep

Generate comprehensive executive intelligence reports to prepare for consulting engagements, sales meetings, or business development conversations.

## Overview

This skill researches executives across multiple dimensions and produces a structured briefing document that helps you:
- Understand their professional background and career trajectory
- Identify mutual connections and warm introduction paths
- Assess their company's strategic priorities and challenges
- Prepare relevant talking points and value propositions
- Avoid blind spots before important meetings

## When to Use

Use this skill when preparing for:
- Initial consulting sales meetings
- Executive interviews or discovery calls
- Conference networking with target prospects
- Board presentations or pitch meetings
- Partnership discussions with key decision-makers

## Research Dimensions

For each executive, gather information across these categories:

### 1. Professional Background
- Current role, title, and scope of responsibility
- Career trajectory (previous roles, companies, tenure)
- Educational background (schools, degrees, notable programs)
- Board memberships and advisory roles
- Published thought leadership (articles, books, podcasts)

### 2. Company Context
- Company size, industry, and market position
- Recent news and strategic initiatives (12-24 months)
- Financial performance and key metrics
- Leadership team and reporting structure
- Known business challenges or opportunities

### 3. Network & Connections
- LinkedIn mutual connections
- Professional association memberships
- Conference speaking history
- Alumni networks (school, previous employers)

### 4. Personal Insights (if available)
- Social media presence and interests
- Philanthropic activities
- Speaking style and communication preferences
- Recent interviews or public statements

## Output Format

Generate a structured HTML report with these sections:

```html
<h1>Executive Briefing: [Name]</h1>

<h2>Executive Summary</h2>
<p>One-paragraph overview of who they are and why they matter</p>

<h2>Current Role & Responsibilities</h2>
<ul>
  <li>Title, Company</li>
  <li>Scope of role (P&L, headcount, key functions)</li>
  <li>Reports to / Direct reports</li>
</ul>

<h2>Career Trajectory</h2>
<table>
  <tr><th>Period</th><th>Role</th><th>Company</th></tr>
  <!-- Timeline of positions -->
</table>

<h2>Company Context</h2>
<ul>
  <li>Company overview (industry, size, market cap)</li>
  <li>Recent strategic priorities</li>
  <li>Known challenges or pain points</li>
  <li>Competitive landscape</li>
</ul>

<h2>Thought Leadership & Public Presence</h2>
<ul>
  <li>Recent interviews/podcasts</li>
  <li>Published articles or books</li>
  <li>Conference speaking history</li>
  <li>Social media presence</li>
</ul>

<h2>Network & Warm Connections</h2>
<ul>
  <li>Potential mutual connections</li>
  <li>Shared networks (alumni, associations)</li>
  <li>Introduction paths</li>
</ul>

<h2>Consulting Engagement Angles</h2>
<ul>
  <li>Potential value propositions</li>
  <li>Relevant case studies to reference</li>
  <li>Conversation starters</li>
  <li>Questions to ask</li>
</ul>

<h2>Preparation Checklist</h2>
<ul>
  <li>[ ] Review their recent LinkedIn activity</li>
  <li>[ ] Check company's latest earnings call</li>
  <li>[ ] Prepare relevant case study</li>
  <li>[ ] Research mutual connections</li>
</ul>
```

## Research Methodology

1. **Web Search**: Use multiple search queries to gather comprehensive information:
   - `"[Name]" "[Company]" CEO/CTO/VP profile`
   - `"[Name]" LinkedIn`
   - `"[Name]" interview podcast`
   - `"[Company]" strategy 2025 2026`
   - `"[Company]" challenges problems`

2. **Web Fetch**: Extract detailed content from:
   - Company executive team pages
   - LinkedIn profiles (via public view)
   - Press releases and news articles
   - Conference speaker bios
   - Podcast interview transcripts

3. **Synthesize**: Cross-reference information from multiple sources to build a complete picture.

## Usage Workflow

1. User provides executive name and company
2. Research across all dimensions using web tools
3. Generate comprehensive HTML briefing report
4. Save to workspace and optionally email

## Example Queries

- "Research John Smith at Acme Corp for my consulting pitch"
- "Generate a prep report for Sarah Johnson, VP Engineering at TechCo"
- "I have a meeting with the CFO of MegaCorp next week, help me prepare"
- "Create an executive briefing for Jane Doe, Chief Strategy Officer"

## Resources

- See [references/research-sources.md](references/research-sources.md) for recommended research sources and search strategies
- See [assets/report-template.html](assets/report-template.html) for the HTML report template