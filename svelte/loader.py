from scraper import AISearchSystem, WebContent
from datetime import datetime
import os
from typing import List, Dict
import json
from pathlib import Path

class DataLoader:
    def __init__(self):
        self.search_system = AISearchSystem()
    
    def add_text_file(self, file_path: str, title: str = None, tags: List[str] = None):
        """Add content from a text file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        file_name = os.path.basename(file_path)
        web_content = WebContent(
            url=f"file://{file_path}",
            content=content,
            timestamp=datetime.now(),
            metadata={
                'title': title or file_name,
                'tags': tags or ['document']
            }
        )
        
        self.search_system.store_content(web_content)
        print(f"Added content from: {file_path}")
    
    def add_directory(self, dir_path: str, extensions: List[str] = None):
        """Add all text files from a directory"""
        if extensions is None:
            extensions = ['.txt', '.md', '.json', '.py', '.js', '.html', '.css']
            
        path = Path(dir_path)
        for file_path in path.rglob('*'):
            if file_path.suffix in extensions:
                try:
                    self.add_text_file(str(file_path))
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
    
    def add_markdown_file(self, file_path: str, tags: List[str] = None):
        """Add content from a markdown file, preserving structure"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        web_content = WebContent(
            url=f"file://{file_path}",
            content=content,
            timestamp=datetime.now(),
            metadata={
                'title': os.path.basename(file_path),
                'tags': tags or ['markdown', 'document']
            }
        )
        
        self.search_system.store_content(web_content)
        print(f"Added markdown from: {file_path}")
    
    def add_web_url(self, url: str, tags: List[str] = None):
        """Add content from a web URL"""
        try:
            web_content = self.search_system.scrape_url(url)
            if tags:
                web_content.metadata['tags'].extend(tags)
            self.search_system.store_content(web_content)
            print(f"Added content from URL: {url}")
        except Exception as e:
            print(f"Error processing URL {url}: {e}")
    
    def add_notes(self, title: str, content: str, tags: List[str] = None):
        """Add custom notes or content"""
        web_content = WebContent(
            url=f"note://{title.lower().replace(' ', '-')}",
            content=content,
            timestamp=datetime.now(),
            metadata={
                'title': title,
                'tags': tags or ['notes']
            }
        )
        
        self.search_system.store_content(web_content)
        print(f"Added note: {title}")

# Example usage function
def add_example_data():
    loader = DataLoader()
    
    # Add a simple note
    loader.add_notes(
        title="Python Programming Tips",
        content="""
        Here are some important Python programming tips:
        1. Use virtual environments for project isolation
        2. Write clear docstrings for functions
        3. Follow PEP 8 style guidelines
        4. Use type hints for better code clarity
        5. Handle exceptions appropriately
        """,
        tags=['python', 'programming', 'tips']
    )
    
    # Add content from a directory
    loader.add_directory('./docs')
    
    # Add a specific markdown file
    loader.add_markdown_file('README.md')
    
    # Add content from web URLs
    urls = [
        'https://example.com/article1',
        'https://example.com/article2'
    ]
    for url in urls:
        loader.add_web_url(url)

if __name__ == "__main__":
    # You can either run example_data() or create your own loading script
    loader = DataLoader()
    
    # Example: Add some custom notes
    loader.add_notes(
        title="Getting Started",
        content="""
        Welcome to the AI Search System!
        
        This is a powerful tool that helps you search and analyze content.
        You can add various types of content:
        - Text files
        - Markdown documents
        - Web pages
        - Custom notes
        
        The system will process all content and make it searchable using
        advanced AI techniques.
        """,
        tags=['guide', 'introduction']
    )
    
    # Add current directory's python files
    loader.add_directory('.', extensions=['.py'])