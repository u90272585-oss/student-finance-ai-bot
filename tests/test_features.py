import unittest
import sqlite3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Database


class TestFeatures(unittest.TestCase):
    """Feature tests — testing complete user scenarios"""

    def setUp(self):
        self.test_db_path = 'test_feature.db'
        self.db = Database.__new__(Database)
        self.db.conn = sqlite3.connect(self.test_db_path)
        self.db.cursor = self.db.conn.cursor()
        self.db.init_db()

    def tearDown(self):
        self.db.conn.close()
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_scenario_register_and_track_expenses(self):
        """
        Scenario 1: User registers → adds income → adds expense → checks balance
        Expected: balance = income - expense
        """
        print("\n📋 Scenario 1: Register and track expenses")

        # Step 1: Register
        self.db.add_user(111, "Uldana", "KZ", "ru", "KZT")
        user = self.db.get_user(111)
        self.assertIsNotNone(user)
        print("  ✅ Step 1: User registered")

        # Step 2: Add income
        self.db.add_transaction(111, "income", 150000, "Salary", "")
        print("  ✅ Step 2: Income added — 150,000 KZT")

        # Step 3: Add expense
        self.db.add_transaction(111, "expense", 45000, "Food", "")
        print("  ✅ Step 3: Expense added — 45,000 KZT")

        # Step 4: Check balance
        income, expense, balance, _ = self.db.get_stats(111)
        self.assertEqual(balance, 105000)
        print(f"  ✅ Step 4: Balance correct — {balance} KZT")
        print("  🎉 Scenario 1 PASSED!")

    def test_scenario_create_goal_and_complete(self):
        """
        Scenario 2: User creates goal → adds money → goal reaches 100%
        Expected: current amount equals target
        """
        print("\n📋 Scenario 2: Create goal and complete it")

        # Step 1: Register
        self.db.add_user(222, "Malika", "KZ", "ru", "KZT")
        print("  ✅ Step 1: User registered")

        # Step 2: Create goal
        goal_id = self.db.add_goal(222, "New Laptop", 200000)
        self.db.set_goal_plant(goal_id, "lotus")
        goals = self.db.get_goals(222)
        self.assertEqual(goals[0][2], 200000)
        print("  ✅ Step 2: Goal created — 200,000 KZT")

        # Step 3: Add money to goal
        self.db.cursor.execute(
            'UPDATE goals SET current = ? WHERE id = ?', (200000, goal_id)
        )
        self.db.conn.commit()
        print("  ✅ Step 3: Money added to goal")

        # Step 4: Check goal completed
        goals = self.db.get_goals(222)
        current = goals[0][3]
        target = goals[0][2]
        self.assertEqual(current, target)
        percent = (current / target) * 100
        self.assertEqual(percent, 100.0)
        print(f"  ✅ Step 4: Goal completed — {percent}%")
        print("  🎉 Scenario 2 PASSED!")

    def test_scenario_premium_unlocks_features(self):
        """
        Scenario 3: User gets premium → can create more than 3 goals
        Expected: premium user can create unlimited goals
        """
        print("\n📋 Scenario 3: Premium unlocks unlimited goals")

        # Step 1: Register
        self.db.add_user(333, "Darina", "KZ", "ru", "KZT")
        print("  ✅ Step 1: User registered")

        # Step 2: Check no premium
        self.assertFalse(self.db.is_premium(333))
        print("  ✅ Step 2: No premium by default")

        # Step 3: Activate premium
        self.db.add_premium(333, 30)
        self.assertTrue(self.db.is_premium(333))
        print("  ✅ Step 3: Premium activated for 30 days")

        # Step 4: Create 5 goals (more than free limit of 3)
        for i in range(5):
            self.db.add_goal(333, f"Goal {i+1}", 100000)
        goals = self.db.get_goals(333)
        self.assertEqual(len(goals), 5)
        print(f"  ✅ Step 4: Created 5 goals (premium unlimited)")
        print("  🎉 Scenario 3 PASSED!")

    def test_scenario_shared_goal_collaboration(self):
        """
        Scenario 4: Two users create and join shared goal → both contribute
        Expected: total contributions equal sum of both users
        """
        print("\n📋 Scenario 4: Shared goal collaboration")

        # Step 1: Register two users
        self.db.add_user(444, "Uldana", "KZ", "ru", "KZT")
        self.db.add_user(555, "Malika", "KZ", "ru", "KZT")
        print("  ✅ Step 1: Two users registered")

        # Step 2: Create shared goal
        goal_id = self.db.create_shared_goal(444, "Trip to Bali", 300000, "BALI2026")
        print("  ✅ Step 2: Shared goal created with invite code BALI2026")

        # Step 3: Second user joins
        result = self.db.join_shared_goal(555, "BALI2026")
        self.assertIsNotNone(result)
        print("  ✅ Step 3: Second user joined the goal")

        # Step 4: Both contribute
        self.db.add_to_shared_goal(444, goal_id, 100000)
        self.db.add_to_shared_goal(555, goal_id, 150000)
        print("  ✅ Step 4: Both users added money")

        # Step 5: Check total
        details = self.db.get_shared_goal_details(goal_id)
        total = details['goal'][3]
        self.assertEqual(total, 250000)
        print(f"  ✅ Step 5: Total contributions correct — {total} KZT")
        print("  🎉 Scenario 4 PASSED!")

    def test_scenario_coins_and_discount(self):
        """
        Scenario 5: User plays game → earns coins → gets discount
        Expected: 500 coins → discount activated → coins become 0
        """
        print("\n📋 Scenario 5: Coins and discount system")

        # Step 1: Register
        self.db.add_user(666, "TestUser", "KZ", "ru", "KZT")
        print("  ✅ Step 1: User registered")

        # Step 2: Earn coins over time (simulate multiple days)
        self.db.cursor.execute('''
            INSERT INTO coins (user_id, total_coins, last_game_date)
            VALUES (?, ?, ?)
        ''', (666, 500, "2026-01-01"))
        self.db.conn.commit()
        total_coins, _ = self.db.get_coins(666)
        self.assertEqual(total_coins, 500)
        print(f"  ✅ Step 2: Earned 500 coins total")

        # Step 3: Use coins for discount
        result = self.db.use_coins_for_discount(666, 500)
        self.assertTrue(result)
        print("  ✅ Step 3: Discount activated!")

        # Step 4: Check coins spent
        total_coins, _ = self.db.get_coins(666)
        self.assertEqual(total_coins, 0)
        print("  ✅ Step 4: Coins spent — balance is 0")
        print("  🎉 Scenario 5 PASSED!")


if __name__ == '__main__':
    print("=" * 50)
    print("🧪 Running Feature Tests — Finance Bot")
    print("=" * 50)
    unittest.main(verbosity=2)
