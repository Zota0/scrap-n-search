from bs4 import BeautifulSoup
import requests
import sqlite3
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
import os
from sklearn.cluster import KMeans
import nltk
from nltk.tokenize import sent_tokenize
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

@dataclass
class WebContent:
    url: str
    content: str
    timestamp: datetime
    metadata: Dict

class AISearchSystem:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), "knowledge_base.db")
        self.db_path = db_path
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self._init_database()
    
    def _init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS web_content (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE,
                    content TEXT,
                    timestamp DATETIME,
                    title TEXT,
                    tags TEXT,
                    summary TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_id INTEGER,
                    chunk_text TEXT,
                    embedding BLOB,
                    key_points TEXT,
                    FOREIGN KEY(content_id) REFERENCES web_content(id)
                )
            """)
    
    def generate_summary(self, text: str, num_sentences: int = 3) -> str:
        """Generate a summary using extractive summarization"""
        # Split text into sentences
        sentences = sent_tokenize(text)
        if len(sentences) <= num_sentences:
            return text
            
        # Generate embeddings for all sentences
        embeddings = self.embedding_model.encode(sentences)
        
        # Calculate sentence importance using similarity to mean embedding
        mean_embedding = np.mean(embeddings, axis=0)
        similarities = np.dot(embeddings, mean_embedding) / (
            np.linalg.norm(embeddings, axis=1) * np.linalg.norm(mean_embedding)
        )
        
        # Get indices of most important sentences
        top_indices = np.argsort(similarities)[-num_sentences:]
        top_indices = sorted(top_indices)  # Sort to maintain original order
        
        # Combine sentences
        summary = ' '.join([sentences[i] for i in top_indices])
        return summary
    
    def extract_key_points(self, text: str) -> List[str]:
        """Extract key points from the text"""
        sentences = sent_tokenize(text)
        if len(sentences) < 2:
            return sentences
            
        embeddings = self.embedding_model.encode(sentences)
        
        # Use clustering to identify main topics
        n_clusters = min(len(sentences) // 3, 5)  # Adjust number of clusters based on content length
        if n_clusters < 2:
            return sentences
            
        kmeans = KMeans(n_clusters=n_clusters, n_init=10)
        clusters = kmeans.fit_predict(embeddings)
        
        # Select most central sentence from each cluster
        key_points = []
        for i in range(n_clusters):
            cluster_sentences = [s for j, s in enumerate(sentences) if clusters[j] == i]
            if cluster_sentences:
                # Find sentence closest to cluster center
                cluster_embeddings = embeddings[clusters == i]
                center_idx = np.argmin(np.linalg.norm(cluster_embeddings - kmeans.cluster_centers_[i], axis=1))
                key_points.append(cluster_sentences[center_idx])
        
        return key_points

    def semantic_search(self, query: str, top_k: int = 5) -> Dict:
        """Enhanced semantic search with summarization and key points"""
        query_embedding = self._compute_embedding(query)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT e.chunk_text, e.embedding, e.key_points,
                           w.url, w.title, w.summary
                    FROM embeddings e
                    JOIN web_content w ON e.content_id = w.id
                """)
                
                results = []
                for chunk_text, embedding_bytes, key_points, url, title, summary in cursor.fetchall():
                    embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
                    similarity = np.dot(query_embedding, embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
                    )
                    
                    results.append({
                        'chunk': chunk_text,
                        'url': url,
                        'title': title or 'Untitled',
                        'similarity': float(similarity),
                        'key_points': key_points.split('||') if key_points else [],
                        'summary': summary
                    })
                
                results.sort(key=lambda x: x['similarity'], reverse=True)
                top_results = results[:top_k]
                
                # Generate a combined summary for top results
                combined_text = ' '.join(r['chunk'] for r in top_results)
                overall_summary = self.generate_summary(combined_text)
                
                return {
                    'results': top_results,
                    'overall_summary': overall_summary
                }
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return {'results': [], 'overall_summary': ''}
        except Exception as e:
            print(f"Error during search: {e}")
            return {'results': [], 'overall_summary': ''}

    def _compute_embedding(self, text: str) -> np.ndarray:
        """Compute embedding for a piece of text"""
        embedding = self.embedding_model.encode(text)
        return embedding.astype(np.float32)

    def _chunk_text(self, text: str, chunk_size: int = 512) -> List[str]:
        """Split text into chunks while preserving sentence boundaries"""
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            if current_length + len(sentence) > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_length = len(sentence)
            else:
                current_chunk.append(sentence)
                current_length += len(sentence) + 1  # +1 for space
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks

    def store_content(self, content: WebContent):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Generate summary for the entire content
            summary = self.generate_summary(content.content)
            
            cursor.execute("""
                INSERT OR REPLACE INTO web_content 
                (url, content, timestamp, title, tags, summary)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                content.url,
                content.content,
                content.timestamp,
                content.metadata['title'],
                ','.join(content.metadata['tags']),
                summary
            ))
            content_id = cursor.lastrowid
            
            # Process and store chunks with key points
            chunks = self._chunk_text(content.content)
            for chunk in chunks:
                embedding = self._compute_embedding(chunk)
                key_points = self.extract_key_points(chunk)
                
                cursor.execute("""
                    INSERT INTO embeddings 
                    (content_id, chunk_text, embedding, key_points)
                    VALUES (?, ?, ?, ?)
                """, (
                    content_id, 
                    chunk, 
                    embedding.tobytes(),
                    '||'.join(key_points)
                ))
            
            conn.commit()

# Test function to verify everything works
def test_system():
    print("Testing AI Search System...")
    
    system = AISearchSystem()
    
    # Add test content
    test_content = WebContent(
        url="test://example",
        content="Artificial intelligence is revolutionizing technology. Machine learning models can now understand natural language and solve complex problems.",
        timestamp=datetime.now(),
        metadata={
            'title': "AI Test Content",
            'tags': ['AI', 'ML']
        }
    )
    
    print("Adding test content...")
    system.store_content(test_content)
    
    print("Testing search...")
    results = system.semantic_search("What is AI?")
    
    print("\nSearch results:")
    for result in results:
        print(f"Title: {result['title']}")
        print(f"Relevance: {result['similarity']:.2f}")
        print(f"Content: {result['chunk'][:100]}...\n")

if __name__ == "__main__":
    test_system()