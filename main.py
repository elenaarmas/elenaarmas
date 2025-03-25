import os
import re
import time
import requests
from urllib.parse import urljoin, urlparse, unquote
from bs4 import BeautifulSoup

class WordPressMirror:
    def __init__(self, base_url, output_dir="docs"):
        self.base_url = base_url
        self.output_dir = output_dir
        self.visited = set()
        self.asset_cache = {}
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': self.base_url
        }
        self.domain = urlparse(base_url).netloc

    def normalize_path(self, url):
        """Preserve WordPress media structure while cleaning parameters"""
        parsed = urlparse(url)
        path = unquote(parsed.path).lstrip('/')
        
        # Clean WordPress-specific patterns
        path = re.sub(r'-\d+x\d+(?=\.\w+$)', '', path)  # Remove size suffixes
        path = re.sub(r'\?.*', '', path)  # Remove query parameters
        path = re.sub(r'/(l\d+/t\d+/w\d+/h\d+)/', '/', path)  # Remove image crop parameters
        
        # Handle directory indexes
        if not path:
            path = "index.html"
        elif path.endswith('/'):
            path += "index.html"
        elif '.' not in os.path.basename(path):
            path = os.path.join(path, "index.html")
            
        return os.path.join(self.output_dir, path)

    def fetch_asset(self, url):
        """Fetch asset with WordPress fallback logic"""
        # First try with size suffix
        response = self.session.get(url, timeout=10, stream=True)
        if response.status_code == 200:
            return response.content
        
        # Fallback to version without size suffix
        clean_url = re.sub(r'-\d+x\d+(?=\.\w+$)', '', url)
        if clean_url != url:
            response = self.session.get(clean_url, timeout=10, stream=True)
            if response.status_code == 200:
                return response.content
        
        return None

    def process_asset(self, base_url, asset_url):
        """Process assets with WordPress-specific fallbacks"""
        if not asset_url or asset_url.startswith(('data:', '#')):
            return asset_url
            
        absolute_url = urljoin(base_url, asset_url)
        if urlparse(absolute_url).netloc != self.domain:
            return asset_url

        if absolute_url in self.asset_cache:
            return self.asset_cache[absolute_url]

        content = self.fetch_asset(absolute_url)
        if not content:
            return asset_url  # Return original if both attempts fail

        # Normalize path preserving UUID directories
        local_path = self.normalize_path(absolute_url)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        try:
            with open(local_path, 'wb') as f:
                f.write(content)
            
            # Calculate relative path
            base_path = os.path.dirname(self.normalize_path(base_url))
            relative_path = os.path.relpath(local_path, base_path)
            
            self.asset_cache[absolute_url] = relative_path
            return relative_path
        except Exception as e:
            print(f"Error saving {local_path}: {e}")
            return asset_url

    def process_page(self, url):
        """Process page with enhanced WordPress media handling"""
        if url in self.visited:
            return
        self.visited.add(url)
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            return

        soup = BeautifulSoup(response.content, 'lxml')
        
        # Process all assets
        for tag, attr in [('img', 'src'), ('link', 'href'), ('script', 'src'), ('source', 'srcset')]:
            for element in soup.find_all(tag, **{attr: True}):
                self.process_element_asset(url, element, attr)

        # Process CSS background images
        for style in soup.find_all('style'):
            if style.string:
                self.process_css_assets(url, style)

        # Save modified HTML
        local_path = self.normalize_path(url)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        # Crawl internal links
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href and not href.startswith(('mailto:', 'tel:', 'javascript:')):
                absolute_url = urljoin(url, href)
                if urlparse(absolute_url).netloc == self.domain:
                    self.process_page(absolute_url)

    def process_element_asset(self, base_url, element, attr):
        """Process individual element assets"""
        if attr == 'srcset':
            new_srcset = []
            for source in element[attr].split(','):
                url_part = source.strip().split()[0]
                processed = self.process_asset(base_url, url_part)
                if processed:
                    new_srcset.append(f"{processed} {source.split()[-1]}")
            if new_srcset:
                element[attr] = ', '.join(new_srcset)
        else:
            original = element[attr]
            processed = self.process_asset(base_url, original)
            if processed:
                element[attr] = processed

    def process_css_assets(self, base_url, style_tag):
        """Process CSS url() references with WordPress fallbacks"""
        css = style_tag.string
        urls = re.findall(r'url\((["\']?)(.*?)\1\)', css)
        for quote, url in urls:
            processed = self.process_asset(base_url, url.strip())
            if processed:
                css = css.replace(url, processed)
        style_tag.string = css

    def run(self):
        """Start mirroring process"""
        print(f"Starting mirror of {self.base_url}")
        self.process_page(self.base_url)
        print(f"Mirror complete! Saved to {self.output_dir}")

if __name__ == "__main__":
    WordPressMirror("https://n1589766.websitebuilder.online/").run()

