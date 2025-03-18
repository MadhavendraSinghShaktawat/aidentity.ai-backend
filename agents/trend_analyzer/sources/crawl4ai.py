"""
Web crawler integration for trend analysis.

This module implements a flexible web crawler to scrape and analyze web content
for trending topics in various industries. It can use the crawl4ai library if available,
or fallback to direct HTTP requests with BeautifulSoup.
"""
import asyncio
import logging
import os
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from ..schemas import TrendSource, TrendDepth

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# API keys
CRAWL4AI_API_KEY = os.getenv("CRAWL4AI_API_KEY")

# Source config
NEWS_SOURCES = {
    "Technology": [
        # Updated selectors for more reliable extraction
        {"url": "https://techcrunch.com/", "elements": "h2.post-block__title a", "date_selector": "time.post-block__time"},
        {"url": "https://news.ycombinator.com/", "elements": ".titleline > a", "date_selector": ".age a"},  # Hacker News is very scraper-friendly
        {"url": "https://www.theverge.com/tech", "elements": "h2 a", "date_selector": "time"},
        # Simple blog-style sites are easier to scrape
        {"url": "https://readwrite.com/", "elements": "h3.entry-title a", "date_selector": "time.entry-date"},
    ],
    "Marketing": [
        {"url": "https://www.marketingdive.com/", "elements": "h3.feed__title", "date_selector": ".feed__date"},
        {"url": "https://www.socialmediatoday.com/", "elements": "h3.à-block__title a", "date_selector": ".à-block__byline"},
        {"url": "https://blog.hubspot.com/marketing", "elements": "a.blog-card__title-link", "date_selector": ".blog-card__date"},  # HubSpot blog is easier to scrape
    ],
    "Finance": [
        {"url": "https://www.investopedia.com/markets-news-4427704", "elements": "a.mntl-card-list-items__card", "date_selector": ".mntl-card__byline"},
        {"url": "https://www.fool.com/investing-news/", "elements": ".article-card__headline a", "date_selector": ".article-card__date"},  # Motley Fool is easier to scrape
        {"url": "https://www.marketwatch.com/latest-news", "elements": ".article__headline a", "date_selector": ".article__timestamp"},
    ],
    "Health": [
        {"url": "https://www.healthline.com/health-news", "elements": "a.css-2fdibo", "date_selector": ".css-o4ybrv"},
        {"url": "https://www.medicalnewstoday.com/", "elements": "a.css-1qghw87", "date_selector": ".css-15ycaor"}, 
        {"url": "https://www.everydayhealth.com/news/", "elements": ".js-content-card-title a", "date_selector": ".js-content-card-publish-date"},  # Everyday Health is easier to scrape
    ],
    "General": [
        {"url": "https://news.google.com/", "elements": ".JtKRv", "date_selector": ".SVJrMe"},
        {"url": "https://news.yahoo.com/", "elements": ".js-content-viewer", "date_selector": "time"},  # Yahoo News is easier to scrape
        {"url": "https://www.reuters.com/", "elements": ".text__text__1FZLe", "date_selector": ".date__date__2nuz_"},
        # Reddit is generally more scraper-friendly
        {"url": "https://www.reddit.com/r/news/", "elements": "h3._eYtD2XCVieq6emjKBH3m", "date_selector": "span._2VF2J19pUIMSLJFky-7PEI"},
    ]
}

