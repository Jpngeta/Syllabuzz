# Description: ModuleManager class for handling module operations
from bson.objectid import ObjectId
from datetime import datetime

class ModuleManager:
    def __init__(self, db, embedding_service=None):
        self.db = db
        self.embedding_service = embedding_service
        
    def create_module(self, name, code, description, keywords):
        """Create a new module"""
        module = {
            'name': name,
            'code': code,
            'description': description,
            'keywords': keywords,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        # Generate vector embedding if embedding service available
        if self.embedding_service:
            module_text = ' '.join(keywords) + ' ' + description
            embedding = self.embedding_service.generate_embedding(module_text)
            module['vector_embedding'] = embedding.tolist()
            
        module_id = self.db.modules.insert_one(module).inserted_id
        return module_id
        
    def get_modules(self, limit=100):
        """Get all modules"""
        return list(self.db.modules.find().limit(limit))
        
    def get_module(self, module_id):
        """Get a single module"""
        return self.db.modules.find_one({'_id': ObjectId(module_id)})
        
    def update_module(self, module_id, updates):
        """Update a module"""
        # Don't allow direct updates to embeddings
        if 'vector_embedding' in updates:
            del updates['vector_embedding']
            
        updates['updated_at'] = datetime.now()
        
        # Update the module
        result = self.db.modules.update_one(
            {'_id': ObjectId(module_id)},
            {'$set': updates}
        )
        
        # Regenerate embedding if keywords or description changed
        if 'keywords' in updates or 'description' in updates:
            module = self.db.modules.find_one({'_id': ObjectId(module_id)})
            if module and self.embedding_service:
                module_text = ' '.join(module['keywords']) + ' ' + module.get('description', '')
                embedding = self.embedding_service.generate_embedding(module_text)
                self.db.modules.update_one(
                    {'_id': ObjectId(module_id)},
                    {'$set': {'vector_embedding': embedding.tolist()}}
                )
                
        return result.modified_count > 0
        
    def delete_module(self, module_id):
        """Delete a module"""
        # Remove from users' modules list
        self.db.users.update_many(
            {'modules': ObjectId(module_id)},
            {'$pull': {'modules': ObjectId(module_id)}}
        )
        
        # Delete module-article relevance scores
        self.db.module_article_relevance.delete_many({'module_id': ObjectId(module_id)})
        
        # Delete module
        result = self.db.modules.delete_one({'_id': ObjectId(module_id)})
        return result.deleted_count > 0
        
    def add_module_to_user(self, user_id, module_id):
        """Add a module to a user's list"""
        result = self.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$addToSet': {'modules': ObjectId(module_id)}}
        )
        return result.modified_count > 0
        
    def remove_module_from_user(self, user_id, module_id):
        """Remove a module from a user's list"""
        result = self.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$pull': {'modules': ObjectId(module_id)}}
        )
        return result.modified_count > 0