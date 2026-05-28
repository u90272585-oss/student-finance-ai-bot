import psycopg2
from datetime import datetime

# Твоя публичная строка подключения
DATABASE_URL = "postgresql://postgres:imegfwFZfoDoobfAPBYHXPBELylmdUlj@switchyard.proxy.rlwy.net:10435/railway"

try:
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    
    cur.execute('''
        SELECT 
            u.user_id, 
            u.name, 
            u.language, 
            u.currency, 
            DATE(u.created_at) as reg_date,
            p.premium_until as premium_until
        FROM users u
        LEFT JOIN premium_users p ON u.user_id = p.user_id
        ORDER BY u.created_at DESC
    ''')
    users = cur.fetchall()
    conn.close()
    
    # Подсчитываем премиум
    premium_count = 0
    for user in users:
        premium_until = user[5]
        if premium_until:
            try:
                if premium_until > datetime.now():
                    premium_count += 1
            except:
                pass
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Finance Bot — База данных</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
        }}
        h1 {{
            color: #2c3e50;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin-top: 20px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        .premium-yes {{
            color: green;
            font-weight: bold;
        }}
        .premium-no {{
            color: gray;
        }}
        .stats {{
            background-color: #e8f4f8;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <h1>📊 Finance Bot — База данных</h1>
    <p>Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
    
    <div class="stats">
        <b>📈 Статистика:</b><br>
        👥 Всего пользователей: {len(users)}<br>
        💎 Активный премиум: {premium_count}<br>
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
        </tr>'''
    
    for user in users:
        user_id, name, language, currency, reg_date, premium_until = user
        
        # Проверяем активный премиум
        is_premium = False
        premium_until_str = "—"
        if premium_until:
            try:
                if premium_until > datetime.now():
                    is_premium = True
                    premium_until_str = premium_until.strftime('%d.%m.%Y')
            except:
                premium_until_str = "—"
        
        premium_status = "✅ Да" if is_premium else "❌ Нет"
        premium_class = "premium-yes" if is_premium else "premium-no"
        
        html += f'''
        <tr>
            <td>{user_id}</td>
            <td>{name or "—"}</td>
            <td>{language}</td>
            <td>{currency}</td>
            <td>{reg_date}</td>
            <td class="{premium_class}">{premium_status}</td>
            <td>{premium_until_str}</td>
        </tr>'''
    
    html += '''
    </table>
</body>
</html>'''
    
    with open('railway_users.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Готово! Найдено пользователей: {len(users)}")
    print("📁 Открой файл: railway_users.html")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")