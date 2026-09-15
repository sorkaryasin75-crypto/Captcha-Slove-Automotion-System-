import asyncio
import logging
import os
import aiohttp
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from twocaptcha import TwoCaptcha

# এনভায়রনমেন্ট ভ্যারিয়েবল থেকে কনফিগারেশন লোড
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY", "YOUR_2CAPTCHA_API_KEY")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
solver = TwoCaptcha(CAPTCHA_API_KEY)


def get_captcha_keyboard(status="ready"):
  """ডায়নামিক ইনলাইন কিবোর্ড জেনারেটর (Aiogram v3)"""
  if status == "ready":
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 অটো সলভ করুন", callback_data="solve_captcha"
                ),
                InlineKeyboardButton(
                    text="❌ বাতিল করুন", callback_data="cancel_task"
                ),
            ]
        ]
    )
  elif status == "processing":
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⏳ প্রসেসিং হচ্ছে...", callback_data="processing"
                )
            ]
        ]
    )
  return None


@dp.message(Command("start"))
async def start_command(message: types.Message):
  """বট স্টার্ট করার হ্যান্ডলার"""
  await message.answer(
      "🤖 *2Captcha মাস্টার অটোমেশন সিস্টেম (v3)*\n\n"
      "ক্যাপচা সলভ করতে একটি ইমেজ ক্যাপচা ফরোয়ার্ড করুন বা আপলোড করুন।",
      parse_mode="Markdown",
  )


@dp.message(F.photo)
async def handle_incoming_captcha(message: types.Message):
  """নতুন ক্যাপচা ইমেজ রিসিভ করে ইনলাইন কিবোর্ড সহ ইন্টারফেস তৈরি করবে"""
  photo_id = message.photo[-1].file_id

  await bot.send_photo(
      chat_id=message.chat.id,
      photo=photo_id,
      caption=(
          "📥 *নতুন ক্যাপচা সনাক্ত হয়েছে!*\nনিচের বোতামে ক্লিক করে অটো-সলভ শুরু"
          " করুন:"
      ),
      parse_mode="Markdown",
      reply_markup=get_captcha_keyboard("ready"),
  )


@dp.callback_query(F.data.in_(["solve_captcha", "cancel_task"]))
async def process_callback(callback_query: types.CallbackQuery):
  """ইনলাইন কিবোর্ডের রেসপন্স হ্যান্ডেল করা এবং ভ্যানিশ/ডিলিট সিস্টেম"""
  query_data = callback_query.data
  message = callback_query.message

  if query_data == "cancel_task":
    # ভ্যানিশ/ডিলিট সিস্টেম
    await message.delete()
    await bot.send_message(
        message.chat.id, "❌ ক্যাপচা সলভিং টাস্ক বাতিল করা হয়েছে।"
    )
    await callback_query.answer()
    return

  if query_data == "solve_captcha":
    # প্রসেসিং স্টেট আপডেট
    await message.edit_caption(
        caption="⏳ *2Captcha সার্ভারে পাঠানো হয়েছে, সলভ হচ্ছে...*",
        parse_mode="Markdown",
        reply_markup=get_captcha_keyboard("processing"),
    )

    try:
      # টেলিগ্রাম থেকে ছবি ডাউনলোড করা
      # Aiogram v3 অনুযায়ী ফাইল ইনফো ফেচ করা
      photo = message.photo[-1]
      file_info = await bot.get_file(photo.file_id)
      file_path = file_info.file_path

      image_name = f"captcha_{message.message_id}.jpg"
      await bot.download_file(file_path, destination=image_name)

      # 2Captcha এপিআই দিয়ে সলভ করা (এটি ব্লকড কল হতে পারে তাই রানারে দেওয়া নিরাপদ)
      result = solver.normal(image_name)
      solved_text = result.get("code")

      # লোকাল ফাইল ক্লিনআপ
      if os.path.exists(image_name):
        os.remove(image_name)

      # ভ্যানিশ ও ডিলিট সিস্টেম: আগের মেসেজটি রিমুভ করে দেওয়া
      await message.delete()

      # সফলভাবে সলভ হওয়ার পর রেজাল্ট পাঠানো
      success_kb = InlineKeyboardMarkup(
          inline_keyboard=[
              [
                  InlineKeyboardButton(
                      text="🔄 নতুন ক্যাপচার জন্য প্রস্তুত",
                      callback_data="new_task",
                  )
              ]
          ]
      )
      await bot.send_message(
          chat_id=message.chat.id,
          text=(
              f"✅ *ক্যাপচা সফলভাবে সলভ হয়েছে!* \n\n🔑 ফলাফল: `{solved_text}`"
          ),
          parse_mode="Markdown",
          reply_markup=success_kb,
      )

    except Exception as e:
      try:
        await message.edit_caption(
            caption=f"❌ সলভ করতে ব্যর্থ হয়েছে: {str(e)}", parse_mode="Markdown"
        )
      except:
        await bot.send_message(
            message.chat.id, f"❌ সলভ করতে ব্যর্থ হয়েছে: {str(e)}"
        )

  await callback_query.answer()


async def main():
  print("মাস্টার অটোমেশন বট রানিং (Aiogram v3)...")
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