# Specialized industry keyword patterns to identify relevance
INDUSTRY_KEYWORDS = {
    "Technology": [
        r"ai", r"artificial intelligence", r"machine learning", r"blockchain", r"crypto", 
        r"automation", r"robotics", r"software", r"app", r"cloud", r"data", r"digital", 
        r"tech", r"smartphone", r"computer", r"internet", r"iot", r"cybersecurity"
    ],
    "Marketing": [
        r"marketing", r"advertising", r"brand", r"campaign", r"social media", r"content", 
        r"seo", r"engagement", r"analytics", r"lead generation", r"conversion", r"email marketing"
    ],
    "Finance": [
        r"finance", r"banking", r"investment", r"stock", r"market", r"economy", r"trading", 
        r"fintech", r"crypto", r"bitcoin", r"ethereum", r"money", r"funding", r"venture capital"
    ],
    "Travel": [
        r"travel", r"tourism", r"vacation", r"destination", r"hotel", r"flight", r"airbnb", 
        r"booking", r"resort", r"adventure", r"experience", r"tour"
    ],
    "Health": [
        r"health", r"wellness", r"medical", r"fitness", r"nutrition", r"diet", r"mental health", 
        r"therapy", r"healthcare", r"medicine", r"covid", r"pandemic", r"virus"
    ],
    "Entertainment": [
        r"entertainment", r"movie", r"film", r"tv", r"television", r"streaming", r"music", 
        r"celebrity", r"hollywood", r"netflix", r"disney", r"amazon prime", r"hbo", r"actor", r"actress"
    ]
}

