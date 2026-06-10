import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.session.aiohttp import AiohttpSession
from aiohttp import ClientError

# === ИСПРАВЛЕНИЕ ДЛЯ WINDOWS ===
# asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ===== НАСТРОЙКИ (МЕНЯЕШЬ ТОЛЬКО ЭТО) =====
BOT_TOKEN = "8728774025:AAEexCfweIM_wltwi_oaJIwv6gaIssmESTg"  # Токен от BotFather
MY_USER_ID = 5811158994  # Твой ID от @userinfobot

# Файл с прокси (создай файл proxies.txt рядом с ботом)
PROXY_FILE = "proxies.txt"
# =========================================

logging.basicConfig(level=logging.INFO)
last_user_id = None
dp = Dispatcher()
bot = None


def load_proxies_from_file():
    """Загружает прокси из файла и добавляет socks5:// в начало"""
    proxies = []
    try:
        with open(PROXY_FILE, "r") as f:
            for line in f:
                line = line.strip()
                # Пропускаем пустые строки и комментарии
                if line and not line.startswith("#"):
                    # Если уже есть socks5://, оставляем как есть, иначе добавляем
                    if line.startswith("socks5://"):
                        proxies.append(line)
                    else:
                        proxies.append(f"socks5://{line}")
        print(f"📂 Загружено {len(proxies)} прокси из файла {PROXY_FILE}")
        return proxies
    except FileNotFoundError:
        print(f"❌ Файл {PROXY_FILE} не найден!")
        print("💡 Создай файл proxies.txt и напиши в нём прокси в формате ip:port (каждый с новой строки)")
        return []
    except Exception as e:
        print(f"❌ Ошибка при чтении файла: {e}")
        return []


async def find_working_proxy(proxy_list):
    """Перебирает прокси и возвращает первый рабочий"""
    if not proxy_list:
        return None

    print(f"🔍 Поиск рабочего прокси... (всего {len(proxy_list)} адресов)")

    for i, proxy in enumerate(proxy_list, 1):
        print(f"   [{i}/{len(proxy_list)}] Пробую {proxy}")
        try:
            # Создаём временную сессию с прокси
            session = AiohttpSession(proxy=proxy)
            test_bot = Bot(token=BOT_TOKEN, session=session)

            # Пытаемся получить информацию о боте (проверка связи)
            me = await test_bot.get_me()
            await test_bot.session.close()

            print(f"   ✅ ПРОКСИ РАБОТАЕТ! Подключено к @{me.username}")
            return proxy
        except (ClientError, OSError, Exception) as e:
            print(f"   ❌ Не работает: {type(e).__name__}")
            continue

    print("   ❌ НЕТ РАБОЧИХ ПРОКСИ! Обнови файл proxies.txt новыми адресами")
    return None


async def main():
    global bot

    # Загружаем прокси из файла
    proxy_list = load_proxies_from_file()

    # Находим рабочий прокси
    working_proxy = await find_working_proxy(proxy_list)
    if not working_proxy:
        print("❌ Не удалось подключиться. Проверь файл proxies.txt или интернет.")
        return

    # Создаём бота с рабочим прокси
    session = AiohttpSession(proxy=working_proxy)
    bot = Bot(token=BOT_TOKEN, session=session)

    # Отправляем тестовое сообщение владельцу
    try:
        await bot.send_message(MY_USER_ID, "✅ Бот успешно запущен и готов к работе!")
    except:
        print("⚠️ Не удалось отправить тестовое сообщение. Напиши /start боту, чтобы начать диалог.")

    print(f"✅ Бот запущен через прокси: {working_proxy}")
    await dp.start_polling(bot)


# ============ ВСЕ ХЕНДЛЕРЫ ============
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

    try:
        await bot.send_message(
            MY_USER_ID,
            f"✉️ От: {name} (ID: {user.id})\n💬 {text}"
        )
        await message.answer("Ждите, я вам позвоню по мере очереди")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


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


# =======================================

if __name__ == "__main__":
    asyncio.run(main())
