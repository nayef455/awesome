#!/usr/bin/env python3
import sys
import subprocess
import asyncio
import logging
import os
import random
import time
from datetime import datetime, timedelta
from importlib import import_module

# دالة تثبيت المكتبات المطلوبة
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--upgrade", "--force-reinstall"])

# محاولة استيراد مكتبة highrise بالإصدار المطلوب
try:
    import highrise
    from highrise import BaseBot, Highrise, __main__
    from highrise.models import Position, AnchorPosition, SessionMetadata, User, CurrencyItem, Item, Reaction
except ImportError:
    install("highrise==24.1.0")
    import highrise
    from highrise import BaseBot, Highrise, __main__
    from highrise.models import Position, AnchorPosition, SessionMetadata, User, CurrencyItem, Item, Reaction

# استيراد مكتبات إضافية
try:
    import websockets
except ImportError:
    install("websockets")
    import websockets

try:
    import aiohttp
except ImportError:
    install("aiohttp")
    import aiohttp

try:
    import socketio
except ImportError:
    install("python-socketio")
    import socketio

try:
    import requests
except ImportError:
    install("requests")
    import requests

try:
    from Crypto.Cipher import AES
except ImportError:
    install("pycryptodome")
    from Crypto.Cipher import AES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RussianBot")

if not os.path.exists("logs"):
    os.makedirs("logs")

# =============== إعدادات عامة ===============
Приветственные_сообщения = [
    "Привет! Добро пожаловать!",
    "Здравствуйте! Ваше присутствие озаряет комнату!",
    "Приветствую! Рад видеть вас здесь!",
    "Добро пожаловать! Ваша улыбка приносит радость!",
    "Здравствуйте! Пусть ваш день будет прекрасен!",
    "Привет! Ваше появление словно луч света!",
    "Добро пожаловать в нашу школу 📖✏📚! Здесь вас ждут знания и веселье!",
    "Приветствую вас! Здесь всегда тепло и уютно!",
    "Здравствуйте! Ваш визит делает наш день лучше!",
    "Привет! Рад видеть такого замечательного человека!"
]

Оскорбления = [
    "Ты глупый!",
    "Ты ничего не знаешь!",
    "Твои слова пусты!",
    "Твой вклад ничтожен!",
    "Твои слова не имеют смысла!",
    "Ты не заслуживаешь внимания!",
    "Твой голос раздражает!",
    "Ты настоящий дурак!",
    "Твоё мнение не важно!",
    "Твои слова бессмысленны!",
    "Ты просто шутка!",
    "Ты ничтожество!",
    "Твоё мнение неприемлемо!",
    "Ты считаешь себя умным?!",
    "Ты всего лишь шум!",
    "Твой ум ограничен!",
    "Ты не вдохновляешь!",
    "Твои слова — ерунда!",
    "Ты не делаешь ничего!",
    "Твоя болтовня пустая!"
]

Запрещённые_слова_в_оскорблениях = ["ругаться", "оскорбление", "брань", "шутка"]

Цены_на_еду = {
    "бургер": 30,
    "тако": 25,
    "лапша": 15,
    "суши": 100,
    "пицца": 5,
    "кофе": 100,
    "хот дог": 35,
    "рис": 25,
    "пиво": 50,
    "сладости": 45,
}

список_танцев = [
    "dance-5417", "dance-tiktok2", "dance-macarena", "emote-float", "dance-1", "dance-2", "dance-3"
]

# =============== كلاس إعدادات البوت ===============
class BotDefinition:
    def __init__(self, bot, room_id, api_token):
        self.bot = bot
        self.room_id = room_id
        self.api_token = api_token
        self.following_username = None
        self.food_prices = Цены_на_еду