class WebCrawler:
    """
    Flexible web crawler implementation that doesn't rely on external packages.
    """
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the crawler with optional API key.
        
        Args:
            api_key: API key (not used in this implementation but kept for compatibility)
        """
        self.api_key = api_key
        
    async def crawl_trending_content(
        self, 
        industry: str,
        trend_depth: TrendDepth,
        max_pages_per_source: int = 3,
        keywords: Optional[List[str]] = None
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Crawl websites for trending content in a specific industry.
        
        Args:
            industry: The target industry
            trend_depth: How far back to look for trends
            max_pages_per_source: Maximum pages to crawl per source
            keywords: Optional list of keywords to specifically look for
            
        Returns:
            Tuple containing (list of articles, whether real data was used)
        """
        # Get sources for industry (or default to General)
        sources = NEWS_SOURCES.get(industry, NEWS_SOURCES["General"])
        
        # Map trend depth to days
        days_to_check = self._map_trend_depth_to_days(trend_depth)
        
        # Keywords for filtering content
        keyword_patterns = self._prepare_keywords(industry, keywords)
        
        # Use our direct HTTP crawler implementation
        return await self._crawl_with_http(
            sources[:max_pages_per_source], 
            days_to_check, 
            keyword_patterns
        )
    
    async def _crawl_with_http(
        self, 
        sources: List[Dict[str, str]],
        days_to_check: int, 
        keyword_patterns: List[re.Pattern]
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Crawl websites using direct HTTP requests.
        
        Args:
            sources: List of source configurations
            days_to_check: Number of days to include
            keyword_patterns: List of regex patterns for filtering
            
        Returns:
            Tuple containing (list of articles, whether real data was used)
        """
        all_articles = []
        
        # Use httpx for async HTTP requests
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            tasks = []
            for source in sources:
                tasks.append(
                    self._fetch_and_parse(
                        client, 
                        source["url"], 
                        source["elements"],
                        source.get("date_selector")
                    )
                )
                
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error in HTTP crawling: {str(result)}")
                    continue
                    
                articles = self._filter_articles(result, days_to_check, keyword_patterns)
                all_articles.extend(articles)
                
        if not all_articles:
            logger.warning("No articles found, returning empty list")
            return [], True
        
        # Sort by date and relevance
        all_articles = sorted(
            all_articles, 
            key=lambda x: (x.get("date", datetime.now()), x.get("relevance_score", 0)),
            reverse=True
        )
        
        # Limit to most relevant
        all_articles = all_articles[:20]
        
        return all_articles, True
    
    async def _fetch_and_parse(
        self, 
        client: httpx.AsyncClient, 
        url: str, 
        selector: str,
        date_selector: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch and parse a webpage using httpx and BeautifulSoup.
        
        Args:
            client: The httpx client
            url: URL to fetch
            selector: CSS selector for article elements
            date_selector: CSS selector for date elements
            
        Returns:
            List of extracted articles
        """
        try:
            logger.info(f"Fetching {url}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0"
            }
            
            # Attempt to fetch the URL with a timeout
            try:
                response = await client.get(url, headers=headers, timeout=20.0)
                response.raise_for_status()
            except httpx.TimeoutException:
                logger.warning(f"Timeout fetching {url}, retrying with longer timeout")
                response = await client.get(url, headers=headers, timeout=30.0)
                response.raise_for_status()
            
            # Log the response status and content length
            logger.info(f"Got response from {url}: status={response.status_code}, content length={len(response.text)}")
            
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = []
            
            # Try multiple selector variations if the original doesn't work
            selectors_to_try = [selector]
            
            # Add some common fallback selectors based on the page structure
            if "h2" in selector or "h3" in selector:
                selectors_to_try.append("h2 a")
                selectors_to_try.append("h3 a")
                selectors_to_try.append(".headline a")
                selectors_to_try.append(".title a")
            
            elements = []
            for sel in selectors_to_try:
                elements = soup.select(sel)
                if elements:
                    logger.info(f"Found {len(elements)} elements using selector '{sel}' on {url}")
                    break
            
            if not elements:
                # Debug output to help diagnose selector issues
                logger.warning(f"No elements found with any selectors on {url}")
                logger.debug(f"Page title: {soup.title.string if soup.title else 'No title'}")
                logger.debug(f"First 500 chars of HTML: {response.text[:500]}...")
                return []
            
            for element in elements:
                title = element.get_text(strip=True)
                link = element.get('href', '')
                
                # Skip empty titles
                if not title:
                    continue
                
                # Handle relative URLs
                if link and not link.startswith(('http://', 'https://')):
                    if link.startswith('/'):
                        domain = '/'.join(url.split('/')[:3])
                        link = domain + link
                    else:
                        link = url + link
                
                # Extract date if date selector is provided
                pub_date = None
                if date_selector:
                    date_element = None
                    # Try to find date element in different locations
                    for parent in [element, element.parent, element.parent.parent]:
                        try:
                            date_element = parent.select_one(date_selector)
                            if date_element:
                                break
                        except Exception:
                            continue
                            
                    if date_element:
                        date_text = date_element.get_text(strip=True)
                        pub_date = self._parse_date(date_text)
                        logger.debug(f"Found date '{date_text}' parsed as {pub_date}")
                
                if title and link:
                    articles.append({
                        "title": title,
                        "url": link,
                        "source": url,
                        "date": pub_date or datetime.now()
                    })
            
            logger.info(f"Extracted {len(articles)} articles from {url}")
            
            # If we couldn't extract articles with the selectors, try a generic approach
            if not articles:
                logger.info(f"Trying generic article extraction for {url}")
                generic_articles = self._extract_articles_generic(soup, url)
                if generic_articles:
                    logger.info(f"Found {len(generic_articles)} articles with generic extraction")
                    articles.extend(generic_articles)
            
            return articles
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return []
    
    def _extract_articles_generic(self, soup: BeautifulSoup, source_url: str) -> List[Dict[str, Any]]:
        """
        Generic article extraction when specific selectors fail.
        
        Args:
            soup: BeautifulSoup object of the page
            source_url: Source URL for reference
            
        Returns:
            List of extracted articles
        """
        articles = []
        
        # Try to find articles by looking for common patterns
        # 1. Look for <article> tags
        for article in soup.find_all('article'):
            title_tag = article.find(['h1', 'h2', 'h3', 'h4', 'a'], class_=lambda c: c and ('title' in c.lower() or 'headline' in c.lower()))
            if not title_tag:
                title_tag = article.find(['h1', 'h2', 'h3', 'h4', 'a'])
            
            if title_tag:
                title = title_tag.get_text(strip=True)
                link = title_tag.get('href', '') if title_tag.name == 'a' else None
                
                if not link:
                    link_tag = article.find('a')
                    if link_tag:
                        link = link_tag.get('href', '')
                
                # Handle relative URLs
                if link and not link.startswith(('http://', 'https://')):
                    if link.startswith('/'):
                        domain = '/'.join(source_url.split('/')[:3])
                        link = domain + link
                    else:
                        link = source_url + link
                
                if title and link:
                    articles.append({
                        "title": title,
                        "url": link,
                        "source": source_url,
                        "date": datetime.now()  # Default to current date for generic extraction
                    })
        
        # 2. If no articles found, look for lists of links
        if not articles:
            for ul in soup.find_all(['ul', 'div'], class_=lambda c: c and ('list' in c.lower() or 'feed' in c.lower() or 'content' in c.lower())):
                for a in ul.find_all('a', href=True):
                    title = a.get_text(strip=True)
                    link = a.get('href', '')
                    
                    # Skip navigation, footer links, etc.
                    if len(title) < 15 or any(x in link.lower() for x in ['login', 'sign', 'account', 'about', 'contact', 'privacy', 'terms']):
                        continue
                    
                    # Handle relative URLs
                    if link and not link.startswith(('http://', 'https://')):
                        if link.startswith('/'):
                            domain = '/'.join(source_url.split('/')[:3])
                            link = domain + link
                        else:
                            link = source_url + link
                    
                    if title and link:
                        articles.append({
                            "title": title,
                            "url": link,
                            "source": source_url,
                            "date": datetime.now()
                        })
        
        return articles
    
    def _filter_articles(
        self, 
        articles: List[Dict[str, Any]], 
        days_to_check: int,
        keyword_patterns: List[re.Pattern]
    ) -> List[Dict[str, Any]]:
        """
        Filter articles by date and relevance.
        
        Args:
            articles: List of articles to filter
            days_to_check: Number of days to include
            keyword_patterns: List of regex patterns for filtering
            
        Returns:
            Filtered list of articles
        """
        filtered = []
        min_date = datetime.now() - timedelta(days=days_to_check)
        
        for article in articles:
            # Skip if too old
            pub_date = article.get("date")
            if pub_date and pub_date < min_date:
                continue
                
            # Check relevance with keywords
            title = article.get("title", "")
            relevance_score = self._calculate_relevance(title, keyword_patterns)
            
            # Only include articles with at least some relevance
            if relevance_score > 0:
                article["relevance_score"] = relevance_score
                filtered.append(article)
                
        logger.info(f"Filtered to {len(filtered)} relevant articles")
        return filtered
    
    def _calculate_relevance(self, text: str, patterns: List[re.Pattern]) -> float:
        """
        Calculate relevance score based on keyword matches.
        
        Args:
            text: The text to analyze
            patterns: List of regex patterns to match
            
        Returns:
            Relevance score from 0.0 to 1.0
        """
        if not text or not patterns:
            return 0.0
            
        text = text.lower()
        matches = 0
        
        for pattern in patterns:
            if pattern.search(text):
                matches += 1
                
        # Normalize score between 0 and 1
        return matches / len(patterns) if patterns else 0.0
    
    def _prepare_keywords(self, industry: str, keywords: Optional[List[str]] = None) -> List[re.Pattern]:
        """
        Prepare regex patterns for keywords.
        
        Args:
            industry: The target industry
            keywords: Optional list of additional keywords
            
        Returns:
            List of compiled regex patterns
        """
        # Get industry-specific keywords
        industry_kws = INDUSTRY_KEYWORDS.get(industry, [])
        
        # Combine with custom keywords
        all_keywords = set(industry_kws)
        if keywords:
            all_keywords.update([k.lower() for k in keywords])
            
        # Compile regex patterns with word boundaries
        patterns = [re.compile(rf'\b{re.escape(kw)}\b', re.IGNORECASE) for kw in all_keywords]
        
        return patterns
    
    def _map_trend_depth_to_days(self, trend_depth: TrendDepth) -> int:
        """
        Map trend depth enum to number of days.
        
        Args:
            trend_depth: The trend depth enum
            
        Returns:
            Number of days to look back
        """
        if trend_depth == TrendDepth.LAST_24H:
            return 1
        elif trend_depth == TrendDepth.PAST_WEEK:
            return 7
        else:  # TrendDepth.MONTHLY
            return 30
    
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """
        Parse date from text using various patterns.
        
        Args:
            date_text: Text containing date information
            
        Returns:
            Parsed datetime or None if parsing failed
        """
        # Common date patterns
        patterns = [
            # Today, Yesterday
            (r'today|now', lambda x: datetime.now()),
            (r'yesterday', lambda x: datetime.now() - timedelta(days=1)),
            # Hours ago
            (r'(\d+)\s*hours?\s*ago', lambda x: datetime.now() - timedelta(hours=int(x.group(1)))),
            # Minutes ago
            (r'(\d+)\s*minutes?\s*ago', lambda x: datetime.now() - timedelta(minutes=int(x.group(1)))),
            # Days ago
            (r'(\d+)\s*days?\s*ago', lambda x: datetime.now() - timedelta(days=int(x.group(1)))),
            # ISO format
            (r'\d{4}-\d{2}-\d{2}', lambda x: datetime.fromisoformat(x.group(0))),
            # Month Day, Year
            (r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2}),?\s+(\d{4})',
                lambda x: datetime.strptime(f"{x.group(1)} {x.group(2)} {x.group(3)}", "%b %d %Y"))
        ]
        
        if not date_text:
            return None
            
        # Try each pattern
        for pattern, parser in patterns:
            match = re.search(pattern, date_text, re.IGNORECASE)
            if match:
                try:
                    return parser(match)
                except Exception:
                    continue
                    
        return None

