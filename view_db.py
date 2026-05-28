import sqlite3
from datetime import datetime

conn = sqlite3.connect('finance.db')
cursor = conn.cursor()

# Получаем данные
cursor.execute("""
    SELECT u.user_id, u.name, u.language, u.currency, u.created_at,
           CASE WHEN p.premium_until > datetime('now') THEN '✅ Да' ELSE '❌ Нет' END as premium,
           p.premium_until
    FROM users u
    LEFT JOIN premium_users p ON u.user_id = p.user_id
    ORDER BY u.created_at DESC
""")
users = cursor.fetchall()

cursor.execute("SELECT COUNT(*) FROM users")
total_users = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM premium_users WHERE premium_until > datetime('now')")
total_premium = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM transactions")
total_transactions = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM goals")
total_goals = cursor.fetchone()[0]

now = datetime.now().strftime('%d.%m.%Y %H:%M')

html = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Finance Bot - База данных</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        h1 {{ color: #333; }}
        .stats {{ display: flex; gap: 20px; margin-bottom: 30px; flex-wrap: wrap; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 10px; 
                      box-shadow: 0 2px 5px rgba(0,0,0,0.1); min-width: 150px; text-align: center; }}
        .stat-card h2 {{ margin: 0; font-size: 36px; color: #4CAF50; }}
        .stat-card p {{ margin: 5px 0 0; color: #666; }}
        table {{ width: 100%; border-collapse: collapse; background: white; 
                 border-radius: 10px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        th {{ background: #4CAF50; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #eee; }}
        tr:hover {{ background: #f9f9f9; }}
        .premium-yes {{ color: green; font-weight: bold; }}
        .premium-no {{ color: #999; }}
        .updated {{ color: #999; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <h1>📊 Finance Bot — База данных</h1>
    <p class="updated">Обновлено: {now}</p>

    <div class="stats">
        <div class="stat-card">
            <h2>{total_users}</h2>
            <p>👥 Пользователей</p>
        </div>
        <div class="stat-card">
            <h2>{total_premium}</h2>
            <p>💎 Премиум</p>
        </div>
        <div class="stat-card">
            <h2>{total_transactions}</h2>
            <p>💰 Транзакций</p>
        </div>
        <div class="stat-card">
            <h2>{total_goals}</h2>
            <p>🎯 Целей</p>
        </div>
    </div>

    <h2>👥 Пользователи</h2>
    <table>
        <tr>
            <th>ID</th>
            <th>Имя</th>
            <th>Язык</th>
            <th>Валюта</th>
            <th>Дата регистрации</th>
            <th>Премиум</th>
            <th>Премиум до</th>
        </tr>
"""

for user in users:
    user_id, name, language, currency, created_at, premium, premium_until = user
    premium_class = "premium-yes" if premium == "✅ Да" else "premium-no"
    premium_date = premium_until[:10] if premium_until else "—"
    
    html += f"""
        <tr>
            <td>{user_id}</td>
            <td>{name or '—'}</td>
            <td>{language}</td>
            <td>{currency}</td>
            <td>{created_at[:10] if created_at else '—'}</td>
            <td class="{premium_class}">{premium}</td>
            <td>{premium_date}</td>
        </tr>
    """

html += """
    </table>
</body>
</html>
"""

with open('users_report.html', 'w', encoding='utf-8') as f:
    f.write(html)

conn.close()
print(f"✅ Файл users_report.html создан! Пользователей: {total_users}")
#open users_report.html