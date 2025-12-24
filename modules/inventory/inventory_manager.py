import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)

class InventoryManager:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.storage_path = config.get('storage_path', 'data/inventory.json')
        
        self.items = {}
        self.locations = {}
        self.categories = set(['Electronics', 'Furniture', 'Appliances', 'Tools', 'Clothing', 'Other'])
        
        if self.enabled:
            self._load_data()
        
        logger.info("InventoryManager initialized")
    
    def _load_data(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.items = data.get('items', {})
                    self.locations = data.get('locations', {})
                    self.categories = set(data.get('categories', list(self.categories)))
                logger.info(f"Loaded {len(self.items)} inventory items")
        except Exception as e:
            logger.error(f"Error loading inventory data: {e}")
    
    def _save_data(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'items': self.items,
                    'locations': self.locations,
                    'categories': list(self.categories),
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving inventory data: {e}")
    
    def add_item(self, name: str, category: str = None, location: str = None,
                quantity: int = 1, purchase_date: str = None, purchase_price: float = None,
                warranty_expiry: str = None, serial_number: str = None,
                model: str = None, notes: str = "") -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            item_id = str(uuid.uuid4())[:8]
            
            if category:
                self.categories.add(category)
            
            self.items[item_id] = {
                'id': item_id,
                'name': name,
                'category': category,
                'location': location,
                'quantity': quantity,
                'purchase_date': purchase_date,
                'purchase_price': purchase_price,
                'warranty_expiry': warranty_expiry,
                'serial_number': serial_number,
                'model': model,
                'notes': notes,
                'condition': 'good',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'tags': []
            }
            
            self._save_data()
            logger.info(f"Added inventory item: {name}")
            return self.items[item_id].copy()
            
        except Exception as e:
            logger.error(f"Error adding item: {e}")
            return None
    
    def update_item(self, item_id: str, **updates) -> bool:
        if not self.enabled or item_id not in self.items:
            return False
        
        try:
            for key, value in updates.items():
                if key in self.items[item_id]:
                    self.items[item_id][key] = value
            
            self.items[item_id]['updated_at'] = datetime.now().isoformat()
            self._save_data()
            logger.info(f"Updated item: {item_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating item: {e}")
            return False
    
    def delete_item(self, item_id: str) -> bool:
        if not self.enabled or item_id not in self.items:
            return False
        
        try:
            del self.items[item_id]
            self._save_data()
            logger.info(f"Deleted item: {item_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting item: {e}")
            return False
    
    def add_location(self, name: str, description: str = "") -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            location_id = str(uuid.uuid4())[:8]
            
            self.locations[location_id] = {
                'id': location_id,
                'name': name,
                'description': description,
                'created_at': datetime.now().isoformat()
            }
            
            self._save_data()
            logger.info(f"Added location: {name}")
            return location_id
            
        except Exception as e:
            logger.error(f"Error adding location: {e}")
            return None
    
    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        return self.items.get(item_id)
    
    def list_items(self, category: str = None, location: str = None) -> List[Dict[str, Any]]:
        items = list(self.items.values())
        
        if category:
            items = [i for i in items if i.get('category') == category]
        if location:
            items = [i for i in items if i.get('location') == location]
        
        return sorted(items, key=lambda x: x.get('name', ''))
    
    def search_items(self, query: str) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        results = []
        
        for item in self.items.values():
            if (query_lower in item['name'].lower() or
                query_lower in item.get('model', '').lower() or
                query_lower in item.get('serial_number', '').lower() or
                query_lower in item.get('notes', '').lower()):
                results.append(item)
        
        return results
    
    def get_items_by_location(self, location: str) -> List[Dict[str, Any]]:
        return [i for i in self.items.values() if i.get('location') == location]
    
    def get_expiring_warranties(self, days: int = 60) -> List[Dict[str, Any]]:
        expiring = []
        now = datetime.now()
        cutoff = now + timedelta(days=days)
        
        for item in self.items.values():
            if not item.get('warranty_expiry'):
                continue
            
            try:
                expiry_date = datetime.fromisoformat(item['warranty_expiry'][:10])
                if now <= expiry_date <= cutoff:
                    days_until = (expiry_date - now).days
                    item_copy = item.copy()
                    item_copy['days_until_expiry'] = days_until
                    expiring.append(item_copy)
            except:
                pass
        
        return sorted(expiring, key=lambda x: x['warranty_expiry'])
    
    def get_total_value(self) -> float:
        total = 0.0
        for item in self.items.values():
            if item.get('purchase_price'):
                total += item['purchase_price'] * item.get('quantity', 1)
        return round(total, 2)
    
    def get_value_by_category(self) -> Dict[str, float]:
        by_category = defaultdict(float)
        
        for item in self.items.values():
            if item.get('purchase_price'):
                category = item.get('category', 'Uncategorized')
                value = item['purchase_price'] * item.get('quantity', 1)
                by_category[category] += value
        
        return {k: round(v, 2) for k, v in by_category.items()}
    
    def get_value_by_location(self) -> Dict[str, float]:
        by_location = defaultdict(float)
        
        for item in self.items.values():
            if item.get('purchase_price'):
                location = item.get('location', 'Unknown')
                value = item['purchase_price'] * item.get('quantity', 1)
                by_location[location] += value
        
        return {k: round(v, 2) for k, v in by_location.items()}
    
    def get_stats(self) -> Dict[str, Any]:
        total_items = len(self.items)
        total_quantity = sum(i.get('quantity', 1) for i in self.items.values())
        total_value = self.get_total_value()
        
        by_category = defaultdict(int)
        by_location = defaultdict(int)
        by_condition = defaultdict(int)
        
        for item in self.items.values():
            if item.get('category'):
                by_category[item['category']] += 1
            if item.get('location'):
                by_location[item['location']] += 1
            by_condition[item.get('condition', 'unknown')] += 1
        
        items_with_warranty = sum(1 for i in self.items.values() if i.get('warranty_expiry'))
        expiring_soon = len(self.get_expiring_warranties(60))
        
        return {
            'total_items': total_items,
            'total_quantity': total_quantity,
            'total_value': total_value,
            'by_category': dict(by_category),
            'by_location': dict(by_location),
            'by_condition': dict(by_condition),
            'total_locations': len(self.locations),
            'items_with_warranty': items_with_warranty,
            'warranties_expiring_soon': expiring_soon
        }
    def get_all_items(self):
        return self.list_items()

    
    
