from loader import DataLoader

def load_my_data():
    loader = DataLoader()
    
    # Add documentation
    # loader.add_directory('./documentation', extensions=['.md', '.txt'])
    
    # Add source code
    # loader.add_directory('./src', extensions=['.py', '.js'])
    
    # Add specific articles
    articles = [
        'https://example.com/',
    ]
    
    for url in articles:
        loader.add_web_url(url, tags=['article'])
    
    # Add some notes

if __name__ == "__main__":
    load_my_data()