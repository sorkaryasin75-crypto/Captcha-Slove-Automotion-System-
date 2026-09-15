import dotenv from 'dotenv';
dotenv.config();

import express, { Request, Response } from 'express';
import { Telegraf, Markup } from 'telegraf';
import { Pool } from 'pg';

const app = express();
app.use(express.json());

// PostgreSQL কানেকশন পুল কনফিগারেশন
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

const token = process.env.TELEGRAM_BOT_TOKEN || '';
const bot = new Telegraf(token);

// ০. মূল রুট এন্ডপয়েন্ট (Railway কন্টেইনার হেলথ চেক নিশ্চিত করতে এটি প্রয়োজন)
app.get('/', (req: Request, res: Response) => {
  res.status(200).send('Telegram CAPTCHA Bot is active and running!');
});

// ১. হেলথ চেক এন্ডপয়েন্ট
app.get('/health', (req: Request, res: Response) => {
  res.status(200).json({ status: 'HEALTHY', timestamp: new Date().toISOString() });
});

// ২. রেডিনেস চেক এন্ডপয়েন্ট (ডাটাবেস কানেকশন যাচাইকরণ)
app.get('/ready', async (req: Request, res: Response) => {
  try {
    await pool.query('SELECT 1');
    res.status(200).json({ status: 'READY' });
  } catch (error) {
    console.error('Database readiness check failed:', error);
    res.status(500).json({ status: 'NOT_READY', error: 'Database connection failed' });
  }
});

// ৩. টেলিগ্রাম ওয়েবহুক রুট
app.post('/telegram/webhook', async (req: Request, res: Response) => {
  try {
    await bot.handleUpdate(req.body);
    res.status(200).send('OK');
  } catch (err) {
    console.error('Webhook Error:', err);
    res.status(500).send('Internal Server Error');
  }
});

// ৪. বট কমান্ড ও ইনলাইন কিবোর্ড ইন্টারফেস ডিজাইন
bot.start(async (ctx) => {
  const telegramUserId = ctx.from?.id;
  const username = ctx.from?.username || '';
  const displayName = `${ctx.from?.first_name || ''} ${ctx.from?.last_name || ''}`.trim();

  if (telegramUserId) {
    try {
      await pool.query(
        `INSERT INTO users (telegram_user_id, username, display_name) 
         VALUES ($1, $2, $3) 
         ON CONFLICT (telegram_user_id) 
         DO UPDATE SET last_active_at = CURRENT_TIMESTAMP`,
        [telegramUserId, username, displayName]
      );
    } catch (dbErr) {
      console.error('Database insert error on start:', dbErr);
    }
  }

  await ctx.reply(
    '🤖 *মাস্টার ম্যানুয়াল ক্যাপচা প্ল্যাটফর্মে স্বাগতম!*\n\nদয়া করে নিচের মেনু থেকে আপনার কাজটি নির্বাচন করুন:',
    {
      parse_mode: 'Markdown',
      ...Markup.inlineKeyboard([
        [Markup.button.callback('▶ Start Work', 'start_work'), Markup.button.callback('🧩 Current Task', 'current_task')],
        [Markup.button.callback('💰 Balance', 'check_balance'), Markup.button.callback('📊 Statistics', 'show_stats')],
        [Markup.button.callback('📜 Work History', 'work_history'), Markup.button.callback('⚙ Settings', 'settings')],
        [Markup.button.callback('❌ Stop Work', 'stop_work')]
      ])
    }
  );
});

bot.action('check_balance', async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.editMessageText(
    '💰 *অ্যাকাউন্ট ব্যালেন্স স্ট্যাটাস*\n\nStatus: Active\nAvailable Balance: `$1.5400 USD`\nLast Synced: Just now',
    {
      parse_mode: 'Markdown',
      ...Markup.inlineKeyboard([[Markup.button.callback('🔙 মূল মেনুতে ফিরুন', 'main_menu')]])
    }
  );
});

bot.action('main_menu', async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.editMessageText(
    '🤖 *মাস্টার ম্যানুয়াল ক্যাপচা প্ল্যাটফর্ম*\n\nআপনার অপশন নির্বাচন করুন:',
    {
      parse_mode: 'Markdown',
      ...Markup.inlineKeyboard([
        [Markup.button.callback('▶ Start Work', 'start_work'), Markup.button.callback('🧩 Current Task', 'current_task')],
        [Markup.button.callback('💰 Balance', 'check_balance'), Markup.button.callback('📊 Statistics', 'show_stats')],
        [Markup.button.callback('📜 Work History', 'work_history'), Markup.button.callback('⚙ Settings', 'settings')],
        [Markup.button.callback('❌ Stop Work', 'stop_work')]
      ])
    }
  );
});

// ৫. সার্ভার স্টার্ট
const PORT = Number(process.env.PORT) || 3000;

app.listen(PORT, '0.0.0.0', async () => {
  console.log(`Server is running and listening on port ${PORT}`);
  
  if (process.env.NODE_ENV === 'production' && process.env.WEBHOOK_URL) {
    try {
      await bot.telegram.setWebhook(`${process.env.WEBHOOK_URL}/telegram/webhook`);
      console.log('Telegram webhook configured successfully.');
    } catch (whErr) {
      console.error('Failed to set Telegram webhook:', whErr);
    }
  }
});