async def fetch_crawl4ai_trends(
    industry: str,
    trend_depth: TrendDepth,
    keywords: Optional[List[str]] = None
) -> TrendSource:
    """
    Fetch trending topics from web sources using the web crawler.
    
    Args:
        industry: The target industry
        trend_depth: How far back to analyze trends
        keywords: Optional list of keywords to focus on
        
    Returns:
        A TrendSource object with the crawling results
    """
    try:
        logger.info(f"Fetching web trends for {industry} over {trend_depth}")
        
        # Initialize crawler (doesn't depend on crawl4ai package)
        crawler = WebCrawler()
        
        # Crawl for trending content
        articles, is_real_data = await crawler.crawl_trending_content(
            industry=industry,
            trend_depth=trend_depth,
            keywords=keywords
        )
        
        if not articles:
            # Return mock data if crawling failed
            logger.warning("Web crawling returned no results, returning mock data")
            return _create_mock_crawl4ai_data(industry, trend_depth)
        
        # Format the results
        formatted_data = _format_article_data(articles, industry)
        
        # Create the trend source
        source = TrendSource(
            platform="WebTrends",
            raw_data=formatted_data,
            timestamp=datetime.utcnow(),
            metadata={
                "is_mock": not is_real_data,
                "source_count": len(articles),
                "industry": industry,
                "trend_depth": trend_depth.value
            }
        )
        
        logger.info(f"Successfully fetched {len(articles)} articles")
        return source
        
    except Exception as e:
        logger.error(f"Error fetching web trends: {str(e)}", exc_info=True)
        return _create_mock_crawl4ai_data(industry, trend_depth)

