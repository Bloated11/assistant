import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)

class MealPlanner:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.storage_path = config.get('storage_path', 'data/meals.json')
        
        self.recipes = {}
        self.meal_plans = {}
        self.shopping_lists = {}
        self.meal_logs = {}
        
        if self.enabled:
            self._load_data()
        
        logger.info("MealPlanner initialized")
    
    def _load_data(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.recipes = data.get('recipes', {})
                    self.meal_plans = data.get('meal_plans', {})
                    self.shopping_lists = data.get('shopping_lists', {})
                    self.meal_logs = data.get('meal_logs', {})
                logger.info(f"Loaded {len(self.recipes)} recipes")
        except Exception as e:
            logger.error(f"Error loading meal data: {e}")
    
    def _save_data(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'recipes': self.recipes,
                    'meal_plans': self.meal_plans,
                    'shopping_lists': self.shopping_lists,
                    'meal_logs': self.meal_logs,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving meal data: {e}")
    
    def add_recipe(self, name: str, ingredients: List[str], instructions: str = "",
                  prep_time: int = None, cook_time: int = None, servings: int = None,
                  category: str = None, cuisine: str = None, tags: List[str] = None,
                  calories: int = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            recipe_id = str(uuid.uuid4())[:8]
            
            self.recipes[recipe_id] = {
                'id': recipe_id,
                'name': name,
                'ingredients': ingredients,
                'instructions': instructions,
                'prep_time': prep_time,
                'cook_time': cook_time,
                'total_time': (prep_time or 0) + (cook_time or 0) if prep_time or cook_time else None,
                'servings': servings,
                'category': category,
                'cuisine': cuisine,
                'tags': tags or [],
                'calories': calories,
                'created_at': datetime.now().isoformat(),
                'favorite': False,
                'times_made': 0
            }
            
            self._save_data()
            logger.info(f"Added recipe: {name}")
            return recipe_id
            
        except Exception as e:
            logger.error(f"Error adding recipe: {e}")
            return None
    
    def create_meal_plan(self, name: str, start_date: str, days: int = 7) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            plan_id = str(uuid.uuid4())[:8]
            
            self.meal_plans[plan_id] = {
                'id': plan_id,
                'name': name,
                'start_date': start_date,
                'days': days,
                'meals': {},
                'created_at': datetime.now().isoformat(),
                'active': True
            }
            
            self._save_data()
            logger.info(f"Created meal plan: {name}")
            return plan_id
            
        except Exception as e:
            logger.error(f"Error creating meal plan: {e}")
            return None
    
    def add_meal_to_plan(self, plan_id: str, date: str, meal_type: str, 
                        recipe_id: str = None, meal_name: str = None) -> bool:
        if not self.enabled or plan_id not in self.meal_plans:
            return False
        
        try:
            if date not in self.meal_plans[plan_id]['meals']:
                self.meal_plans[plan_id]['meals'][date] = {}
            
            meal_data = {
                'type': meal_type,
                'recipe_id': recipe_id,
                'meal_name': meal_name or (self.recipes[recipe_id]['name'] if recipe_id else ""),
                'added_at': datetime.now().isoformat()
            }
            
            self.meal_plans[plan_id]['meals'][date][meal_type] = meal_data
            
            self._save_data()
            logger.info(f"Added {meal_type} to plan {plan_id} for {date}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding meal to plan: {e}")
            return False
    
    def log_meal(self, meal_type: str, meal_name: str, calories: int = None,
                notes: str = "", date: str = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            log_id = str(uuid.uuid4())[:8]
            meal_date = date or datetime.now().isoformat()
            
            self.meal_logs[log_id] = {
                'id': log_id,
                'type': meal_type,
                'meal_name': meal_name,
                'calories': calories,
                'notes': notes,
                'date': meal_date,
                'created_at': datetime.now().isoformat()
            }
            
            self._save_data()
            logger.info(f"Logged meal: {meal_type} - {meal_name}")
            return log_id
            
        except Exception as e:
            logger.error(f"Error logging meal: {e}")
            return None
    
    def create_shopping_list(self, name: str, items: List[str] = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            list_id = str(uuid.uuid4())[:8]
            
            self.shopping_lists[list_id] = {
                'id': list_id,
                'name': name,
                'items': {},
                'created_at': datetime.now().isoformat(),
                'completed': False
            }
            
            if items:
                for item in items:
                    item_id = str(uuid.uuid4())[:8]
                    self.shopping_lists[list_id]['items'][item_id] = {
                        'id': item_id,
                        'name': item,
                        'checked': False
                    }
            
            self._save_data()
            logger.info(f"Created shopping list: {name}")
            return list_id
            
        except Exception as e:
            logger.error(f"Error creating shopping list: {e}")
            return None
    
    def add_to_shopping_list(self, list_id: str, item: str, quantity: str = None) -> bool:
        if not self.enabled or list_id not in self.shopping_lists:
            return False
        
        try:
            item_id = str(uuid.uuid4())[:8]
            
            self.shopping_lists[list_id]['items'][item_id] = {
                'id': item_id,
                'name': item,
                'quantity': quantity,
                'checked': False
            }
            
            self._save_data()
            logger.info(f"Added '{item}' to shopping list")
            return True
            
        except Exception as e:
            logger.error(f"Error adding to shopping list: {e}")
            return False
    
    def check_shopping_item(self, list_id: str, item_id: str, checked: bool = True) -> bool:
        if not self.enabled or list_id not in self.shopping_lists:
            return False
        
        try:
            if item_id in self.shopping_lists[list_id]['items']:
                self.shopping_lists[list_id]['items'][item_id]['checked'] = checked
                self._save_data()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error checking shopping item: {e}")
            return False
    
    def search_recipes(self, query: str = None, category: str = None, 
                      cuisine: str = None, max_time: int = None) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        try:
            results = list(self.recipes.values())
            
            if query:
                query_lower = query.lower()
                results = [r for r in results if query_lower in r['name'].lower()
                          or any(query_lower in ing.lower() for ing in r['ingredients'])]
            
            if category:
                results = [r for r in results if r.get('category') == category]
            
            if cuisine:
                results = [r for r in results if r.get('cuisine') == cuisine]
            
            if max_time:
                results = [r for r in results if r.get('total_time') 
                          and r['total_time'] <= max_time]
            
            return sorted(results, key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error searching recipes: {e}")
            return []
    
    def get_recipe(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        if not self.enabled or recipe_id not in self.recipes:
            return None
        return self.recipes[recipe_id].copy()
    
    def get_meal_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        if not self.enabled or plan_id not in self.meal_plans:
            return None
        
        plan = self.meal_plans[plan_id].copy()
        
        for date, meals in plan['meals'].items():
            for meal_type, meal in meals.items():
                if meal.get('recipe_id') and meal['recipe_id'] in self.recipes:
                    meal['recipe'] = self.recipes[meal['recipe_id']]
        
        return plan
    
    def get_shopping_list(self, list_id: str) -> Optional[Dict[str, Any]]:
        if not self.enabled or list_id not in self.shopping_lists:
            return None
        
        shopping_list = self.shopping_lists[list_id].copy()
        items = list(shopping_list['items'].values())
        
        shopping_list['total_items'] = len(items)
        shopping_list['checked_items'] = len([i for i in items if i['checked']])
        shopping_list['unchecked_items'] = len([i for i in items if not i['checked']])
        
        return shopping_list
    
    def get_todays_meals(self) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        today = datetime.now().date().isoformat()
        meals = []
        
        for plan in self.meal_plans.values():
            if plan['active'] and today in plan['meals']:
                for meal_type, meal in plan['meals'][today].items():
                    meals.append({
                        'type': meal_type,
                        'meal_name': meal['meal_name'],
                        'recipe_id': meal.get('recipe_id'),
                        'from_plan': plan['name']
                    })
        
        return meals
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            'enabled': self.enabled,
            'total_recipes': len(self.recipes),
            'total_meal_plans': len(self.meal_plans),
            'active_meal_plans': len([p for p in self.meal_plans.values() if p['active']]),
            'total_shopping_lists': len(self.shopping_lists),
            'total_meal_logs': len(self.meal_logs)
        }
    def get_all_meals(self) -> List[Dict[str, Any]]:
        meals_list = []
        for meal_id, meal in self.meals.items():
            meal_copy = meal.copy()
            meal_copy['id'] = meal_id
            meals_list.append(meal_copy)
        return meals_list
    
    def delete_meal(self, meal_id: str) -> bool:
        if not self.enabled or meal_id not in self.meals:
            return False
        del self.meals[meal_id]
        self._save_data()
        return True



    def add_meal(self, name: str, meal_type: str, recipe: str = None, **kwargs):
        log_id = self.log_meal(meal_type, name, **kwargs)
        if log_id:
            return self.meal_logs[log_id].copy()
        return None
    
    @property
    def meals(self):
        return self.meal_logs
