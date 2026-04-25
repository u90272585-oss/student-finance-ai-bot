import unittest
import sqlite3
import os
import sys
from datetime import datetime, timedelta

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Database


class TestDatabase(unittest.TestCase):
    """Unit tests for Database class"""

    def setUp(self):
        """Create a test database before each test"""
        self.test_db_path = 'test_finance.db'
        self.db = Database.__new__(Database)
        self.db.conn = sqlite3.connect(self.test_db_path)
        self.db.cursor = self.db.conn.cursor()
        self.db.init_db()

    def tearDown(self):
        """Delete test database after each test"""
        self.db.conn.close()
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    # ========== USER TESTS ==========

    def test_add_user(self):
        """Test: user is correctly saved to database"""
        result = self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        user = self.db.get_user(123456)
        self.assertIsNotNone(user)
        self.assertEqual(user[0], 123456)
        self.assertEqual(user[1], "TestUser")
        self.assertEqual(user[3], "ru")
        print("✅ test_add_user passed")

    def test_get_user_not_found(self):
        """Test: returns None for non-existing user"""
        user = self.db.get_user(999999)
        self.assertIsNone(user)
        print("✅ test_get_user_not_found passed")

    def test_update_language(self):
        """Test: language is correctly updated"""
        self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        self.db.update_language(123456, "en")
        user = self.db.get_user(123456)
        self.assertEqual(user[3], "en")
        print("✅ test_update_language passed")

    def test_update_currency(self):
        """Test: currency is correctly updated"""
        self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        self.db.update_currency(123456, "USD")
        user = self.db.get_user(123456)
        self.assertEqual(user[4], "USD")
        print("✅ test_update_currency passed")

    # ========== TRANSACTION TESTS ==========

    def test_add_transaction(self):
        """Test: transaction is correctly saved"""
        self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        self.db.add_transaction(123456, "income", 50000, "Salary", "Monthly salary")
        transactions = self.db.get_all_transactions(123456)
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0][2], 50000)
        self.assertEqual(transactions[0][1], "income")
        print("✅ test_add_transaction passed")

    def test_get_stats_balance(self):
        """Test: balance is calculated correctly (income - expense)"""
        self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        self.db.add_transaction(123456, "income", 100000, "Salary", "")
        self.db.add_transaction(123456, "expense", 30000, "Food", "")
        income, expense, balance, _ = self.db.get_stats(123456)
        self.assertEqual(income, 100000)
        self.assertEqual(expense, 30000)
        self.assertEqual(balance, 70000)
        print("✅ test_get_stats_balance passed")

    def test_get_stats_empty(self):
        """Test: stats return 0 for user with no transactions"""
        self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        income, expense, balance, _ = self.db.get_stats(123456)
        self.assertEqual(income, 0)
        self.assertEqual(expense, 0)
        self.assertEqual(balance, 0)
        print("✅ test_get_stats_empty passed")

    # ========== GOAL TESTS ==========

    def test_add_goal(self):
        """Test: goal is created with correct target amount"""
        self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        goal_id = self.db.add_goal(123456, "New iPhone", 500000)
        goals = self.db.get_goals(123456)
        self.assertEqual(len(goals), 1)
        self.assertEqual(goals[0][2], 500000)
        self.assertEqual(goals[0][1], "New iPhone")
        print("✅ test_add_goal passed")

    def test_delete_goal(self):
        """Test: goal is correctly deleted"""
        self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        goal_id = self.db.add_goal(123456, "Test Goal", 100000)
        self.db.delete_goal(goal_id)
        goals = self.db.get_goals(123456)
        self.assertEqual(len(goals), 0)
        print("✅ test_delete_goal passed")

    def test_goal_plant(self):
        """Test: plant type is correctly set and retrieved"""
        self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        goal_id = self.db.add_goal(123456, "Test Goal", 100000)
        self.db.set_goal_plant(goal_id, "rose")
        plant = self.db.get_goal_plant(goal_id)
        self.assertEqual(plant, "rose")
        print("✅ test_goal_plant passed")

    # ========== PREMIUM TESTS ==========

    def test_add_premium(self):
        """Test: premium is correctly activated"""
        self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        self.db.add_premium(123456, 30)
        self.assertTrue(self.db.is_premium(123456))
        print("✅ test_add_premium passed")

    def test_remove_premium(self):
        """Test: premium is correctly removed"""
        self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        self.db.add_premium(123456, 30)
        self.db.remove_premium(123456)
        self.assertFalse(self.db.is_premium(123456))
        print("✅ test_remove_premium passed")

    def test_is_premium_false_by_default(self):
        """Test: user has no premium by default"""
        self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        self.assertFalse(self.db.is_premium(123456))
        print("✅ test_is_premium_false_by_default passed")

    # ========== COINS TESTS ==========

    def test_add_coins(self):
        """Test: coins are correctly added after game"""
        self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        self.db.add_coins(123456, 25)
        total_coins, _ = self.db.get_coins(123456)
        self.assertEqual(total_coins, 25)
        print("✅ test_add_coins passed")

    def test_coins_accumulate(self):
        """Test: coins accumulate correctly over multiple games"""
        self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        self.db.add_coins(123456, 25)
        self.db.add_coins(123456, 30)
        total_coins, _ = self.db.get_coins(123456)
        self.assertEqual(total_coins, 55)
        print("✅ test_coins_accumulate passed")

    def test_can_play_today(self):
        """Test: user can play if they haven't played today"""
        self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        self.assertTrue(self.db.can_play_today(123456))
        print("✅ test_can_play_today passed")

    def test_cannot_play_twice_today(self):
        """Test: user cannot play twice in one day"""
        self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        self.db.add_coins(123456, 25)  # This sets last_game_date to today
        self.assertFalse(self.db.can_play_today(123456))
        print("✅ test_cannot_play_twice_today passed")

    def test_use_coins_for_discount(self):
        """Test: coins are correctly spent for discount"""
        self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        self.db.add_coins(123456, 500)
        result = self.db.use_coins_for_discount(123456, 500)
        self.assertTrue(result)
        total_coins, _ = self.db.get_coins(123456)
        self.assertEqual(total_coins, 0)
        print("✅ test_use_coins_for_discount passed")

    def test_use_coins_insufficient(self):
        """Test: discount fails if not enough coins"""
        self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        self.db.add_coins(123456, 100)
        result = self.db.use_coins_for_discount(123456, 500)
        self.assertFalse(result)
        print("✅ test_use_coins_insufficient passed")

    # ========== SHARED GOALS TESTS ==========

    def test_create_shared_goal(self):
        """Test: shared goal is correctly created"""
        self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        goal_id = self.db.create_shared_goal(123456, "Trip to Bali", 500000, "ABC12345")
        self.assertIsNotNone(goal_id)
        print("✅ test_create_shared_goal passed")

    def test_join_shared_goal(self):
        """Test: user can join shared goal with invite code"""
        self.db.add_user(123456, "Creator", "KZ", "ru", "KZT")
        self.db.add_user(789012, "Joiner", "KZ", "ru", "KZT")
        self.db.create_shared_goal(123456, "Trip to Bali", 500000, "ABC12345")
        result = self.db.join_shared_goal(789012, "ABC12345")
        self.assertIsNotNone(result)
        self.assertNotEqual(result, "already_member")
        print("✅ test_join_shared_goal passed")

    def test_join_shared_goal_invalid_code(self):
        """Test: joining with invalid code returns None"""
        self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT")
        result = self.db.join_shared_goal(123456, "INVALID1")
        self.assertIsNone(result)
        print("✅ test_join_shared_goal_invalid_code passed")


if __name__ == '__main__':
    print("=" * 50)
    print("🧪 Running Unit Tests — Finance Bot Database")
    print("=" * 50)
    unittest.main(verbosity=2)