def _format_article_data(articles: List[Dict[str, Any]], industry: str) -> str:
    """
    Format article data into a readable string.
    
    Args:
        articles: List of article dictionaries
        industry: The target industry
        
    Returns:
        Formatted string representation
    """
    if not articles:
        return f"No trending {industry} articles found."
        
    result = f"Top {len(articles)} Trending Articles in {industry}:\n\n"
    
    for i, article in enumerate(articles, 1):
        title = article.get("title", "Untitled")
        url = article.get("url", "")
        source = article.get("source", "").replace("https://", "").replace("www.", "").split("/")[0]
        
        date_str = ""
        if date := article.get("date"):
            if isinstance(date, datetime):
                date_str = date.strftime("%Y-%m-%d")
                
        relevance = article.get("relevance_score", 0) * 100
        
        result += f"{i}. {title}\n"
        result += f"   Source: {source} | Date: {date_str} | Relevance: {relevance:.0f}%\n"
        result += f"   URL: {url}\n\n"
    
    # Add a section summary
    topics = _extract_main_topics([a.get("title", "") for a in articles])
    result += f"\nMain Topics Trending in {industry}:\n"
    for topic, count in topics.items():
        result += f"- {topic} (mentioned in {count} articles)\n"
        
    return result

def _extract_main_topics(titles: List[str]) -> Dict[str, int]:
    """
    Extract main topics from article titles.
    
    Args:
        titles: List of article titles
        
    Returns:
        Dictionary of topics and their occurrence count
    """
    # Common stopwords to ignore
    stopwords = {
        "a", "an", "the", "in", "on", "at", "to", "for", "with", "by", "about", 
        "as", "of", "and", "or", "but", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will", "would",
        "should", "could", "may", "might", "must", "can", "this", "that"
    }
    
    # Extract words and phrases
    topics = {}
    
    for title in titles:
        # Clean the title
        clean_title = re.sub(r'[^\w\s]', '', title.lower())
        words = clean_title.split()
        
        # Skip stopwords and single-character words
        filtered_words = [w for w in words if w not in stopwords and len(w) > 1]
        
        # Count individual words
        for word in filtered_words:
            if word in topics:
                topics[word] += 1
            else:
                topics[word] = 1
        
        # Check for common phrases (2-3 words)
        for i in range(len(filtered_words) - 1):
            phrase = ' '.join(filtered_words[i:i+2])
            if phrase in topics:
                topics[phrase] += 1
            else:
                topics[phrase] = 1
                
    # Filter to most common topics (appearing more than once)
    filtered_topics = {k: v for k, v in topics.items() if v > 1}
    
    # Sort by count and return top 10
    return dict(sorted(filtered_topics.items(), key=lambda x: x[1], reverse=True)[:10])

