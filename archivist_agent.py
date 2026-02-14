#!/usr/bin/env python3
"""
Archivist Agent - Paper Parser & Insight Generator
Handles academic papers, engineering blogs, and research summaries.
Emails insights to both work and personal addresses.
"""

import sys
import os
sys.path.insert(0, '/Users/dansmacmini/.openclaw/workspace')

from email_sender import send_email
import configparser
from datetime import datetime

def parse_paper(url, title_hint=None):
    """
    Placeholder for paper parsing logic.
    In production, this would:
    1. Fetch the content
    2. Generate summary using LLM
    3. Extract key insights
    4. Format for email
    """
    return {
        'title': title_hint or 'Research Paper',
        'summary': 'Summary placeholder',
        'insights': ['Insight 1', 'Insight 2'],
        'url': url
    }

def generate_email_html(paper_info):
    """Generate HTML email template for paper"""
    return f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #2c3e50; color: white; padding: 30px; text-align: center; border-radius: 8px; margin-bottom: 30px; }}
        .section {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        h1 {{ margin: 0; font-size: 24px; }}
        h2 {{ color: #2c3e50; border-bottom: 2px solid #2c3e50; padding-bottom: 10px; }}
        .link-box {{ background: #e3f2fd; padding: 15px; border-left: 4px solid #2196F3; margin: 20px 0; }}
        a {{ color: #2196F3; word-break: break-all; }}
        .meta {{ color: #666; font-size: 14px; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📄 Paper Shared: {paper_info['title']}</h1>
        <div class="meta">Shared by Dan via Archivist Agent | {datetime.now().strftime('%b %d, %Y')}</div>
    </div>

    <div class="section">
        <h2>📝 Summary</h2>
        <p>{paper_info['summary']}</p>
        
        <h2>💡 Key Insights</h2>
        <ul>
            {''.join(f'<li>{insight}</li>' for insight in paper_info['insights'])}
        </ul>
    </div>

    <div class="link-box">
        <strong>🔗 Original Link:</strong><br>
        <a href="{paper_info['url']}">{paper_info['url']}</a>
    </div>

    <div class="section">
        <p style="font-size: 12px; color: #666; text-align: center;">Sent via Archivist Agent 📚</p>
    </div>
</body>
</html>"""

def distribute_paper(url, to_work=False):
    """
    Main entry point for paper distribution.
    
    Args:
        url: The paper/article URL
        to_work: If True, send to both work and personal emails
                If False, send to personal only
    """
    print(f"📚 Archivist: Processing {url}")
    
    # Parse the paper
    paper_info = parse_paper(url)
    
    # Generate email content
    html_content = generate_email_html(paper_info)
    subject = f"Paper: {paper_info['title']}"
    
    # Save to file for email_sender
    temp_file = f"/tmp/paper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(temp_file, 'w') as f:
        f.write(html_content)
    
    # Send emails based on rules
    if to_work:
        # Send to BOTH work and personal
        send_email('dagnachew.birru@quantiphi.com', subject, html_content)
        send_email('dbirru@gmail.com', subject + ' (CC)', html_content)
        print(f"✅ Sent to work + personal emails")
    else:
        # Personal only
        send_email('dbirru@gmail.com', subject, html_content)
        print(f"✅ Sent to personal email only")
    
    # Cleanup
    os.remove(temp_file)
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 archivist_agent.py <URL> [--work]")
        sys.exit(1)
    
    url = sys.argv[1]
    to_work = '--work' in sys.argv
    
    distribute_paper(url, to_work)
