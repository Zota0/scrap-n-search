# from scraper import AISearchSystem, WebContent
# import sqlite3
# from datetime import datetime


# def test_database():
#     print("Testing database connection and content...")
    
#     # Initialize the system
#     system = AISearchSystem()
    
#     # Add some test content
#     test_content = WebContent(
#         url="https://example.com/",
#         content="This is a test entry about artificial intelligence. AI is changing the world through machine learning and neural networks.",
#         timestamp=datetime.now(),
#         metadata={
#             'title': "Test AI Content",
#             'tags': ['AI', 'test']
#         }
#     )
    
#     try:
#         # Store content
#         print("Storing test content...")
#         system.store_content(test_content)
#         print("Content stored successfully!")
        
#         # Test database connection
#         with sqlite3.connect(system.db_path) as conn:
#             cursor = conn.cursor()
            
#             # Check web_content table
#             cursor.execute("SELECT COUNT(*) FROM web_content")
#             content_count = cursor.fetchone()[0]
#             print(f"Number of content entries: {content_count}")
            
#             # Check embeddings table
#             cursor.execute("SELECT COUNT(*) FROM embeddings")
#             embedding_count = cursor.fetchone()[0]
#             print(f"Number of embeddings: {embedding_count}")
            
#         print("Database test completed successfully!")
        
#     except Exception as e:
#         print(f"Error during testing: {e}")