def _create_mock_crawl4ai_data(industry: str, trend_depth: TrendDepth) -> TrendSource:
    """
    Create mock crawling data when real crawling fails.
    
    Args:
        industry: The target industry
        trend_depth: The trend depth
        
    Returns:
        A TrendSource with mock data
    """
    mock_articles = [
        {
            "title": f"Latest {industry} Trends You Need to Know in 2024",
            "source": "trendindustry.com",
            "date": "2024-03-18",
            "relevance": "95%"
        },
        {
            "title": f"How AI is Transforming the {industry} Landscape",
            "source": "aibusiness.com",
            "date": "2024-03-17", 
            "relevance": "93%"
        },
        {
            "title": f"Top 10 {industry} Innovations of the Month",
            "source": "innovationweekly.com",
            "date": "2024-03-15",
            "relevance": "90%"
        },
        {
            "title": f"The Future of {industry}: Expert Predictions",
            "source": "futurism.com",
            "date": "2024-03-14",
            "relevance": "87%"
        },
        {
            "title": f"Why {industry} Companies Are Investing in Blockchain",
            "source": "techtrends.com",
            "date": "2024-03-12",
            "relevance": "85%"
        }
    ]
    
    formatted_data = f"[MOCK DATA] Top 5 Trending Articles in {industry}:\n\n"
    
    for i, article in enumerate(mock_articles, 1):
        formatted_data += f"{i}. {article['title']}\n"
        formatted_data += f"   Source: {article['source']} | Date: {article['date']} | Relevance: {article['relevance']}\n\n"
    
    formatted_data += f"\nMain Topics Trending in {industry}:\n"
    formatted_data += f"- AI (mentioned in 3 articles)\n"
    formatted_data += f"- Innovation (mentioned in 2 articles)\n"
    formatted_data += f"- Blockchain (mentioned in 2 articles)\n"
    formatted_data += f"- Future Trends (mentioned in 2 articles)\n"
    
    return TrendSource(
        platform="WebTrends",
        raw_data=formatted_data,
        timestamp=datetime.utcnow(),
        metadata={
            "is_mock": True,
            "source_count": len(mock_articles),
            "industry": industry,
            "trend_depth": trend_depth.value
        }
    ) 