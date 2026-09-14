import logging
import os
import time
import requests
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from twocaptcha import TwoCaptcha

# এনভায়রনমেন্ট ভ্যারিয়েবল থেকে কনফিগারেশন লোড
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY", "YOUR_2CAPTCHA_API_KEY")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)
solver = TwoCaptcha(CAPTCHA_API_KEY)


def get_captcha_keyboard(status="ready"):
  """ডায়নামিক ইনলাইন কিবোর্ড জেনারেটর"""
  keyboard = InlineKeyboardMarkup(row_width=2)
  if status == "ready":
    keyboard.add(
        InlineKeyboardButton("🚀 অটো সলভ করুন", callback_data="solve_captcha"),
        InlineKeyboardButton("❌ বাতিল করুন", callback_data="cancel_task"),
    )
  elif status == "processing":
    keyboard.add(
        InlineKeyboardButton(
            "⏳ প্রসেসিং হচ্ছে...", callback_data="processing"
        )
    )
  return keyboard


@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
  """বট স্টার্ট করার হ্যান্ডলার"""
  await message.reply(
      "🤖 *2Captcha মাস্টার অটোমেশন সিস্টেম*\n\n"
      "ক্যাপচা সলভ করতে একটি ইমেজ ক্যাপচা ফরোয়ার্ড করুন বা আপলোড করুন।",
      parse_mode="Markdown",
  )


@dp.message_handler(content_types=[types.ContentType.PHOTO])
async def handle_incoming_captcha(message: types.Message):
  """নতুন ক্যাপচা ইমেজ রিসিভ করে ইনলাইন কিবোর্ড সহ ইন্টারফেস তৈরি করবে"""
  photo_id = message.photo[-1].file_id

  # ক্যাপচার সাথে ইনলাইন কিবোর্ড যুক্ত করে মেসেজ পাঠানো
  await bot.send_photo(
      chat_id=message.chat.id,
      photo=photo_id,
      caption=(
          "📥 *নতুন ক্যাপচা সনাক্ত হয়েছে!*\nনিচের বোটনে ক্লিক করে অটো-সলভ শুরু"
          " করুন:"
      ),
      parse_mode="Markdown",
      reply_markup=get_captcha_keyboard("ready"),
  )


@dp.callback_query_handler(
    lambda c: c.data in ["solve_captcha", "cancel_task"]
)
async def process_callback(callback_query: types.CallbackQuery):
  """ইনলাইন কিবোর্ডের রেসপন্স হ্যান্ডেল করা এবং ভ্যানিশ/ডিলিট সিস্টেম"""
  query_data = callback_query.data
  message = callback_query.message

  if query_data == "cancel_task":
    # ভ্যানিশ/ডিলিট সিস্টেম: টাস্ক বাতিল হলে মেসেজ ডিলিট হবে
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    await bot.send_message(
        message.chat.id, "❌ ক্যাপচা সলভিং টাস্ক বাতিল করা হয়েছে।"
    )
    return

  if query_data == "solve_captcha":
    # প্রসেসিং স্টেট আপডেট (ইনলাইন কিবোর্ড পরিবর্তন)
    await bot.edit_message_caption(
        chat_id=message.chat.id,
        message_id=message.message_id,
        caption="⏳ *2Captcha সার্ভারে পাঠানো হয়েছে, সলভ হচ্ছে...*",
        parse_mode="Markdown",
        reply_markup=get_captcha_keyboard("processing"),
    )

    try:
      # ইমেজ ফাইল ডাউনলোড করা
      photo = message.photo[-1] if message.photo else None
      # ശ്രദ്ധ্য: ছবি প্রসেস করার জন্য টেলিগ্রাম থেকে ফাইল অবজেক্ট নিতে হবে
      file_info = await bot.get_file(message.photo[-1].file_id)
      downloaded_file = await bot.download_file(file_info.file_path)

      image_name = f"captcha_{message.message_id}.jpg"
      with open(image_name, "wb") as f:
        f.write(downloaded_file.getvalue())

      # 2Captcha এপিআই দিয়ে সলভ করা
      result = solver.normal(image_name)
      solved_text = result.get("code")

      # লোকাল ফাইল ক্লিনআপ
      if os.path.exists(image_name):
        os.remove(image_name)

      # ভ্যানিশ ও ডিলিট সিস্টেম: আগের প্রসেসিং মেসেজটি রিমুভ করে দেওয়া
      await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

      # সফলভাবে সলভ হওয়ার পর রেজাল্ট পাঠানো এবং অটোমেটিক পরবর্তী স্টেপের অপশন
      success_kb = InlineKeyboardMarkup().add(
          InlineKeyboardButton("🔄 নতুন ক্যাপচা দিন", callback_data="new_task")
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
      # ত্রুটি হলে হ্যান্ডেল করা
      await bot.edit_message_caption(
          chat_id=message.chat.id,
          message_id=message.message_id,
          caption=f"❌ সলভ করতে ব্যর্থ হয়েছে: {str(e)}",
          parse_mode="Markdown",
      )


if __name__ == "__main__":
  print("মাস্টার অটোমেশন বট রানিং...")
  executor.start_polling(dp, skip_updates=True)
