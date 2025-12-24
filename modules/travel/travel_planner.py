import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)

class TravelPlanner:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.storage_path = config.get('storage_path', 'data/travel.json')
        
        self.trips = {}
        self.packing_lists = {}
        self.destinations = {}
        
        if self.enabled:
            self._load_data()
        
        logger.info("TravelPlanner initialized")
    
    def _load_data(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.trips = data.get('trips', {})
                    self.packing_lists = data.get('packing_lists', {})
                    self.destinations = data.get('destinations', {})
                logger.info(f"Loaded {len(self.trips)} trips")
        except Exception as e:
            logger.error(f"Error loading travel data: {e}")
    
    def _save_data(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'trips': self.trips,
                    'packing_lists': self.packing_lists,
                    'destinations': self.destinations,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving travel data: {e}")
    
    def add_trip(self, destination: str, start_date: str, end_date: str = None,
                purpose: str = None, budget: float = None, notes: str = "") -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            trip_id = str(uuid.uuid4())[:8]
            
            self.trips[trip_id] = {
                'id': trip_id,
                'destination': destination,
                'start_date': start_date,
                'end_date': end_date,
                'purpose': purpose,
                'budget': budget,
                'expenses': [],
                'notes': notes,
                'status': 'planned',
                'itinerary': [],
                'accommodations': [],
                'transportation': [],
                'documents': [],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self._save_data()
            logger.info(f"Added trip to: {destination}")
            return self.trips[trip_id].copy()
            
        except Exception as e:
            logger.error(f"Error adding trip: {e}")
            return None
    
    def add_itinerary_item(self, trip_id: str, date: str, time: str, activity: str,
                          location: str = None, cost: float = None, notes: str = "") -> Optional[str]:
        if not self.enabled or trip_id not in self.trips:
            return None
        
        try:
            item_id = str(uuid.uuid4())[:8]
            
            item = {
                'id': item_id,
                'date': date,
                'time': time,
                'activity': activity,
                'location': location,
                'cost': cost,
                'notes': notes,
                'completed': False
            }
            
            self.trips[trip_id]['itinerary'].append(item)
            self.trips[trip_id]['updated_at'] = datetime.now().isoformat()
            self._save_data()
            logger.info(f"Added itinerary item: {activity}")
            return item_id
            
        except Exception as e:
            logger.error(f"Error adding itinerary item: {e}")
            return None
    
    def add_accommodation(self, trip_id: str, name: str, check_in: str, check_out: str = None,
                         address: str = None, confirmation: str = None, cost: float = None) -> Optional[str]:
        if not self.enabled or trip_id not in self.trips:
            return None
        
        try:
            acc_id = str(uuid.uuid4())[:8]
            
            accommodation = {
                'id': acc_id,
                'name': name,
                'check_in': check_in,
                'check_out': check_out,
                'address': address,
                'confirmation': confirmation,
                'cost': cost,
                'type': 'hotel'
            }
            
            self.trips[trip_id]['accommodations'].append(accommodation)
            self.trips[trip_id]['updated_at'] = datetime.now().isoformat()
            self._save_data()
            logger.info(f"Added accommodation: {name}")
            return acc_id
            
        except Exception as e:
            logger.error(f"Error adding accommodation: {e}")
            return None
    
    def create_packing_list(self, trip_id: str = None, name: str = "Packing List") -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            list_id = str(uuid.uuid4())[:8]
            
            self.packing_lists[list_id] = {
                'id': list_id,
                'trip_id': trip_id,
                'name': name,
                'items': [],
                'created_at': datetime.now().isoformat()
            }
            
            self._save_data()
            logger.info(f"Created packing list: {name}")
            return list_id
            
        except Exception as e:
            logger.error(f"Error creating packing list: {e}")
            return None
    
    def add_packing_item(self, list_id: str, item: str, quantity: int = 1,
                        category: str = None, packed: bool = False) -> bool:
        if not self.enabled or list_id not in self.packing_lists:
            return False
        
        try:
            item_id = str(uuid.uuid4())[:8]
            
            packing_item = {
                'id': item_id,
                'item': item,
                'quantity': quantity,
                'category': category,
                'packed': packed
            }
            
            self.packing_lists[list_id]['items'].append(packing_item)
            self._save_data()
            logger.info(f"Added packing item: {item}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding packing item: {e}")
            return False
    
    def mark_item_packed(self, list_id: str, item_id: str, packed: bool = True) -> bool:
        if not self.enabled or list_id not in self.packing_lists:
            return False
        
        try:
            for item in self.packing_lists[list_id]['items']:
                if item['id'] == item_id:
                    item['packed'] = packed
                    self._save_data()
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Error marking item packed: {e}")
            return False
    
    def add_expense(self, trip_id: str, category: str, amount: float,
                   description: str = "", date: str = None) -> Optional[str]:
        if not self.enabled or trip_id not in self.trips:
            return None
        
        try:
            expense_id = str(uuid.uuid4())[:8]
            expense_date = date or datetime.now().isoformat()
            
            expense = {
                'id': expense_id,
                'category': category,
                'amount': amount,
                'description': description,
                'date': expense_date
            }
            
            self.trips[trip_id]['expenses'].append(expense)
            self.trips[trip_id]['updated_at'] = datetime.now().isoformat()
            self._save_data()
            logger.info(f"Added expense: {category} - ${amount}")
            return expense_id
            
        except Exception as e:
            logger.error(f"Error adding expense: {e}")
            return None
    
    def get_trip(self, trip_id: str) -> Optional[Dict[str, Any]]:
        return self.trips.get(trip_id)
    
    def list_trips(self, status: str = None) -> List[Dict[str, Any]]:
        trips = list(self.trips.values())
        if status:
            trips = [t for t in trips if t['status'] == status]
        return sorted(trips, key=lambda x: x.get('start_date', ''), reverse=True)
    
    def get_upcoming_trips(self, days: int = 30) -> List[Dict[str, Any]]:
        upcoming = []
        cutoff = (datetime.now() + timedelta(days=days)).isoformat()
        
        for trip in self.trips.values():
            if trip.get('start_date') and trip['start_date'] <= cutoff:
                if trip['status'] != 'completed':
                    upcoming.append(trip)
        
        return sorted(upcoming, key=lambda x: x.get('start_date', ''))
    
    def get_trip_budget_summary(self, trip_id: str) -> Optional[Dict[str, Any]]:
        if trip_id not in self.trips:
            return None
        
        trip = self.trips[trip_id]
        total_expenses = sum(e['amount'] for e in trip['expenses'])
        budget = trip.get('budget', 0)
        
        return {
            'trip_id': trip_id,
            'destination': trip['destination'],
            'budget': budget,
            'total_expenses': total_expenses,
            'remaining': budget - total_expenses if budget else None,
            'expense_count': len(trip['expenses']),
            'by_category': self._group_expenses_by_category(trip['expenses'])
        }
    
    def _group_expenses_by_category(self, expenses: List[Dict]) -> Dict[str, float]:
        by_category = defaultdict(float)
        for expense in expenses:
            by_category[expense['category']] += expense['amount']
        return dict(by_category)
    
    def get_packing_list(self, list_id: str) -> Optional[Dict[str, Any]]:
        return self.packing_lists.get(list_id)
    
    def get_packing_progress(self, list_id: str) -> Optional[Dict[str, Any]]:
        if list_id not in self.packing_lists:
            return None
        
        items = self.packing_lists[list_id]['items']
        total = len(items)
        packed = sum(1 for item in items if item['packed'])
        
        return {
            'list_id': list_id,
            'total_items': total,
            'packed_items': packed,
            'remaining': total - packed,
            'progress_percent': (packed / total * 100) if total > 0 else 0
        }
    
    def search_trips(self, query: str) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        results = []
        
        for trip in self.trips.values():
            if (query_lower in trip['destination'].lower() or
                query_lower in trip.get('notes', '').lower() or
                query_lower in trip.get('purpose', '').lower()):
                results.append(trip)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        total_trips = len(self.trips)
        total_packing_lists = len(self.packing_lists)
        
        upcoming = len(self.get_upcoming_trips(30))
        
        statuses = defaultdict(int)
        for trip in self.trips.values():
            statuses[trip['status']] += 1
        
        total_budget = sum(t.get('budget', 0) or 0 for t in self.trips.values())
        total_expenses = sum(
            sum(e['amount'] for e in t['expenses'])
            for t in self.trips.values()
        )
        
        return {
            'total_trips': total_trips,
            'upcoming_trips': upcoming,
            'by_status': dict(statuses),
            'total_packing_lists': total_packing_lists,
            'total_budget': total_budget,
            'total_expenses': total_expenses
        }
    def get_all_trips(self):
        return self.list_trips()

    
    
    def delete_trip(self, trip_id: str) -> bool:
        if not self.enabled or trip_id not in self.trips:
            return False
        del self.trips[trip_id]
        self._save_data()
        return True
