import os
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from pathlib import Path

class WebsiteCopier:
    def __init__(self, base_url, output_dir="docs"):
        self.base_url = base_url
        self.output_dir = output_dir
        self.visited_urls = set()
        self.domain = urlparse(base_url).netloc
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})

    def save_resource(self, url, content, content_type):
        parsed_url = urlparse(url)
        path = parsed_url.path.lstrip('/')
        
        # Create local file path
        if not path:
            path = 'index.html'
        elif '.' not in os.path.basename(path):
            path = os.path.join(path, 'index.html')
            
        local_path = os.path.join(self.output_dir, path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        # Save content
        mode = 'w' if 'text' in content_type else 'wb'
        with open(local_path, mode) as f:
            f.write(content if mode == 'wb' else content.decode('utf-8'))
            
        return local_path

    def download_asset(self, url):
        if url in self.visited_urls:
            return
        self.visited_urls.add(url)
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                self.save_resource(url, response.content, content_type)
        except Exception as e:
            print(f"Error downloading {url}: {e}")

    def process_page(self, url):
        if url in self.visited_urls:
            return
        self.visited_urls.add(url)
        
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                # Save main HTML
                content_type = response.headers.get('Content-Type', '')
                html_content = response.content
                local_path = self.save_resource(url, html_content, content_type)
                
                # Parse HTML for linked resources
                soup = BeautifulSoup(html_content, 'lxml')
                
                # Find all resources that need to be downloaded
                tags = {
                    'img': 'src',
                    'link': 'href',
                    'script': 'src',
                    'a': 'href'
                }
                
                for tag, attr in tags.items():
                    for element in soup.find_all(tag):
                        resource_url = element.get(attr)
                        if resource_url:
                            absolute_url = urljoin(url, resource_url)
                            if urlparse(absolute_url).netloc == self.domain:
                                # Download linked resource
                                self.download_asset(absolute_url)
                                
                                # Update link to local path
                                parsed = urlparse(absolute_url)
                                local_resource_path = os.path.join(
                                    self.output_dir, 
                                    parsed.path.lstrip('/')
                                )
                                element[attr] = os.path.relpath(
                                    local_resource_path, 
                                    os.path.dirname(local_path)
                                )
                                
                # Save modified HTML
                with open(local_path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                
                # Find and process other pages
                for link in soup.find_all('a'):
                    href = link.get('href')
                    if href:
                        absolute_url = urljoin(url, href)
                        if (urlparse(absolute_url).netloc == self.domain and
                            not absolute_url.endswith(('.pdf', '.zip'))):
                            self.process_page(absolute_url)

        except Exception as e:
            print(f"Error processing {url}: {e}")

    def start(self):
        self.process_page(self.base_url)

if __name__ == "__main__":
    copier = WebsiteCopier("https://n1589766.websitebuilder.online/")
    copier.start()
    print("Website mirroring complete!")

