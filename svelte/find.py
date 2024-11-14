import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from typing import Set, List
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class UrlData:
    url: str
    title: str
    found_at: str
    timestamp: str
    status_code: int

class UrlFinder:
    def __init__(self, base_url: str, max_pages: int = 10, same_domain_only: bool = True):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.max_pages = max_pages
        self.same_domain_only = same_domain_only
        self.visited_urls: Set[str] = set()
        self.found_urls: List[UrlData] = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and should be processed"""
        if not url or url.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
            return False
            
        if self.same_domain_only:
            return urlparse(url).netloc == self.domain
            
        return True
    
    def get_page_data(self, url: str, found_at: str) -> None:
        """Fetch and process a single page"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string if soup.title else url
            
            # Store the URL data
            url_data = UrlData(
                url=url,
                title=title.strip() if title else "No title",
                found_at=found_at,
                timestamp=datetime.now().isoformat(),
                status_code=response.status_code
            )
            self.found_urls.append(url_data)
            
            # Process links if we haven't reached the limit
            if len(self.visited_urls) < self.max_pages:
                links = soup.find_all('a', href=True)
                
                for link in links:
                    href = link['href']
                    absolute_url = urljoin(url, href)
                    
                    if (self.is_valid_url(absolute_url) and 
                        absolute_url not in self.visited_urls):
                        self.visited_urls.add(absolute_url)
                        self.get_page_data(absolute_url, url)
                        
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"Error processing {url}: {e}")
    
    def find_urls(self) -> List[UrlData]:
        """Start the URL finding process"""
        print(f"Starting URL search from {self.base_url}")
        self.visited_urls.add(self.base_url)
        self.get_page_data(self.base_url, "starting_point")
        return self.found_urls
    
    def save_results(self, filename: str = "svelte/urls.json"):
        """Save results to a JSON file"""
        data = [
            {
                "url": url.url,
                "title": url.title,
                "found_at": url.found_at,
                "timestamp": url.timestamp,
                "status_code": url.status_code
            }
            for url in self.found_urls
        ]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Results saved to {filename}")
    
    def export_urls_to_txt(self, filename: str = "svelte/urls.txt"):
        """Export just the URLs to a text file, separated by commas"""
        urls = [f'"{url.url}"' for url in self.found_urls]
        urls_text = ",".join(urls)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(urls_text)
        
        print(f"URLs exported to {filename}")

def main(urls):
    for url in urls:    
    # Example usage
        base_url = url  # Replace with your target URL
        finder = UrlFinder(
            base_url=base_url,
            max_pages=10,  # Limit to 50 pages
            same_domain_only=True  # Only find URLs on the same domain
        )
        
        print(f"Starting URL finder for {base_url}")
        print(f"Max pages: {finder.max_pages}")
        print(f"Same domain only: {finder.same_domain_only}")
        
        # Find URLs
        urls = finder.find_urls()
        
        print("\nResults:")
        print(f"Found {len(urls)} URLs")
        
        # Save both formats
        finder.save_results()  # Full JSON data
        finder.export_urls_to_txt()  # Simple comma-separated URLs
        
        # Print some statistics
        domains = set(urlparse(url.url).netloc for url in urls)
        print(f"\nUnique domains found: {len(domains)}")
        print("\nSample of found URLs:")
    for url in urls[:5]:  # Show first 5 URLs
        print(f"- {url.url} (found at: {url.found_at})")

if __name__ == "__main__":
    urls = [
        "https://www.w3schools.com/js/",
        "https://www.typescriptlang.org/docs/",
        "https://www.w3schools.com/html",
        "https://www.w3schools.com/css",
        "https://www.w3schools.com/sql",
        "https://www.w3schools.com/typescript",
        "https://tailwindcss.com/docs"

    ]
    main(urls)