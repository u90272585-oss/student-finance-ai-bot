import unittest
import sqlite3
import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Database


class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.test_db_path = 'test_finance.db'
        self.db = Database.__new__(Database)
        self.db.use_postgres = False
        self.db.pool = None
        self.db.conn = sqlite3.connect(self.test_db_path)
        self.db.cursor = self.db.conn.cursor()
        self.db._init_sqlite()

    def tearDown(self):
        self.db.conn.close()
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def run_async(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_add_user(self):
        self.run_async(self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT"))
        user = self.run_async(self.db.get_user(123456))
        self.assertIsNotNone(user)
        self.assertEqual(user[0], 123456)

    def test_get_user_not_found(self):
        user = self.run_async(self.db.get_user(999999))
        self.assertIsNone(user)

    def test_update_language(self):
        self.run_async(self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT"))
        self.run_async(self.db.update_language(123456, "en"))
        user = self.run_async(self.db.get_user(123456))
        self.assertEqual(user[3], "en")

    def test_update_currency(self):
        self.run_async(self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT"))
        self.run_async(self.db.update_currency(123456, "USD"))
        user = self.run_async(self.db.get_user(123456))
        self.assertEqual(user[4], "USD")

    def test_add_transaction(self):
        self.run_async(self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT"))
        self.run_async(self.db.add_transaction(123456, "income", 50000, "Salary", ""))
        transactions = self.run_async(self.db.get_all_transactions(123456))
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0][2], 50000)

    def test_get_stats_balance(self):
        self.run_async(self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT"))
        self.run_async(self.db.add_transaction(123456, "income", 100000, "Salary", ""))
        self.run_async(self.db.add_transaction(123456, "expense", 30000, "Food", ""))
        income, expense, balance, _ = self.run_async(self.db.get_stats(123456))
        self.assertEqual(income, 100000)
        self.assertEqual(expense, 30000)
        self.assertEqual(balance, 70000)

    def test_get_stats_empty(self):
        self.run_async(self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT"))
        income, expense, balance, _ = self.run_async(self.db.get_stats(123456))
        self.assertEqual(income, 0)
        self.assertEqual(expense, 0)

    def test_add_goal(self):
        self.run_async(self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT"))
        self.run_async(self.db.add_goal(123456, "New iPhone", 500000))
        goals = self.run_async(self.db.get_goals(123456))
        self.assertEqual(len(goals), 1)
        self.assertEqual(goals[0][1], "New iPhone")

    def test_delete_goal(self):
        self.run_async(self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT"))
        goal_id = self.run_async(self.db.add_goal(123456, "Test Goal", 100000))
        self.run_async(self.db.delete_goal(goal_id))
        goals = self.run_async(self.db.get_goals(123456))
        self.assertEqual(len(goals), 0)

    def test_goal_plant(self):
        self.run_async(self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT"))
        goal_id = self.run_async(self.db.add_goal(123456, "Test Goal", 100000))
        self.run_async(self.db.set_goal_plant(goal_id, "rose"))
        plant = self.run_async(self.db.get_goal_plant(goal_id))
        self.assertEqual(plant, "rose")

    def test_add_premium(self):
        self.run_async(self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT"))
        self.run_async(self.db.add_premium(123456, 30))
        self.assertTrue(self.run_async(self.db.is_premium(123456)))

    def test_remove_premium(self):
        self.run_async(self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT"))
        self.run_async(self.db.add_premium(123456, 30))
        self.run_async(self.db.remove_premium(123456))
        self.assertFalse(self.run_async(self.db.is_premium(123456)))

    def test_is_premium_false_by_default(self):
        self.run_async(self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT"))
        self.assertFalse(self.run_async(self.db.is_premium(123456)))

    def test_add_coins(self):
        self.run_async(self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT"))
        self.run_async(self.db.add_coins(123456, 25))
        total_coins, _ = self.run_async(self.db.get_coins(123456))
        self.assertEqual(total_coins, 25)

    def test_coins_accumulate(self):
        self.run_async(self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT"))
        self.run_async(self.db.add_coins(123456, 25))
        self.run_async(self.db.add_coins(123456, 30))
        total_coins, _ = self.run_async(self.db.get_coins(123456))
        self.assertEqual(total_coins, 55)

    def test_can_play_today(self):
        self.run_async(self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT"))
        self.assertTrue(self.run_async(self.db.can_play_today(123456)))

    def test_cannot_play_twice_today(self):
        self.run_async(self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT"))
        self.run_async(self.db.add_coins(123456, 25))
        self.assertFalse(self.run_async(self.db.can_play_today(123456)))

    def test_use_coins_for_discount(self):
        self.run_async(self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT"))
        self.run_async(self.db.add_coins(123456, 500))
        result = self.run_async(self.db.use_coins_for_discount(123456, 500))
        self.assertTrue(result)
        total_coins, _ = self.run_async(self.db.get_coins(123456))
        self.assertEqual(total_coins, 0)

    def test_use_coins_insufficient(self):
        self.run_async(self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT"))
        self.run_async(self.db.add_coins(123456, 100))
        result = self.run_async(self.db.use_coins_for_discount(123456, 500))
        self.assertFalse(result)

    def test_create_shared_goal(self):
        self.run_async(self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT"))
        goal_id = self.run_async(self.db.create_shared_goal(123456, "Trip to Bali", 500000, "ABC12345"))
        self.assertIsNotNone(goal_id)

    def test_join_shared_goal(self):
        self.run_async(self.db.add_user(123456, "Creator", "KZ", "ru", "KZT"))
        self.run_async(self.db.add_user(789012, "Joiner", "KZ", "ru", "KZT"))
        self.run_async(self.db.create_shared_goal(123456, "Trip to Bali", 500000, "ABC12345"))
        result = self.run_async(self.db.join_shared_goal(789012, "ABC12345"))
        self.assertIsNotNone(result)

    def test_join_shared_goal_invalid_code(self):
        self.run_async(self.db.add_user(123456, "TestUser", "KZ", "ru", "KZT"))
        result = self.run_async(self.db.join_shared_goal(123456, "INVALID1"))
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
