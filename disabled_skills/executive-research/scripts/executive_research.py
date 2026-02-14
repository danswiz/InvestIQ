#!/usr/bin/env python3
"""
Executive Research Helper Script
Generates search queries and helps structure research for executive briefings.
"""
import sys
import json
from datetime import datetime

def generate_search_queries(name, company, title=""):
    """Generate comprehensive search queries for executive research"""
    queries = []
    
    # Basic profile searches
    queries.extend([
        f'"{name}" "{company}" profile biography',
        f'"{name}" LinkedIn',
        f'"{name}" "{title}" "{company}"' if title else f'"{name}" "{company}" executive',
    ])
    
    # Career history
    queries.extend([
        f'"{name}" previous roles before "{company}"',
        f'"{name}" career history background',
        f'"{name}" former employer',
    ])
    
    # Thought leadership
    queries.extend([
        f'"{name}" interview podcast',
        f'"{name}" speaker conference keynote',
        f'"{name}" article thought leadership',
    ])
    
    # Company context
    queries.extend([
        f'"{company}" strategy 2025 2026',
        f'"{company}" challenges issues',
        f'"{company}" earnings results financial',
        f'"{company}" layoffs restructuring',
        f'"{company}" new product launch initiative',
    ])
    
    # Network research
    queries.extend([
        f'"{name}" board member advisor',
        f'"{name}" mentor angel investor',
    ])
    
    return queries

def generate_report_filename(name, company):
    """Generate standardized report filename"""
    timestamp = datetime.now().strftime("%Y%m%d")
    safe_name = name.lower().replace(" ", "_")
    safe_company = company.lower().replace(" ", "_")
    return f"executive_briefing_{safe_name}_{safe_company}_{timestamp}.html"

def print_research_checklist():
    """Print research checklist for manual completion"""
    checklist = """
EXECUTIVE RESEARCH CHECKLIST
============================

TIER 1 SOURCES (Must Check)
☐ LinkedIn profile (public view)
☐ Company executive team page
☐ Recent press releases from company
☐ Official company biography

TIER 2 SOURCES (Should Check)
☐ Google News search (last 12 months)
☐ Podcast appearances
☐ Conference speaking history
☐ Published articles or interviews
☐ Industry publication mentions

TIER 3 SOURCES (Nice to Have)
☐ Glassdoor company reviews
☐ Employee LinkedIn connections
☐ Alumni networks
☐ Social media presence

COMPANY CONTEXT
☐ Latest earnings call (if public)
☐ Recent strategic announcements
☐ Competitive landscape
☐ Industry trends affecting company

CONSULTING PREP
☐ Identify 2-3 value propositions
☐ Find relevant case studies
☐ Prepare thoughtful questions
☐ Research mutual connections
☐ Check for recent company news
"""
    print(checklist)

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 executive_research.py <name> <company> [title]")
        print("\nExample:")
        print('  python3 executive_research.py "John Smith" "Acme Corp" "VP Engineering"')
        print("\nOr run with no arguments to print research checklist:")
        print("  python3 executive_research.py")
        sys.exit(1)
    
    name = sys.argv[1]
    company = sys.argv[2]
    title = sys.argv[3] if len(sys.argv) > 3 else ""
    
    print(f"\nExecutive Research Plan: {name} at {company}")
    print("=" * 60)
    
    # Generate search queries
    queries = generate_search_queries(name, company, title)
    print("\nSEARCH QUERIES TO RUN:")
    print("-" * 40)
    for i, query in enumerate(queries, 1):
        print(f"{i}. {query}")
    
    # Generate filename
    filename = generate_report_filename(name, company)
    print(f"\n\nSUGGESTED REPORT FILENAME:")
    print("-" * 40)
    print(filename)
    
    # Output as JSON for programmatic use
    output = {
        "name": name,
        "company": company,
        "title": title,
        "search_queries": queries,
        "suggested_filename": filename,
        "generated_at": datetime.now().isoformat()
    }
    
    print(f"\n\nJSON OUTPUT:")
    print("-" * 40)
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print_research_checklist()
    else:
        main()