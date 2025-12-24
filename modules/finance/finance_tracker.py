import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)

class FinanceTracker:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.storage_path = config.get('storage_path', 'data/finances.json')
        self.currency = config.get('currency', 'USD')
        
        self.transactions = {}
        self.budgets = {}
        self.categories = set(['Food', 'Transport', 'Entertainment', 'Bills', 'Shopping', 'Income', 'Other'])
        
        if self.enabled:
            self._load_data()
        
        logger.info("FinanceTracker initialized")
    
    def _load_data(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.transactions = data.get('transactions', {})
                    self.budgets = data.get('budgets', {})
                    self.categories = set(data.get('categories', list(self.categories)))
                logger.info(f"Loaded {len(self.transactions)} transactions")
        except Exception as e:
            logger.error(f"Error loading finance data: {e}")
    
    def _save_data(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'transactions': self.transactions,
                    'budgets': self.budgets,
                    'categories': list(self.categories),
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving finance data: {e}")
    
    def add_expense(self, amount: float, category: str, description: str = "", 
                   date: str = None, payment_method: str = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        return self._add_transaction('expense', amount, category, description, date, payment_method)
    
    def add_income(self, amount: float, source: str, description: str = "",
                  date: str = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        return self._add_transaction('income', amount, source, description, date)
    
    def _add_transaction(self, trans_type: str, amount: float, category: str,
                        description: str = "", date: str = None, payment_method: str = None) -> Optional[str]:
        try:
            trans_id = str(uuid.uuid4())[:8]
            trans_date = date or datetime.now().isoformat()
            
            if category:
                self.categories.add(category)
            
            self.transactions[trans_id] = {
                'id': trans_id,
                'type': trans_type,
                'amount': float(amount),
                'category': category,
                'description': description,
                'date': trans_date,
                'payment_method': payment_method,
                'created_at': datetime.now().isoformat()
            }
            
            self._save_data()
            logger.info(f"Added {trans_type}: {amount} {self.currency} in {category}")
            return trans_id
            
        except Exception as e:
            logger.error(f"Error adding transaction: {e}")
            return None
    
    def delete_transaction(self, trans_id: str) -> bool:
        if not self.enabled or trans_id not in self.transactions:
            return False
        
        del self.transactions[trans_id]
        self._save_data()
        return True
    
    def set_budget(self, category: str, amount: float, period: str = "monthly") -> bool:
        if not self.enabled:
            return False
        
        try:
            self.categories.add(category)
            
            self.budgets[category] = {
                'category': category,
                'amount': float(amount),
                'period': period,
                'created_at': datetime.now().isoformat()
            }
            
            self._save_data()
            logger.info(f"Set {period} budget for {category}: {amount} {self.currency}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting budget: {e}")
            return False
    
    def get_budget_status(self, category: str = None, period_days: int = 30) -> Dict[str, Any]:
        if not self.enabled:
            return {'enabled': False}
        
        if category:
            return self._get_category_budget_status(category, period_days)
        else:
            return self._get_all_budgets_status(period_days)
    
    def _get_category_budget_status(self, category: str, period_days: int) -> Dict[str, Any]:
        if category not in self.budgets:
            return {'category': category, 'has_budget': False}
        
        budget = self.budgets[category]
        budget_amount = budget['amount']
        
        cutoff_date = (datetime.now() - timedelta(days=period_days)).isoformat()
        spent = sum(
            t['amount'] for t in self.transactions.values()
            if t['type'] == 'expense' and t['category'] == category and t['date'] >= cutoff_date
        )
        
        remaining = budget_amount - spent
        percentage = (spent / budget_amount * 100) if budget_amount > 0 else 0
        
        return {
            'category': category,
            'has_budget': True,
            'budget': budget_amount,
            'spent': round(spent, 2),
            'remaining': round(remaining, 2),
            'percentage': round(percentage, 1),
            'period': budget['period'],
            'status': 'over' if spent > budget_amount else 'warning' if percentage > 80 else 'good'
        }
    
    def _get_all_budgets_status(self, period_days: int) -> Dict[str, Any]:
        statuses = {}
        for category in self.budgets.keys():
            statuses[category] = self._get_category_budget_status(category, period_days)
        return statuses
    
    def get_summary(self, period_days: int = 30) -> Dict[str, Any]:
        if not self.enabled:
            return {'enabled': False}
        
        cutoff_date = (datetime.now() - timedelta(days=period_days)).isoformat()
        
        total_income = sum(
            t['amount'] for t in self.transactions.values()
            if t['type'] == 'income' and t['date'] >= cutoff_date
        )
        
        total_expenses = sum(
            t['amount'] for t in self.transactions.values()
            if t['type'] == 'expense' and t['date'] >= cutoff_date
        )
        
        net_balance = total_income - total_expenses
        
        expense_by_category = defaultdict(float)
        for t in self.transactions.values():
            if t['type'] == 'expense' and t['date'] >= cutoff_date:
                expense_by_category[t['category']] += t['amount']
        
        top_categories = sorted(
            expense_by_category.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        transaction_count = sum(
            1 for t in self.transactions.values()
            if t['date'] >= cutoff_date
        )
        
        return {
            'enabled': True,
            'period_days': period_days,
            'total_income': round(total_income, 2),
            'total_expenses': round(total_expenses, 2),
            'net_balance': round(net_balance, 2),
            'transaction_count': transaction_count,
            'top_categories': [(cat, round(amt, 2)) for cat, amt in top_categories],
            'currency': self.currency
        }
    
    def get_category_breakdown(self, period_days: int = 30) -> Dict[str, float]:
        if not self.enabled:
            return {}
        
        cutoff_date = (datetime.now() - timedelta(days=period_days)).isoformat()
        
        breakdown = defaultdict(float)
        for t in self.transactions.values():
            if t['type'] == 'expense' and t['date'] >= cutoff_date:
                breakdown[t['category']] += t['amount']
        
        return {cat: round(amt, 2) for cat, amt in sorted(breakdown.items(), key=lambda x: x[1], reverse=True)}
    
    def get_recent_transactions(self, limit: int = 10, trans_type: str = None) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        transactions = list(self.transactions.values())
        
        if trans_type:
            transactions = [t for t in transactions if t['type'] == trans_type]
        
        transactions.sort(key=lambda x: x['date'], reverse=True)
        
        return transactions[:limit]
    
    def search_transactions(self, category: str = None, description: str = None,
                           min_amount: float = None, max_amount: float = None,
                           start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        results = []
        
        for trans in self.transactions.values():
            if category and trans['category'] != category:
                continue
            
            if description and description.lower() not in trans.get('description', '').lower():
                continue
            
            if min_amount and trans['amount'] < min_amount:
                continue
            
            if max_amount and trans['amount'] > max_amount:
                continue
            
            if start_date and trans['date'] < start_date:
                continue
            
            if end_date and trans['date'] > end_date:
                continue
            
            results.append(trans)
        
        return sorted(results, key=lambda x: x['date'], reverse=True)
    
    def get_monthly_trend(self, months: int = 6) -> Dict[str, Dict[str, float]]:
        if not self.enabled:
            return {}
        
        trend = defaultdict(lambda: {'income': 0.0, 'expenses': 0.0, 'net': 0.0})
        
        for trans in self.transactions.values():
            trans_date = datetime.fromisoformat(trans['date'])
            month_key = trans_date.strftime('%Y-%m')
            
            if trans['type'] == 'income':
                trend[month_key]['income'] += trans['amount']
            else:
                trend[month_key]['expenses'] += trans['amount']
        
        for month_data in trend.values():
            month_data['net'] = month_data['income'] - month_data['expenses']
        
        sorted_months = sorted(trend.keys(), reverse=True)[:months]
        
        return {
            month: {
                'income': round(trend[month]['income'], 2),
                'expenses': round(trend[month]['expenses'], 2),
                'net': round(trend[month]['net'], 2)
            }
            for month in sorted_months
        }
    
    def add_category(self, category: str) -> bool:
        if not self.enabled:
            return False
        
        self.categories.add(category)
        self._save_data()
        return True
    
    def get_categories(self) -> List[str]:
        if not self.enabled:
            return []
        
        return sorted(list(self.categories))
    
    def get_stats(self) -> Dict[str, Any]:
        if not self.enabled:
            return {'enabled': False}
        
        total_transactions = len(self.transactions)
        total_expenses = sum(1 for t in self.transactions.values() if t['type'] == 'expense')
        total_incomes = sum(1 for t in self.transactions.values() if t['type'] == 'income')
        
        all_time_income = sum(t['amount'] for t in self.transactions.values() if t['type'] == 'income')
        all_time_expenses = sum(t['amount'] for t in self.transactions.values() if t['type'] == 'expense')
        
        return {
            'enabled': True,
            'total_transactions': total_transactions,
            'total_expenses': total_expenses,
            'total_incomes': total_incomes,
            'all_time_income': round(all_time_income, 2),
            'all_time_expenses': round(all_time_expenses, 2),
            'all_time_net': round(all_time_income - all_time_expenses, 2),
            'active_budgets': len(self.budgets),
            'total_categories': len(self.categories),
            'currency': self.currency
        }
    def add_transaction(self, transaction_type: str, amount: float, category: str, description: str = ""):
        return self.create_transaction(transaction_type, amount, category, description)

    def add_transaction(self, transaction_type: str, amount: float, category: str, description: str = "") -> Dict[str, Any]:
        success = self.log_transaction(transaction_type, amount, category, description)
        if success:
            for trans_id, trans in self.transactions.items():
                if (trans['type'] == transaction_type and trans['amount'] == amount and 
                    trans['category'] == category and trans['description'] == description):
                    trans['id'] = trans_id
                    return trans
        return None
    
    def delete_transaction(self, transaction_id: str) -> bool:
        if not self.enabled or transaction_id not in self.transactions:
            return False
        del self.transactions[transaction_id]
        self._save_data()
        return True

    def add_transaction(self, transaction_type: str, amount: float, category: str, description: str = "") -> Dict[str, Any]:
        if transaction_type.lower() == 'expense':
            trans_id = self.add_expense(amount, category, description)
        elif transaction_type.lower() == 'income':
            trans_id = self.add_income(amount, category, description)
        else:
            trans_id = self._add_transaction(transaction_type, amount, category, description)
        if trans_id:
            return self.transactions[trans_id].copy()
        return None

