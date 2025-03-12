from sentence_transformers import SentenceTransformer
import numpy as np

class EmbeddingService:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        
    def generate_embedding(self, text):
        """Generate embedding for a single text"""
        return self.model.encode(text)
        
    def generate_embeddings(self, texts):
        """Generate embeddings for multiple texts"""
        return self.model.encode(texts)
        
    def get_module_embedding(self, module):
        """Generate an embedding for a module based on its keywords and description"""
        module_text = ' '.join(module['keywords']) + ' ' + module.get('description', '')
        return self.model.encode(module_text)
        
    def calculate_similarity(self, embedding1, embedding2):
        """Calculate cosine similarity between two embeddings"""
        return np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))