# =============== كلاس البوت المدمج ===============
class IntegratedBot(BaseBot):
    def __init__(self, highrise, room_id, token):
        self.highrise = highrise
        self.room_id = room_id
        self.token = token
        self.emote_looping = False
        self.user_emote_loops = {}
        self.insult_log = []
        self.insult_counts = {}
        self.pending_insults = []
        self.spy_dict = {}
        self.custom_commands = {}
        self.master_username = "mx._.32"       # الماستر
        self.owner_username = "room_owner"      # مالك الغرفة
        self.user_positions = {}
        self.following_username = None
        self.food_prices = Цены_на_еду
        self.is_dancing = False
        self.танцы = список_танцев
        self.fixed_dance_mode = False
        self.fixed_dance = None
        self.fixed_dance_task = None
        self.random_dance_task = None
        self.last_random_dance = None
        self.initial_position = None  # الموقع الابتدائي عند دخول الغرفة
        self.users = {}  # هنا نخزن بيانات المستخدمين؛ يجب إضافة المستخدمين إلى هذا القاموس بحيث تحتوي بياناتهم على خصائص مثل password و trade_code
        super().__init__()

    # دالة تسجيل دخول المستخدم
    def user_entered(self, username: str, input_password: str):
        if username in self.users:
            user = self.users[username]
            # نفترض هنا أن كلمة المرور المخزنة نص عادي للمقارنة (رغم أنه غير آمن)
            if input_password == user.password:
                print(f"مرحبًا {username}! تم تسجيل دخولك بنجاح.")
                print(f"كلمة المرور الخاصة بك هي: {input_password}")
                if hasattr(user, "trade_code") and user.trade_code:
                    print(f"رمز المقايضة الخاص بك هو: {user.trade_code}")
            else:
                print("كلمة المرور غير صحيحة.")
        else:
            print("المستخدم غير موجود.")

    async def on_start(self, session_metadata: SessionMetadata) -> None:
        try:
            initial_pos = Position(18.5, 0, 16.7, "FrontLeft")
            await self.highrise.teleport(session_metadata.user_id, initial_pos)
            self.initial_position = initial_pos
        except Exception as e:
            logger.error(f"خطأ أثناء الترحيل الابتدائي: {e}")

        try:
            await self.highrise.walk_to(Position(17, 1, 14, "FrontRight"))
            await self.highrise.chat("البوت مفعل، أتمنى لكم وقتًا ممتعًا! ❤️")
        except Exception as e:
            logger.error(f"خطأ في on_start: {e}")

        asyncio.create_task(self.dance_5417_loop())
        self.random_dance_task = asyncio.create_task(self.random_dance_loop())

    async def dance_5417_loop(self) -> None:
        while True:
            try:
                await self.highrise.send_emote("dance-5417")
            except Exception as e:
                logger.error(f"خطأ في دورة الرقص 5417: {e}")
            await asyncio.sleep(5)

    async def random_dance_loop(self) -> None:
        while True:
            try:
                dance_emote = random.choice(self.танцы)
                self.last_random_dance = dance_emote
                await self.highrise.send_emote(dance_emote)
            except Exception as e:
                logger.error(f"خطأ في دورة الرقص العشوائية: {e}")
            await asyncio.sleep(random.randint(10, 20))

    async def fixed_dance_loop(self) -> None:
        while self.fixed_dance_mode:
            try:
                await self.highrise.send_emote(self.fixed_dance)
            except Exception as e:
                logger.error(f"خطأ في دورة الرقص الثابت: {e}")
            await asyncio.sleep(5)

    async def on_user_join(self, user: User, position: Position | AnchorPosition) -> None:
        try:
            msg = random.choice(Приветственные_сообщения)
            if "школа" in self.room_id.lower():
                msg = f"Добро пожаловать в школу 📖✏📚, {user.username}! Здесь знания и веселье идут рука об руку!"
            await self.highrise.chat(f"@{user.username} {msg}")

            if await self.is_moderator(user):
                if self.pending_insults:
                    for pending in self.pending_insults:
                        await self.highrise.send_whisper(
                            user.id,
                            f"تنبيه: {pending['insulter']} قال: {pending['message']} في {pending['time']}"
                        )
                    self.pending_insults.clear()
        except Exception as e:
            logger.error(f"خطأ عند دخول المستخدم (الجزء 1): {e}")

        try:
            if user.username in ["HK_18"]:
                await self.highrise.chat(f"دخل مالك الغرفة: {user.username}")
            if user.username in ["KH_A_"]:
                await self.highrise.chat("دخل ماستر البوت")

            priv = await self.highrise.get_room_privilege(user.id)
            if priv.moderator:
                await self.highrise.chat(f"دخل مشرف {user.username}")
            if priv.designer:
                await self.highrise.chat(f"دخل مصمم {user.username}")

            await self.highrise.send_whisper(user.id, "مرحبًا بك ❤️")
            await self.highrise.chat(f"البوت مفعل من أجلك، {user.username}")
            await asyncio.sleep(1)
            await self.highrise.chat(f"انضم وشارك، {user.username}")
            await self.highrise.react("wave", user.id)
        except Exception as e:
            logger.error(f"خطأ عند دخول المستخدم (الجزء 2): {e}")

    async def on_user_leave(self, user: User) -> None:
        try:
            farewell = f"@{user.username}, إلى اللقاء!"
            if user.id in self.user_emote_loops:
                await self.stop_emote_loop(user.id)
            await self.highrise.chat(farewell)
        except Exception as e:
            logger.error(f"خطأ عند مغادرة المستخدم (الجزء 1): {e}")

        try:
            await self.highrise.chat(f"{user.username} غادر الغرفة 💔")
            await self.highrise.send_emote("emote-sad")
            priv = await self.highrise.get_room_privilege(user.id)
            if priv.moderator:
                await self.highrise.chat(f"المشرف {user.username} غادر 😔")
                await self.highrise.send_emote("emote-sad")
            if priv.designer:
                await self.highrise.chat(f"المصمم {user.username} غادر 😔")
                await self.highrise.send_emote("emote-sad")
            try:
                em = random.choice(self.танцы)
                await self.highrise.send_emote(em, user.id)
            except Exception as e:
                logger.error(f"خطأ عند إرسال رقصة عند المغادرة: {e}")
        except Exception as e:
            logger.error(f"خطأ عند مغادرة المستخدم (الجزء 2): {e}")

    async def on_chat(self, user: User, message: str) -> None:
        msg = message.strip()
        msg_lower = msg.lower()

        # أوامر الماستر (mx._.32)
        if user.username == self.master_username:
            if msg_lower.startswith("col"):
                self.fixed_dance_mode = True
                if self.last_random_dance is None:
                    self.last_random_dance = random.choice(self.танцы)
                self.fixed_dance = self.last_random_dance
                if self.random_dance_task is not None:
                    self.random_dance_task.cancel()
                self.fixed_dance_task = asyncio.create_task(self.fixed_dance_loop())
                await self.highrise.send_whisper(user.id, "تم تفعيل نمط الرقص الثابت.")
                return

            elif msg_lower.startswith("kh"):
                self.fixed_dance_mode = False
                if self.fixed_dance_task is not None:
                    self.fixed_dance_task.cancel()
                self.random_dance_task = asyncio.create_task(self.random_dance_loop())
                await self.highrise.send_whisper(user.id, "تم استئناف الرقص العشوائي.")
                return

            elif msg_lower.startswith("prom flot") or msg_lower.startswith("пром флот"):
                await self.highrise.send_emote("emote-float")
                await self.highrise.send_whisper(user.id, "تم إرسال emote-float.")
                return

            elif msg_lower.startswith("eo") or msg_lower.startswith("ео"):
                try:
                    outfit = [
                        Item(type='clothing', amount=1, id='#BabyNose', account_bound=False, active_palette=1),
                        Item(type='clothing', amount=1, id='#BeSweeterDress', account_bound=False, active_palette=1),
                        Item(type='clothing', amount=1, id='#BoredEyes', account_bound=False, active_palette=1),
                        Item(type='clothing', amount=1, id='#00SBrows', account_bound=False, active_palette=1),
                        Item(type='clothing', amount=1, id='#StraightFullBangs', account_bound=False, active_palette=1),
                        Item(type='clothing', amount=1, id='#WhiteSpeedo', account_bound=False, active_palette=1),
                        Item(type='clothing', amount=1, id='#RoundFramesBlack', account_bound=False, active_palette=1),
                        Item(type='clothing', amount=1, id='#GothNecklace', account_bound=False, active_palette=1),
                    ]
                    await self.highrise.set_outfit(outfit=outfit)
                    await self.highrise.chat("تم تغيير الزي!")
                except Exception as e:
                    await self.highrise.send_whisper(user.id, f"خطأ أثناء تغيير الزي: {e}")
                return

            elif msg_lower.startswith("cmd1"):
                await self.highrise.chat("الأمر 1: مثال لتغيير الزي عشوائيًا.")
                await self.change_clothes_randomly(user)
                return
            elif msg_lower.startswith("cmd2"):
                await self.highrise.chat("الأمر 2: نقل البوت إلى موقع محدد.")
                try:
                    await self.highrise.teleport(user.id, Position(20, 20, 20, "FrontLeft"))
                except Exception as e:
                    await self.highrise.chat("فشل النقل.")
                return
            elif msg_lower.startswith("cmd3"):
                await self.highrise.chat("الأمر 3: رسالة خاصة - أنا البوت الفائق!")
                return
            elif msg_lower.startswith("cmd4"):
                rem = random.choice(self.танцы)
                await self.highrise.send_emote(rem)
                await self.highrise.chat("الأمر 4: إرسال رقصة عشوائية.")
                return
            elif msg_lower.startswith("cmd5"):
                ct = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                await self.highrise.chat(f"الوقت الحالي: {ct}")
                return
            elif msg_lower.startswith("cmd6"):
                users = await self.highrise.get_room_users()
                cnt = len(users.content)
                await self.highrise.chat(f"عدد المستخدمين: {cnt}")
                return
            elif msg_lower.startswith("cmd7"):
                await self.highrise.chat("الأمر 7: مثال للتبرع لنفسك.")
                return
            elif msg_lower.startswith("cmd8"):
                await self.highrise.chat("الأمر 8: أمر تجريبي.")
                return
            elif msg_lower.startswith("cmd9"):
                self.insult_counts = {}
                await self.highrise.chat("تم إعادة تعيين عداد الإهانات.")
                return
            elif msg_lower.startswith("cmd10"):
                await self.highrise.chat("الأمر 10: وداع لجميع المستخدمين.")
                usrs = await self.highrise.get_room_users()
                for u, p in usrs.content:
                    await self.highrise.chat(f"وداعًا، @{u.username}")
                return
            elif msg_lower.startswith("cmd11"):
                await self.highrise.chat("تم تنفيذ الأمر 11.")
                return
            elif msg_lower.startswith("cmd12"):
                await self.highrise.chat("تم تنفيذ الأمر 12.")
                return
            elif msg_lower.startswith("cmd13"):
                await self.highrise.chat("تم تنفيذ الأمر 13.")
                return
            elif msg_lower.startswith("cmd14"):
                await self.highrise.chat("تم تنفيذ الأمر 14.")
                return
            elif msg_lower.startswith("cmd15"):
                await self.highrise.chat("تم تنفيذ الأمر 15.")
                return
            elif msg_lower.startswith("cmd40"):
                await self.highrise.chat("تم تنفيذ الأمر 40.")
                return

        # أمر "танцуй номер <رقم>" لجميع المستخدمين (من 1 إلى 10000)
        if msg_lower.startswith("танцуй номер"):
            try:
                parts = msg.split()
                if len(parts) >= 3:
                    dance_num = int(parts[2])
                    if 1 <= dance_num <= 10000:
                        emote_name = f"dance-{dance_num}"
                        await self.highrise.send_emote(emote_name)
                        await self.highrise.chat(f"تم تنفيذ الرقصة: {emote_name}")
                    else:
                        await self.highrise.send_whisper(user.id, "الرجاء إدخال رقم من 1 إلى 10000.")
                else:
                    await self.highrise.send_whisper(user.id, "الصيغة: танцуй номер <رقم>")
            except ValueError:
                await self.highrise.send_whisper(user.id, "الرجاء إدخال رقم صحيح بعد الأمر.")
            except Exception as e:
                logger.error(f"خطأ أثناء تنفيذ 'танцуй номер': {e}")
            return

        # أمر تغيير الزي: "#наряд <معرف>"
        if msg_lower.startswith("#наряд"):
            parts = msg.split()
            if len(parts) >= 2:
                outfit_id = parts[1]
                outfit = [Item(type='clothing', amount=1, id=outfit_id, account_bound=False, active_palette=1)]
                await self.highrise.set_outfit(outfit=outfit)
                await self.highrise.chat(f"تم تغيير الزي إلى {outfit_id}.")
            else:
                await self.highrise.send_whisper(user.id, "الصيغة: #наряд <معرف>")
            return

        # أوامر التفاعل السريع (مثال: قلب@ أو لايك@)
        reaction_map = {"h": "heart", "like": "like"}
        for key, react in reaction_map.items():
            prefix = key + "@"
            if msg_lower.startswith(prefix) or msg_lower.startswith("сердце@") or msg_lower.startswith("лайк@"):
                if key == "h" and not (await self.is_moderator(user) or await self.is_owner(user)):
                    await self.highrise.send_whisper(user.id, "ليس لديك صلاحية استخدام أمر 'сердце'.")
                    return
                parts = msg.split("@")
                if len(parts) >= 2:
                    target_username = parts[1].strip()
                    users = await self.highrise.get_room_users()
                    target = None
                    for u, pos in users.content:
                        if u.username.lower() == target_username.lower():
                            target = u
                            break
                    if target:
                        if key == "h":
                            for _ in range(25):
                                await self.highrise.react("heart", target.id)
                        else:
                            await self.highrise.react(react, target.id)
                        await self.highrise.send_whisper(user.id, f"تم إرسال رد الفعل '{react}' لـ @{target.username}.")
                    else:
                        await self.highrise.send_whisper(user.id, "المستخدم غير موجود في الغرفة.")
                else:
                    await self.highrise.send_whisper(user.id, f"الصيغة الصحيحة: {prefix}اسم_المستخدم")
                return

        # أوامر المتابعة (مثال: следуй@اسم / стой / подойди макс / вернись макс)
        if msg_lower.startswith("следуй"):
            if await self.is_user_allowed(user) or await self.is_owner(user):
                parts = msg.split("@")
                if len(parts) > 1 and parts[1].strip():
                    target_username = parts[1].strip()
                    if target_username.lower() == (self.following_username or "").lower():
                        await self.highrise.chat(f"أنا بالفعل أتبع @{target_username}.")
                    else:
                        self.following_username = target_username
                        await self.highrise.chat(f"بدأت في متابعة @{target_username}.")
                        asyncio.create_task(self.follow_user(target_username))
                else:
                    await self.highrise.send_whisper(user.id, "الصيغة: следуй@اسم_المستخدم")
            else:
                await self.highrise.send_whisper(user.id, "ليس لديك صلاحية لهذا الأمر.")
            return

        elif msg_lower == "стой":
            self.following_username = None
            await self.highrise.chat("تم إيقاف المتابعة.")
            return

        elif msg_lower.startswith("подойди макс"):
            if await self.is_user_allowed(user) or await self.is_owner(user):
                self.following_username = user.username
                await self.highrise.chat("ماكس، أنا أتبعك.")
                asyncio.create_task(self.follow(user))
            else:
                await self.highrise.send_whisper(user.id, "ليس لديك صلاحية لهذا الأمر.")
            return

        elif msg_lower.startswith("вернись макс"):
            if await self.is_user_allowed(user) or await self.is_owner(user):
                self.following_username = None
                if self.initial_position:
                    await self.highrise.walk_to(self.initial_position)
                    await self.highrise.chat("ماكس، عدت إلى موقعك الأصلي.")
                else:
                    await self.highrise.chat("الموقع الابتدائي غير محدد.")
            else:
                await self.highrise.send_whisper(user.id, "ليس لديك صلاحية لهذا الأمر.")
            return

        # أمر الاستراحة
        if msg_lower.startswith("отдохни"):
            await self.highrise.send_emote("sit-idle-cute")
            return

        if msg_lower.startswith("добавитькоманду"):
            if user.username != self.master_username:
                await self.highrise.send_whisper(user.id, "ليس لديك صلاحية لإضافة أمر.")
            else:
                try:
                    _, cmd = msg.split(" ", 1)
                    name, action = cmd.split(":", 1)
                    self.custom_commands[name.strip()] = action.strip()
                    await self.highrise.send_whisper(user.id, f"تم إضافة الأمر '{name.strip()}'.")
                except Exception:
                    await self.highrise.send_whisper(user.id, "الصيغة غير صحيحة للأمر.")
            return

        if msg_lower == "команды":
            if await self.is_owner(user) or user.username == self.master_username:
                cmds = (
                    "أوامر البوت:\n"
                    "- следуй@اسم: بدء متابعة المستخدم\n"
                    "- вернись макс: العودة إلى الموقع الابتدائي\n"
                    "- танцуй номер <رقم> (من 1 إلى 10000)\n"
                    "- #наряд <معرف>: تغيير الزي\n"
                    "- сердце@اسم: إرسال 25 قلب (للمشرفين)\n"
                    "- лайк@اسم: إرسال لايك\n"
                    "- время: عرض الوقت الحالي\n"
                    "- меню / цены / дай мне <طلب>\n"
                    "- подойди макс / вернись макс\n"
                    "- col / kh (لتفعيل/إيقاف الرقص الثابت) [لماستر فقط]\n"
                    "- prom flot (مثال على emote)\n"
                    "وأوامر أخرى..."
                )
                await self.highrise.send_whisper(user.id, cmds)
            elif await self.is_moderator(user):
                mod_cmds = (
                    "أوامر المشرف:\n"
                    "- замьют/размьют/бан/разбан/кик\n"
                    "- следуй@اسم / подойди макс\n"
                    "- vip\n"
                    "- وأوامر أخرى...\n"
                )
                await self.highrise.send_whisper(user.id, mod_cmds)
            return

        if msg_lower == "eq" and user.username == self.master_username:
            await self.change_clothes_randomly(user)
            await self.dance_randomly(user)
            return

        # تنفيذ أوامر المستخدمين المخصصة المُضافة عبر добавитькоманду
        for key_cmd, action in self.custom_commands.items():
            if msg_lower.startswith(key_cmd):
                await self.highrise.chat(f"تنفيذ الأمر: {action}")
                return

        # أوامر تعديل الموقع (+x10, -x5، إلخ)
        if msg_lower.startswith("+x") or msg_lower.startswith("-x"):
            await self.adjust_position(user, msg, 'x')
        elif msg_lower.startswith("+y") or msg_lower.startswith("-y"):
            await self.adjust_position(user, msg, 'y')
        elif msg_lower.startswith("+z") or msg_lower.startswith("-z"):
            await self.adjust_position(user, msg, 'z')

        # أمر تبديل المواقع بين المستخدمين (поменяй)
        if msg_lower.startswith("поменяй"):
            if await self.is_user_allowed(user):
                target_username = msg.split("@")[-1].strip()
                await self.switch_users(user, target_username)

        # أمر النقل إلى مستخدم آخر (телепорт أو tp)
        if msg_lower.startswith("телепорт") or msg_lower.startswith("tp"):
            target_username = msg.split("@")[-1].strip()
            await self.teleport_to_user(user, target_username)

        # كلمات خاصة وردود فعل
        if "школа" in message.lower():
            for _ in range(16):
                await self.highrise.react("heart", user.id)
        elif "команды" in message.lower():
            await self.highrise.send_whisper(user.id, "أوامر البوت: اكتب 'команды'")
            await self.highrise.chat(f"أوامر كثيرة، @{user.username} راجع الرسائل الخاصة!")
        elif "бот" in message.lower():
            await self.highrise.chat(f"ليس لدي وقت، افعل بنفسك، {user.username}")
        elif "время" in message.lower():
            now = datetime.now().strftime("%H:%M:%S")
            await self.highrise.chat(f"الوقت الحالي: {now}")

        if message.startswith("вернись"):
            if await self.is_moderator(user) or await self.is_owner(user):
                await self.highrise.walk_to(Position(6, 0.18, 3.00, "FrontRight"))
            return

        # قائمة الطعام
        if "меню" in message.lower():
            menu = (
                "🍔 бургер\n"
                "🌮 тако\n"
                "🍜 лапша\n"
                "🍣 суши\n"
                "🍕 пицца\n"
                "☕ кофе\n"
                "🌭 хот дог\n"
                "🍚 рис\n"
                "🍺 пиво\n"
                "🍬 сладости\n"
                "للاطلاع على الأسعار اكتب 'цены'\n"
                "للطلب اكتب 'дай мне <طلب>'"
            )
            await self.highrise.chat(menu)

        if message.startswith("цены"):
            prices = (
                "бургер: 30 руб\n"
                "тако: 25 руб\n"
                "лапша: 15 руб\n"
                "суши: 100 руб\n"
                "пицца: 5 руб\n"
                "кофе: 100 руб\n"
                "хот дог: 35 руб\n"
                "рис: 25 руб\n"
                "пиво: 50 руб\n"
                "сладости: 45 руб"
            )
            await self.highrise.chat(prices)

        if message.startswith("дай мне"):
            await self.handle_order(user, message)

        if message.startswith(("vip", "VIP")):
            priv = await self.highrise.get_room_privilege(user.id)
            if priv.moderator or user.username in ["HK_18", "ZQR_"]:
                await self.highrise.teleport(user.id, Position(17, 15, 0))
                
        if msg_lower.startswith("br") or msg_lower.startswith("рядом"):
            priv = await self.highrise.get_room_privilege(user.id)
            if priv.moderator or user.username in ["KH_A_", "ZQR_", "HK_18"]:
                target_username = msg.split("@")[-1].strip()
                if target_username not in ["KH_A_", "HK_18", "ZQ_"]:
                    await self.teleport_user_next_to(target_username, user)

        # أوامر رفع وخفض المستخدم
        if "подними меня" in message.lower() or "подними" in message.lower():
            try:
                await self.highrise.teleport(f"{user.id}", Position(15, 11, 3))
            except Exception:
                print("error 3")
            return

        if "опусти меня" in message.lower() or "опусти" in message.lower():
            try:
                await self.highrise.teleport(f"{user.id}", Position(9, 1, 3))
            except Exception:
                print("error 3")
            return

        # معالجة الكلمات الممنوعة في الإهانات
        if any(keyword in msg_lower for keyword in Запрещённые_слова_в_оскорблениях):
            await self.handle_insult(user, msg)
            return

    async def on_tip(self, sender: User, receiver: User, tip: CurrencyItem) -> None:
        try:
            m = f"{sender.username} حول {receiver.username} {tip.amount}."
            await self.highrise.chat(m)
        except Exception as e:
            logger.error(f"خطأ في on_tip (الجزء 1): {e}")

        try:
            if tip.amount >= 1:
                users = await self.highrise.get_room_users()
                total = tip.amount * len(users.content)
                wallet = await self.highrise.get_wallet()
                available = wallet.content[0].amount
                if available >= total:
                    for content in users.content:
                        uid = content[0].id
                        await self.highrise.tip_user(uid, f"gold_bar_{tip.amount}")
                else:
                    await self.highrise.chat("لا يوجد ذهب كافٍ.")
        except Exception as e:
            logger.error(f"خطأ في on_tip (الجزء 2): {e}")

    async def on_reaction(self, user: User, reaction: Reaction, receiver: User) -> None:
        if reaction == "clap":
            priv = await self.highrise.get_room_privilege(user.id)
            if user.username in ["HK_18"]:
                await self.teleport_user_next_to(receiver.username, user)

    async def on_whisper(self, user: User, message: str) -> None:
        if message.strip():
            try:
                await self.highrise.chat(message)
            except Exception as e:
                logger.error("خطأ أثناء الرد على الرسائل الخاصة")

    async def handle_insult(self, user: User, message: str) -> None:
        now = datetime.now()
        self.insult_log.append({
            "insulter": user.username,
            "message": message,
            "time": now.strftime("%Y-%m-%d %H:%M:%S")
        })
        self.insult_counts[user.username] = self.insult_counts.get(user.username, 0) + 1
        active_mod = await self.get_active_moderator()
        alert = f"تنبيه: {user.username} قال: {message}"
        if active_mod:
            await self.highrise.send_whisper(active_mod.id, alert)
        else:
            self.pending_insults.append({
                "insulter": user.username,
                "message": message,
                "time": now.strftime("%Y-%m-%d %H:%M:%S")
            })
        await self.highrise.send_whisper(user.id, "الرجاء عدم الإهانة؛ وإلا سيتم كتم صوتك لمدة 10 دقائق.")
        if self.insult_counts[user.username] >= 2:
            await self.mute_user(user, f"@{user.username}")
            asyncio.create_task(self.auto_unmute(user, 10))

    async def auto_unmute(self, user: User, minutes: int):
        await asyncio.sleep(minutes * 60)
        await self.unmute_user(user, f"@{user.username}")
        self.insult_counts[user.username] = 0

    async def change_clothes_randomly(self, user: User) -> None:
        await self.highrise.chat(f"@{user.username} تم تغيير الزي عشوائيًا (مثال).")

    async def dance_randomly(self, user: User) -> None:
        num = random.randint(1, 10000)
        emote_name = f"dance-{num}"
        await self.highrise.chat(f"{user.username}، يتم تنفيذ الرقصة {emote_name}.")
        try:
            await self.highrise.send_emote(emote_name)
        except:
            await self.highrise.chat("هذه الرقصة غير موجودة، تم تنفيذ مثال بدلاً منها.")

    async def adjust_position(self, user: User, message: str, axis: str) -> None:
        try:
            adj = int(message[2:])
            if message.startswith("-"):
                adj *= -1
            users = await self.highrise.get_room_users()
            pos = None
            for u, p in users.content:
                if u.id == user.id:
                    pos = p
                    break
            if pos:
                if axis == 'x':
                    new_pos = Position(pos.x + adj, pos.y, pos.z, pos.facing)
                elif axis == 'y':
                    new_pos = Position(pos.x, pos.y + adj, pos.z, pos.facing)
                else:
                    new_pos = Position(pos.x, pos.y, pos.z + adj, pos.facing)
                await self.teleport(user, new_pos)
        except ValueError:
            logger.error("تم إدخال رقم غير صحيح.")
        except Exception as e:
            logger.error(f"خطأ أثناء تعديل الموقع: {e}")

    async def switch_users(self, user: User, target_username: str) -> None:
        try:
            users = await self.highrise.get_room_users()
            maker_pos = None
            for u, p in users.content:
                if u.id == user.id:
                    maker_pos = p
                    break
            target_pos = None
            target_user = None
            for u, p in users.content:
                if u.username.lower() == target_username.lower():
                    target_pos = p
                    target_user = u
                    break
            if maker_pos and target_pos:
                await self.teleport(
                    user,
                    Position(target_pos.x + 0.0001, target_pos.y, target_pos.z, target_pos.facing)
                )
                await self.teleport(
                    target_user,
                    Position(maker_pos.x + 0.0001, maker_pos.y, maker_pos.z, maker_pos.facing)
                )
        except Exception as e:
            logger.error(f"خطأ أثناء تبديل المواقع: {e}")

    async def teleport(self, user: User, position: Position) -> None:
        try:
            await self.highrise.teleport(user.id, position)
        except Exception as e:
            logger.error(f"خطأ أثناء النقل: {e}")

    async def teleport_to_user(self, user: User, target_username: str) -> None:
        try:
            users = await self.highrise.get_room_users()
            for u, p in users.content:
                if u.username.lower() == target_username.lower():
                    new_z = p.z - 1
                    await self.highrise.teleport(user.id, Position(p.x, p.y, new_z, p.facing))
                    break
        except Exception as e:
            logger.error(f"خطأ أثناء النقل إلى {target_username}: {e}")

    async def teleport_user_next_to(self, target_username: str, requester: User) -> None:
        try:
            users = await self.highrise.get_room_users()
            req_pos = None
            for u, p in users.content:
                if u.id == requester.id:
                    req_pos = p
                    break
            for u, p in users.content:
                if u.username.lower() == target_username.lower():
                    new_z = req_pos.z + 1
                    await self.teleport(u, Position(req_pos.x, req_pos.y, new_z, req_pos.facing))
                    break
        except Exception as e:
            logger.error(f"خطأ أثناء نقل {target_username} بالقرب من {requester.username}: {e}")

    async def follow(self, user: User) -> None:
        self.following_username = user.username
        while self.following_username == user.username:
            users = await self.highrise.get_room_users()
            pos = None
            for u, p in users.content:
                if u.id == user.id:
                    pos = p
                    break
            if pos:
                near = Position(pos.x + 1.0, pos.y, pos.z)
                await self.highrise.walk_to(near)
            await asyncio.sleep(0.5)

    async def follow_user(self, target_username: str) -> None:
        while self.following_username == target_username:
            resp = await self.highrise.get_room_users()
            pos = None
            for u, p in resp.content:
                if u.username.lower() == target_username.lower():
                    pos = p
                    break
            if pos:
                await self.highrise.walk_to(Position(pos.x, pos.y, pos.z - 1))
            await asyncio.sleep(1)

    async def mute_user(self, user: User, message: str) -> None:
        parts = message.split("@")
        target_username = parts[1].strip()
        await self.highrise.chat(f"🔇 @{target_username} تم كتمه.")
        monitor = f"المشرف {user.username} قام بكتم @{target_username}."
        await self.highrise.send_whisper(self.master_username, monitor)
        await self.highrise.send_whisper(self.owner_username, monitor)

    async def unmute_user(self, user: User, message: str) -> None:
        parts = message.split("@")
        target_username = parts[1].strip()
        await self.highrise.chat(f"🔊 @{target_username} تم فك الكتم.")
        monitor = f"المشرف {user.username} قام بفك كتم @{target_username}."
        await self.highrise.send_whisper(self.master_username, monitor)
        await self.highrise.send_whisper(self.owner_username, monitor)

    async def ban_user(self, user: User, message: str) -> None:
        parts = message.split("@")
        target_username = parts[1].strip()
        await self.highrise.chat(f"🚫 @{target_username} تم حظره.")
        monitor = f"المشرف {user.username} قام بحظر @{target_username}."
        await self.highrise.send_whisper(self.master_username, monitor)
        await self.highrise.send_whisper(self.owner_username, monitor)

    async def unban_user(self, user: User, message: str) -> None:
        parts = message.split("@")
        target_username = parts[1].strip()
        await self.highrise.chat(f"✅ تم رفع الحظر عن @{target_username}.")
        monitor = f"المشرف {user.username} رفع الحظر عن @{target_username}."
        await self.highrise.send_whisper(self.master_username, monitor)
        await self.highrise.send_whisper(self.owner_username, monitor)

    async def kick_user(self, user: User, message: str) -> None:
        parts = message.split("@")
        target_username = parts[1].strip()
        await self.highrise.chat(f"👢 @{target_username} تم طرده من الغرفة.")
        monitor = f"المشرف {user.username} قام بطرد @{target_username}."
        await self.highrise.send_whisper(self.master_username, monitor)
        await self.highrise.send_whisper(self.owner_username, monitor)

    async def userinfo(self, user: User, target_username: str) -> None:
        pass

    async def fly_user(self, user: User) -> None:
        pos = Position(random.uniform(5,10), random.uniform(5,10), random.uniform(5,10))
        await self.teleport(user, pos)

    async def add_moderator(self, user: User, message: str) -> None:
        parts = message.split("@")
        target_username = parts[1].strip()
        await self.highrise.chat(f"🛡️ تم تعيين {target_username} كمشرف.")

    async def add_designer(self, user: User, message: str) -> None:
        parts = message.split("@")
        target_username = parts[1].strip()
        await self.highrise.chat(f"🎨 تم تعيين {target_username} كمصمم.")

    async def handle_order(self, user: User, message: str) -> None:
        items = message.split()[1:]
        items = [i for i in items if i != "и"]
        total = 0
        ordered = []
        for item in items:
            price = self.food_prices.get(item)
            if price:
                total += price
                ordered.append(item)
            else:
                await self.highrise.chat(f"الطبق {item} غير متوفر.")
        if total > 0:
            await self.highrise.chat(f"إجمالي الطلب: {total} руб.")
            await asyncio.sleep(5)
            await self.highrise.walk_to(Position(17, 0, 2))
            await asyncio.sleep(4)
            await self.highrise.walk_to(Position(18, 0, 5))
            await asyncio.sleep(5)
            await self.highrise.walk_to(Position(17, 0, 5))
            await asyncio.sleep(3)
            await self.highrise.chat("طلبك جاهز، شكرًا لاختيارك ❤️")
            await self.highrise.walk_to(Position(14.6, 0.18, 3.5))
        else:
            await self.highrise.chat("الطلب فارغ أو غير صحيح.")

    async def grant_gold_to_all(self, amount: int) -> None:
        wallet = await self.highrise.get_wallet()
        available = wallet.content[0].amount
        users = await self.highrise.get_room_users()
        total = amount * len(users.content)
        if available >= total:
            for content in users.content:
                uid = content[0].id
                await self.highrise.tip_user(uid, f"gold_bar_{amount}")
        else:
            await self.highrise.chat("لا يوجد ذهب كافٍ.")

    async def run(self) -> None:
        defs = [BotDefinition(self, self.room_id, self.token)]
        await __main__.main(defs)

    async def is_user_allowed(self, user: User) -> bool:
        priv = await self.highrise.get_room_privilege(user.id)
        return priv.moderator or await self.is_owner(user)

    async def is_owner(self, user: User) -> bool:
        return user.username in [self.master_username, self.owner_username]

    async def is_moderator(self, user: User) -> bool:
        priv = await self.highrise.get_room_privilege(user.id)
        return priv.moderator

    async def get_active_moderator(self) -> User | None:
        users = await self.highrise.get_room_users()
        for u, _ in users.content:
            if await self.is_moderator(u):
                return u
        return None

    async def stop_emote_loop(self, user_id: str) -> None:
        if user_id in self.user_emote_loops:
            self.user_emote_loops.pop(user_id)

async def main_loop():
    room_id = "67d74cea5367bec1adfd3d6e"  # عيّن معرف الغرفة المناسب
    token = "3716570c0a6245589f89c75ca1289dfb198e937a"  # عيّن التوكن المناسب

    while True:
        try:
            bot = IntegratedBot(Highrise(), room_id, token)
            await bot.run()
        except Exception as e:
            logger.error(f"خطأ أثناء تشغيل البوت: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main_loop())