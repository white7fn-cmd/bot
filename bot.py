import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.session.aiohttp import AiohttpSession

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8728774025:AAEexCfweIM_wltwi_oaJIwv6gaIssmESTg"
MY_USER_ID = 5811158994
PROXY_FILE = "proxies.txt"
# ====================

logging.basicConfig(level=logging.INFO)
last_user_id = None
dp = Dispatcher()
bot = None


def load_proxies_from_file():
    proxies = []
    try:
        with open(PROXY_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if line.startswith("socks5://"):
                        proxies.append(line)
                    else:
                        proxies.append(f"socks5://{line}")
        print(f"📂 Загружено {len(proxies)} прокси из файла {PROXY_FILE}")
        return proxies
    except FileNotFoundError:
        print(f"❌ Файл {PROXY_FILE} не найден!")
        return []
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []


async def find_working_proxy(proxy_list):
    if not proxy_list:
        return None

    print(f"🔍 Поиск рабочего прокси... (всего {len(proxy_list)} адресов)")

    for i, proxy in enumerate(proxy_list, 1):
        print(f"   [{i}/{len(proxy_list)}] Пробую {proxy}")
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            session = AiohttpSession(proxy=proxy, timeout=timeout)
            test_bot = Bot(token=BOT_TOKEN, session=session)
            me = await test_bot.get_me()
            await test_bot.session.close()
            print(f"   ✅ ПРОКСИ РАБОТАЕТ! Подключено к @{me.username}")
            return proxy
        except Exception:
            continue

    print("   ❌ НЕТ РАБОЧИХ ПРОКСИ")
    return None


async def main():
    global bot

    proxy_list = load_proxies_from_file()
    working_proxy = await find_working_proxy(proxy_list)

    if working_proxy:
        session = AiohttpSession(proxy=working_proxy)
        bot = Bot(token=BOT_TOKEN, session=session)
        print(f"✅ Бот запущен через прокси: {working_proxy}")
    else:
        bot = Bot(token=BOT_TOKEN)
        print("✅ Бот запущен без прокси")

    try:
        await bot.send_message(MY_USER_ID, "✅ Бот успешно запущен!")
    except:
        print("⚠️ Напиши /start боту в Telegram")

    await dp.start_polling(bot)


# ============ ХЕНДЛЕРЫ ============
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Здравствуйте, опишите вашу проблему и я с вами свяжусь по мере очереди")


@dp.message()
async def forward_to_owner(message: types.Message):
    global last_user_id
    user = message.from_user
    last_user_id = user.id
    name = user.full_name or user.username or "Без имени"
    text = message.text

    # Отправляем пользователю только успех (ошибки — только в лог)
    try:
        await bot.send_message(
            MY_USER_ID,
            f"✉️ От: {name} (ID: {user.id})\n💬 {text}"
        )
        await message.answer("✅ Ждите, я вам позвоню по мере очереди")
    except Exception as e:
        # Ошибку не показываем пользователю, только пишем в консоль
        logging.error(f"Ошибка при отправке владельцу: {e}")
        await message.answer("❌ Не удалось доставить сообщение. Попробуйте позже.")


@dp.message(Command("r"))
async def reply_to_last(message: types.Message):
    if message.from_user.id != MY_USER_ID:
        return
    global last_user_id
    if not last_user_id:
        await message.answer("❌ Нет последнего пользователя")
        return

    reply_text = message.text.replace("/r", "", 1).strip()
    if not reply_text:
        await message.answer("❌ Напиши текст после /r")
        return

    try:
        await bot.send_message(last_user_id, f"📨 Ответ от создателя:\n{reply_text}")
        await message.answer("✅ Отправлено")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@dp.message(Command("reply"))
async def reply_to_id(message: types.Message):
    if message.from_user.id != MY_USER_ID:
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("❌ Формат: /reply ID текст")
        return
    _, target_id, reply_text = parts
    try:
        await bot.send_message(int(target_id), f"📨 Ответ от создателя:\n{reply_text}")
        await message.answer("✅ Отправлено")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(main())