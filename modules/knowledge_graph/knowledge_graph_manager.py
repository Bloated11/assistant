import logging
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

class KnowledgeGraphManager:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.storage_path = config.get('storage_path', 'data/knowledge_graph.json')
        
        self.entities = {}
        self.relationships = []
        self.entity_types = set()
        self.relationship_types = set()
        
        if self.enabled:
            self._load_graph()
        
        logger.info("KnowledgeGraphManager initialized")
    
    def _load_graph(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.entities = data.get('entities', {})
                    self.relationships = data.get('relationships', [])
                    self.entity_types = set(data.get('entity_types', []))
                    self.relationship_types = set(data.get('relationship_types', []))
                logger.info(f"Loaded {len(self.entities)} entities and {len(self.relationships)} relationships")
        except Exception as e:
            logger.error(f"Error loading knowledge graph: {e}")
    
    def _save_graph(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'entities': self.entities,
                    'relationships': self.relationships,
                    'entity_types': list(self.entity_types),
                    'relationship_types': list(self.relationship_types),
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving knowledge graph: {e}")
    
    def add_entity(self, name: str, entity_type: str, properties: Dict[str, Any] = None) -> bool:
        if not self.enabled:
            return False
        
        try:
            entity_id = self._generate_entity_id(name, entity_type)
            
            self.entities[entity_id] = {
                'id': entity_id,
                'name': name,
                'type': entity_type,
                'properties': properties or {},
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self.entity_types.add(entity_type)
            self._save_graph()
            
            logger.info(f"Added entity: {name} ({entity_type})")
            return True
            
        except Exception as e:
            logger.error(f"Error adding entity: {e}")
            return False
    
    def add_relationship(self, from_entity: str, relationship_type: str, to_entity: str, properties: Dict[str, Any] = None) -> bool:
        if not self.enabled:
            return False
        
        try:
            from_id = self._find_entity_id(from_entity)
            to_id = self._find_entity_id(to_entity)
            
            if not from_id or not to_id:
                logger.warning(f"Entity not found: {from_entity} or {to_entity}")
                return False
            
            relationship = {
                'from': from_id,
                'type': relationship_type,
                'to': to_id,
                'properties': properties or {},
                'created_at': datetime.now().isoformat()
            }
            
            self.relationships.append(relationship)
            self.relationship_types.add(relationship_type)
            self._save_graph()
            
            logger.info(f"Added relationship: {from_entity} -{relationship_type}-> {to_entity}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding relationship: {e}")
            return False
    
    def _generate_entity_id(self, name: str, entity_type: str) -> str:
        base_id = f"{entity_type}_{name}".lower().replace(' ', '_')
        return base_id
    
    def _find_entity_id(self, name: str) -> Optional[str]:
        name_lower = name.lower()
        
        for entity_id, entity in self.entities.items():
            if entity['name'].lower() == name_lower:
                return entity_id
        
        return None
    
    def get_entity(self, name: str) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        entity_id = self._find_entity_id(name)
        if entity_id:
            return self.entities.get(entity_id)
        
        return None
    
    def get_relationships(self, entity_name: str, direction: str = 'both') -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        entity_id = self._find_entity_id(entity_name)
        if not entity_id:
            return []
        
        results = []
        
        for rel in self.relationships:
            if direction in ['from', 'both'] and rel['from'] == entity_id:
                to_entity = self.entities.get(rel['to'], {})
                results.append({
                    'direction': 'outgoing',
                    'type': rel['type'],
                    'entity': to_entity.get('name'),
                    'entity_type': to_entity.get('type'),
                    'properties': rel.get('properties', {})
                })
            
            if direction in ['to', 'both'] and rel['to'] == entity_id:
                from_entity = self.entities.get(rel['from'], {})
                results.append({
                    'direction': 'incoming',
                    'type': rel['type'],
                    'entity': from_entity.get('name'),
                    'entity_type': from_entity.get('type'),
                    'properties': rel.get('properties', {})
                })
        
        return results
    
    def find_path(self, from_entity: str, to_entity: str, max_depth: int = 3) -> Optional[List[Dict[str, Any]]]:
        if not self.enabled:
            return None
        
        from_id = self._find_entity_id(from_entity)
        to_id = self._find_entity_id(to_entity)
        
        if not from_id or not to_id:
            return None
        
        visited = set()
        queue = [(from_id, [])]
        
        while queue:
            current_id, path = queue.pop(0)
            
            if len(path) >= max_depth:
                continue
            
            if current_id == to_id:
                return path
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            for rel in self.relationships:
                if rel['from'] == current_id:
                    next_id = rel['to']
                    next_entity = self.entities.get(next_id, {})
                    new_path = path + [{
                        'from': self.entities[current_id]['name'],
                        'type': rel['type'],
                        'to': next_entity.get('name')
                    }]
                    queue.append((next_id, new_path))
        
        return None
    
    def query_by_type(self, entity_type: str) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        results = []
        for entity in self.entities.values():
            if entity['type'] == entity_type:
                results.append(entity)
        
        return results
    
    def search_entities(self, query: str) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        query_lower = query.lower()
        results = []
        
        for entity in self.entities.values():
            if query_lower in entity['name'].lower():
                results.append(entity)
            elif any(query_lower in str(v).lower() for v in entity.get('properties', {}).values()):
                results.append(entity)
        
        return results
    
    def get_context(self, entity_name: str, depth: int = 1) -> Dict[str, Any]:
        if not self.enabled:
            return {}
        
        entity = self.get_entity(entity_name)
        if not entity:
            return {}
        
        context = {
            'entity': entity,
            'relationships': {},
            'related_entities': []
        }
        
        rels = self.get_relationships(entity_name)
        
        rel_by_type = defaultdict(list)
        for rel in rels:
            rel_by_type[rel['type']].append(rel)
        
        context['relationships'] = dict(rel_by_type)
        
        related_ids = set()
        for rel in rels:
            related_name = rel['entity']
            related_entity = self.get_entity(related_name)
            if related_entity:
                context['related_entities'].append(related_entity)
                related_ids.add(related_entity['id'])
        
        if depth > 1:
            for related_name in list(related_ids):
                sub_rels = self.get_relationships(related_name)
                for sub_rel in sub_rels:
                    if sub_rel['entity'] not in related_ids and sub_rel['entity'] != entity_name:
                        sub_entity = self.get_entity(sub_rel['entity'])
                        if sub_entity:
                            context['related_entities'].append(sub_entity)
        
        return context
    
    def delete_entity(self, name: str) -> bool:
        if not self.enabled:
            return False
        
        entity_id = self._find_entity_id(name)
        if not entity_id:
            return False
        
        del self.entities[entity_id]
        
        self.relationships = [
            rel for rel in self.relationships
            if rel['from'] != entity_id and rel['to'] != entity_id
        ]
        
        self._save_graph()
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        if not self.enabled:
            return {'enabled': False}
        
        return {
            'enabled': True,
            'entity_count': len(self.entities),
            'relationship_count': len(self.relationships),
            'entity_types': list(self.entity_types),
            'relationship_types': list(self.relationship_types),
            'entity_type_counts': {
                et: len(self.query_by_type(et)) for et in self.entity_types
            }
        }
    
    def export_graph(self, format: str = 'json') -> str:
        if format == 'json':
            return json.dumps({
                'entities': self.entities,
                'relationships': self.relationships
            }, indent=2)
        
        elif format == 'cypher':
            cypher_statements = []
            
            for entity in self.entities.values():
                props = ', '.join([f"{k}: '{v}'" for k, v in entity.get('properties', {}).items()])
                cypher_statements.append(
                    f"CREATE (:{entity['type']} {{name: '{entity['name']}', {props}}})"
                )
            
            for rel in self.relationships:
                from_entity = self.entities[rel['from']]
                to_entity = self.entities[rel['to']]
                cypher_statements.append(
                    f"MATCH (a {{name: '{from_entity['name']}'}}), (b {{name: '{to_entity['name']}'}}) "
                    f"CREATE (a)-[:{rel['type'].upper().replace(' ', '_')}]->(b)"
                )
            
            return '\n'.join(cypher_statements)
        
        return ""
