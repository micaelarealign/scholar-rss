from flask import Flask, Response, request
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime
from urllib.parse import urlencode
import logging
import time
from random import uniform

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
@app.route('/')
def home():
    return '''
    <h1>Scholar RSS Feed Generator</h1>
    <p>Access the feed at: <a href="/scholar.rss?q=psilocybin">/scholar.rss?q=psilocybin</a></p>
    '''

def get_scholar_url(query='psilocybin'):
    base_url = 'https://scholar.google.com/scholar'
    params = {
        'q': query,
        'hl': 'en',
        'as_sdt': '0,5',
        'scisbd': '1',
        'as_ylo': '2024'
    }
    return f"{base_url}?{urlencode(params)}"

def parse_scholar_results(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    articles = soup.find_all('div', class_='gs_r gs_or gs_scl')
    results = []
    
    for article in articles:
        try:
            title_elem = article.find('h3', class_='gs_rt')
            title = title_elem.text.strip() if title_elem else 'No title'
            
            link = title_elem.find('a')
            url = link['href'] if link else ''
            
            authors = article.find('div', class_='gs_a').text.strip()
            abstract = article.find('div', class_='gs_rs').text.strip()
            
            results.append({
                'title': title,
                'url': url,
                'authors': authors,
                'abstract': abstract
            })
        except Exception as e:
            logging.error(f"Error parsing article: {e}")
            continue
            
    return results

from datetime import datetime, timezone
@app.route('/scholar.rss')
def scholar_rss():
    query = request.args.get('q', 'psilocybin')
    
    # Create feed
    fg = FeedGenerator()
    fg.title(f'Google Scholar - {query}')
    fg.link(href=get_scholar_url(query))
    fg.description(f'Latest research about {query}')
    fg.language('en')
    
    # Define headers here
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    
    try:
        response = requests.get(get_scholar_url(query), headers=headers)
        articles = parse_scholar_results(response.text)
        
        for article in articles:
            fe = fg.add_entry()
            fe.title(article['title'])
            fe.link(href=article['url'])
            fe.description(article['abstract'])
            fe.author({'name': article['authors']})
            fe.pubDate(datetime.now(timezone.utc))
            
    except Exception as e:
        logging.error(f"Error fetching results: {e}")
        return Response("Error generating feed", status=500)
    
    return Response(fg.rss_str(pretty=True), mimetype='application/rss+xml')


if __name__ == '__main__':
    app.run(debug=True)
