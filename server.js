import express from 'express';
import dotenv from 'dotenv';
import fetch from 'node-fetch';
dotenv.config();

const app = express();
app.use(express.json());
app.use(express.static('.'));

// === ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ ТОКЕНА ===
async function getAccessToken() {
    const credentials = Buffer.from(
        `${process.env.PAYPAL_CLIENT_ID}:${process.env.PAYPAL_CLIENT_SECRET}`
    ).toString('base64');

    const tokenRes = await fetch('https://api-m.sandbox.paypal.com/v1/oauth2/token', {
        method: 'POST',
        headers: {
            Authorization: `Basic ${credentials}`,
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'grant_type=client_credentials',
    });

    const { access_token } = await tokenRes.json();
    return access_token;
}

// === ЭНДПОИНТ: СОЗДАНИЕ ЗАКАЗА ===
app.post('/api/orders', async (req, res) => {
    try {
        const accessToken = await getAccessToken();
        const { amount, currency, description } = req.body;

        const orderRes = await fetch('https://api-m.sandbox.paypal.com/v2/checkout/orders', {
            method: 'POST',
            headers: {
                Authorization: `Bearer ${accessToken}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                intent: 'CAPTURE',
                purchase_units: [{
                    amount: {
                        currency_code: currency || 'USD',
                        value: amount || '2.90',
                    },
                    description: description || 'CoinMind Premium',
                }],
                application_context: {
                    return_url: 'http://localhost:3000/landing/success.html',
                    cancel_url: 'http://localhost:3000/landing/home.html',
                },
            }),
        });

        const order = await orderRes.json();

        if (order.error) {
            console.error('PayPal error:', order.error);
            return res.status(400).json({ error: order.error.message });
        }

        res.json({ id: order.id });
    } catch (error) {
        console.error('Ошибка создания заказа:', error);
        res.status(500).json({ error: 'Не удалось создать заказ' });
    }
});

// === ЭНДПОИНТ: ПОДТВЕРЖДЕНИЕ ОПЛАТЫ ===
app.post('/api/orders/:orderID/capture', async (req, res) => {
    console.log('📥 Запрос на создание заказа получен!');  // ← ВОТ ЗДЕСЬ
    try {
        const accessToken = await getAccessToken();
        const { orderID } = req.params;

        const captureRes = await fetch(
            `https://api-m.sandbox.paypal.com/v2/checkout/orders/${orderID}/capture`,
            {
                method: 'POST',
                headers: {
                    Authorization: `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            }
        );

        const captureData = await captureRes.json();

        if (captureData.error) {
            console.error('PayPal capture error:', captureData.error);
            return res.status(400).json({ error: captureData.error.message });
        }

        res.json(captureData);
    } catch (error) {
        console.error('Ошибка подтверждения оплаты:', error);
        res.status(500).json({ error: 'Не удалось подтвердить оплату' });
    }
});

// === ЗАПУСК СЕРВЕРА ===
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`🚀 Server running on http://localhost:${PORT}`);
    console.log(`📱 Open: http://localhost:${PORT}/landing/payment.html`);
});