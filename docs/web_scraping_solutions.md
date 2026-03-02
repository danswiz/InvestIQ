# Web Scraping Solutions for Commercial Real Estate

## Problem Summary
LoopNet, Crexi, CoStar, and major commercial real estate sites block automated access via:
- Bot detection/fingerprinting
- CAPTCHA challenges
- IP blocking/rate limiting
- JavaScript challenges
- Login walls

---

## SOLUTION 1: Third-Party Scraping APIs (EASIEST - RECOMMENDED)

### Services that handle anti-bot protection:

**1. ScrapingBee** (https://www.scrapingbee.com)
- Cost: $49/month (10,000 API credits) to $599/month (2.5M credits)
- Handles JavaScript rendering, proxies, CAPTCHAs automatically
- Python/Node.js SDK available
- **Best for:** Quick implementation, reliable results

```python
import requests

def scrape_with_scrapingbee(url, api_key):
    response = requests.get(
        "https://app.scrapingbee.com/api/v1/",
        params={
            "api_key": api_key,
            "url": url,
            "render_js": "true",
            "premium_proxy": "true",  # Residential proxy
            "country_code": "us"
        }
    )
    return response.text
```

**2. ScrapingAnt** (https://scrapingant.com)
- Cost: $19/month (100,000 API credits) to $249/month
- Similar features to ScrapingBee
- Good for JavaScript-heavy sites

**3. ScrapingRobot** (https://scrapingrobot.com)
- Cost: $49/month (5,000 scrapes) - pay as you go
- Offers pre-built modules for popular sites

**4. Bright Data** (formerly Luminati) - https://brightdata.com
- Cost: $500+/month (enterprise-grade)
- Residential proxy network + scraping infrastructure
- **Best for:** Large-scale, production scraping

**Verdict:** ScrapingBee at $49/month is the sweet spot for this use case.

---

## SOLUTION 2: Stealth Browser + Residential Proxies

### Stack:
- **Playwright** or **Puppeteer** with stealth plugins
- **Residential proxy** (Bright Data, Smartproxy, Oxylabs)
- **Docker** for consistent environment

### Components:

**1. Puppeteer-Extra with Stealth Plugin**
```javascript
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const browser = await puppeteer.launch({
    headless: false,  // Or use xvfb for headful in container
    args: [
        '--proxy-server=http://proxy-provider:port',
        '--disable-blink-features=AutomationControlled'
    ]
});
```

**2. Residential Proxy Providers:**
- **Smartproxy**: $50/month (5GB), rotating residential IPs
- **Oxylabs**: $300/month starter, premium residential network
- **Bright Data**: Pay-per-GB, enterprise quality

**3. Human-like Behavior:**
- Random delays between actions (2-8 seconds)
- Mouse movement paths (not instant jumps)
- Scroll patterns (variable speed, pauses)
- Viewport randomization
- User agent rotation

**Cost estimate:** $50-100/month for proxy + server costs

---

## SOLUTION 3: Official APIs (Limited Availability)

### Zillow API
- **Zillow Data API**: Primarily residential, limited commercial
- **Bridge API**: Requires partnership approval
- **Cost**: Expensive, enterprise-only
- **Verdict**: Not suitable for this use case

### Realtor.com
- No public API for commercial listings
- Partner program exists but restrictive

### LoopNet / CoStar
- **CoStar Go**: Mobile app API (can be reverse-engineered but violates ToS)
- **No official public API** for listings
- **Verdict**: Not viable

### Crexi
- No public API documented
- Some endpoints exposed but not officially supported

**Verdict:** Official APIs are locked down for commercial real estate.

---

## SOLUTION 4: Alternative Data Sources (Free/Public)

### 1. County Assessor Records (Framingham / Middlesex County)
**Massachusetts Land Records:**
- URL: https://www.masslandrecords.com/
- Data available: Property ownership, assessments, parcel maps
- **Not real-time listings** but shows property changes

**Framingham Assessor Database:**
- URL: https://www.framinghamma.gov/assessor
- Can identify commercial properties by zoning
- Searchable by property type, size, owner

### 2. Zoning and Permit Data
**Framingham Planning Department:**
- Phone: (508) 532-5480
- Track commercial permits (indicates activity)
- Zoning map shows commercial zones

### 3. Public Records Scraping
- **NETR Online**: http://www.netronline.com/ (public records portal)
- **Regrid**: https://regrid.com/ (parcel data, some free tier)

**Verdict:** Good for identifying properties, not for active listings.

---

## SOLUTION 5: RSS/Email Alert Aggregation

### Workaround Strategy:
1. Set up alerts ON the sites (LoopNet, Crexi, Realtor.com)
2. Forward alert emails to a parsing service
3. Extract data from notification emails

**Implementation:**
- Create dedicated email: cre-alerts@yourdomain.com
- Set up filters on LoopNet/Crexi for criteria
- Use email parsing (Zapier, n8n, or custom Python)
- Store results in database

**Cost:** Free (just email infrastructure)
**Verdict:** Hacky but effective for daily updates.

---

## RECOMMENDED APPROACH FOR E27 REAL ESTATE

### Phase 1: Quick Win (This Week)
**Use ScrapingBee + Python script**
- Sign up for ScrapingBee ($49/month)
- Build scraper for LoopNet, Crexi, Realtor.com
- Run daily, email results
- **Timeline**: 2-3 days to implement

### Phase 2: Robust Solution (Next Month)
**Stealth Browser + Residential Proxy**
- Build Docker container with Playwright + stealth
- Integrate Smartproxy residential IPs
- Deploy on cloud (AWS/GCP) for reliability
- **Timeline**: 2-3 weeks
- **Cost**: ~$100/month ongoing

### Phase 3: Hybrid (Ongoing)
**Combine approaches:**
- ScrapingBee for daily monitoring
- Manual broker outreach for off-market deals
- County records for property research

---

## IMPLEMENTATION: ScrapingBee Solution

### Step 1: Sign up
https://www.scrapingbee.com - Start with free trial (1000 credits)

### Step 2: Python Implementation
```python
import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime

SCRAPINGBEE_API_KEY = os.getenv('SCRAPINGBEE_API_KEY')

def scrape_loopnet_framingham():
    """Scrape LoopNet for Framingham commercial properties"""
    
    url = "https://www.loopnet.com/search/commercial-real-estate/framingham-ma/retail|industrial|office"
    
    response = requests.get(
        "https://app.scrapingbee.com/api/v1/",
        params={
            "api_key": SCRAPINGBEE_API_KEY,
            "url": url,
            "render_js": "true",
            "premium_proxy": "true",
            "wait": "5000",  # Wait for JS to load
            "country_code": "us"
        },
        timeout=60
    )
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # Extract property cards, prices, addresses
        properties = extract_properties(soup)
        return properties
    else:
        print(f"Error: {response.status_code}")
        return []

def extract_properties(soup):
    """Extract property data from LoopNet HTML"""
    properties = []
    # Selector depends on LoopNet's current structure
    # Inspect element to get correct CSS selectors
    listings = soup.find_all('article', class_='placard')  # Example
    
    for listing in listings:
        prop = {
            'address': listing.find('address').text.strip() if listing.find('address') else 'N/A',
            'price': listing.find('span', class_='price').text.strip() if listing.find('span', class_='price') else 'N/A',
            'sqft': listing.find('span', class_='sqft').text.strip() if listing.find('span', class_='sqft') else 'N/A',
            'url': listing.find('a')['href'] if listing.find('a') else 'N/A'
        }
        properties.append(prop)
    
    return properties

# Run daily
def main():
    properties = scrape_loopnet_framingham()
    # Filter by criteria (0.5+ acres, under $2M)
    # Send email with results
    
if __name__ == "__main__":
    main()
```

### Step 3: Cron Setup
```bash
# Run daily at 9 AM
0 9 * * * cd /path/to/scraper && python3 cre_scraper.py
```

---

## COST SUMMARY

| Solution | Setup Cost | Monthly Cost | Reliability | Speed |
|----------|-----------|--------------|-------------|-------|
| ScrapingBee | Low | $49 | High | Fast |
| Stealth+Proxy | Medium | $100 | Very High | Medium |
| Email Alerts | None | Free | Medium | Slow |
| Official APIs | N/A | N/A | N/A | N/A |
| County Records | Free | Free | Low | Manual |

---

## NEXT STEPS

1. **Test ScrapingBee free trial** (1000 credits)
2. **Build proof-of-concept** for LoopNet
3. **If successful**, subscribe and expand to Crexi, Realtor.com
4. **If blocked**, upgrade to stealth browser solution

---

## NOTES

- **Terms of Service**: Scraping may violate ToS of some sites. Use at own risk.
- **Rate Limiting**: Even with proxies, don't hammer sites. Be respectful.
- **Legal**: Commercial real estate data is valuable. Sites actively protect it.
- **Alternative**: Building relationships with local brokers is often more effective than scraping.
