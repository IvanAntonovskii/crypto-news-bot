import requests
import logging
import asyncio
import aiohttp
import random
import json
import os
import io
from datetime import datetime
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont, ImageOps
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CryptoNewsBot:
    def __init__(self, token, channel):
        self.token = token
        self.channel = channel
        self.session = None
        self.published_news = set()
        self.load_published_news()

        # Байтовые фразы для постов
        self.viral_phrases = [
            "🚀 ЗАЛЕТАЕМ В ТРЕНДЫ!",
            "💎 ХАЙП НА СТАРТЕ!",
            "🔥 ГОРИМ, НО НЕ СДАЕМСЯ!",
            "📈 ВЗЛЕТАЕМ НА ЛУНУ!",
            "💥 БОМБИЧЕСКИЕ НОВОСТИ!",
            "🚨 ВНИМАНИЕ, ХАЙП!",
            "🎯 ТОЧКА ВХОДА!",
            "⚡ МОМЕНТ ИСТИНЫ!",
            "🌟 ЗВЕЗДНЫЙ ЧАС!",
            "💣 БОМБА ДНЯ!"
        ]

        self.emojis = ["🚀", "💎", "🔥", "📈", "💥", "🚨", "🎯", "⚡", "🌟", "💣", "🎊", "👑", "💸", "🤑", "👀"]

        # Загружаем логотип
        self.logo = self.load_logo()

    def load_logo(self):
        """Загружает логотип из файла"""
        try:
            if os.path.exists('лого.png'):
                logo = Image.open('лого.png')
                # Ресайзим логотип до подходящего размера
                logo = logo.resize((200, 80), Image.Resampling.LANCZOS)
                return logo
            else:
                logger.warning("Логотип 'лого.png' не найден, создаем стандартный")
                return self.create_default_logo()
        except Exception as e:
            logger.error(f"Error loading logo: {e}")
            return self.create_default_logo()

    def create_default_logo(self):
        """Создает стандартный логотип если файл не найден"""
        try:
            logo = Image.new('RGB', (200, 80), color=(255, 193, 7))
            draw = ImageDraw.Draw(logo)

            try:
                font = ImageFont.truetype("arial.ttf", 20)
                font_small = ImageFont.truetype("arial.ttf", 14)
            except:
                font = ImageFont.load_default()
                font_small = ImageFont.load_default()

            draw.text((10, 10), "A", fill=(0, 0, 0), font=font)
            draw.text((40, 15), "ANT CAPITAL", fill=(0, 0, 0), font=font_small)
            draw.rectangle([0, 0, 199, 79], outline=(0, 0, 0), width=2)

            return logo
        except Exception as e:
            logger.error(f"Error creating default logo: {e}")
            return None

    def load_published_news(self):
        """Загружает историю опубликованных новостей"""
        try:
            if os.path.exists('published_news.json'):
                with open('published_news.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.published_news = set(data.get('published', []))
        except Exception as e:
            logger.error(f"Error loading published news: {e}")

    def save_published_news(self):
        """Сохраняет историю опубликованных новостей"""
        try:
            with open('published_news.json', 'w', encoding='utf-8') as f:
                json.dump({'published': list(self.published_news)}, f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving published news: {e}")

    async def init_session(self):
        """Инициализация HTTP сессии"""
        self.session = aiohttp.ClientSession()

    async def close_session(self):
        """Закрытие HTTP сессии"""
        if self.session:
            await self.session.close()

    async def get_investing_news(self):
        """Парсинг новостей с Investing.com"""
        try:
            url = "https://ru.investing.com/news/cryptocurrency-news"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            async with self.session.get(url, headers=headers) as response:
                html = await response.text()

            soup = BeautifulSoup(html, 'html.parser')
            articles = []

            news_items = soup.find_all('article', class_='js-article-item')[:10]

            for item in news_items:
                try:
                    title_elem = item.find('a', class_='title')
                    if title_elem:
                        title = title_elem.text.strip()
                        link = title_elem.get('href', '')
                        if link and not link.startswith('http'):
                            link = 'https://ru.investing.com' + link

                        news_id = hash(title)
                        if news_id not in self.published_news:
                            articles.append({
                                'title': title,
                                'link': link,
                                'source': 'Investing.com',
                                'id': news_id
                            })
                except Exception:
                    continue

            return articles
        except Exception as e:
            logger.error(f"Error parsing Investing.com: {e}")
            return []

    async def get_cointelegraph_news(self):
        """Парсинг новостей с Cointelegraph"""
        try:
            url = "https://cointelegraph.com/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            async with self.session.get(url, headers=headers) as response:
                html = await response.text()

            soup = BeautifulSoup(html, 'html.parser')
            articles = []

            news_items = soup.find_all('article')[:15]

            for item in news_items:
                try:
                    title_elem = item.find('h3') or item.find('h2') or item.find('span', class_='post-card__title')
                    if title_elem:
                        title = title_elem.text.strip()

                        link_elem = item.find('a')
                        link = link_elem.get('href', '') if link_elem else ""
                        if link and not link.startswith('http'):
                            link = 'https://cointelegraph.com' + link

                        news_id = hash(title)
                        if news_id not in self.published_news:
                            articles.append({
                                'title': title,
                                'link': link,
                                'source': 'Cointelegraph',
                                'id': news_id
                            })
                except Exception:
                    continue

            return articles
        except Exception as e:
            logger.error(f"Error parsing Cointelegraph: {e}")
            return []

    async def get_economic_events(self):
        """Парсинг экономического календаря"""
        try:
            url = "https://ru.investing.com/economic-calendar/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            async with self.session.get(url, headers=headers) as response:
                html = await response.text()

            soup = BeautifulSoup(html, 'html.parser')
            events = []

            event_rows = soup.find_all('tr', id=lambda x: x and x.startswith('eventRowId'))[:5]

            for row in event_rows:
                try:
                    time_elem = row.find('td', class_='time')
                    event_elem = row.find('td', class_='event')

                    if time_elem and event_elem:
                        time_str = time_elem.text.strip()
                        event_name = event_elem.text.strip()

                        importance_elem = row.find('td', class_='sentiment')
                        importance = "Средняя"
                        if importance_elem:
                            bull_count = len(importance_elem.find_all('i', class_='grayFullBull'))
                            if bull_count >= 3:
                                importance = "Высокая"
                            elif bull_count == 2:
                                importance = "Средняя"
                            else:
                                importance = "Низкая"

                        events.append({
                            'time': time_str,
                            'event': event_name,
                            'importance': importance
                        })
                except Exception:
                    continue

            return events
        except Exception as e:
            logger.error(f"Error parsing economic calendar: {e}")
            return []

    def create_news_image(self, title, source):
        """Создание изображения для поста с фиксированным логотипом"""
        try:
            width, height = 800, 600
            # Создаем градиентный фон
            image = Image.new('RGB', (width, height), color=(13, 17, 23))
            draw = ImageDraw.Draw(image)

            # Яркий градиент для привлечения внимания
            for i in range(height):
                r = int(25 + (i / height) * 50)
                g = int(30 + (i / height) * 40)
                b = int(45 + (i / height) * 60)
                draw.line([(0, i), (width, i)], fill=(r, g, b))

            # Добавляем логотип (если он есть)
            if self.logo:
                image.paste(self.logo, (width - 210, 20))

            # Загружаем шрифты
            try:
                font_large = ImageFont.truetype("arial.ttf", 36)
                font_medium = ImageFont.truetype("arial.ttf", 24)
                font_small = ImageFont.truetype("arial.ttf", 18)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()

            # Добавляем виральную фразу
            viral_phrase = random.choice(self.viral_phrases)
            bbox = draw.textbbox((0, 0), viral_phrase, font=font_medium)
            text_width = bbox[2] - bbox[0]
            draw.text(((width - text_width) // 2, 120), viral_phrase,
                      fill=(255, 215, 0), font=font_medium)

            # Разбиваем заголовок на строки
            words = title.split()
            lines = []
            current_line = []

            for word in words:
                test_line = ' '.join(current_line + [word])
                if len(test_line) < 40:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]

            if current_line:
                lines.append(' '.join(current_line))

            # Ограничиваем количество строк
            lines = lines[:4]

            # Рисуем заголовок с тенью для эффектности
            y_position = 180
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font_large)
                text_width = bbox[2] - bbox[0]
                x_position = (width - text_width) // 2

                # Тень
                draw.text((x_position + 2, y_position + 2), line,
                          fill=(0, 0, 0), font=font_large)
                # Основной текст
                draw.text((x_position, y_position), line,
                          fill=(255, 255, 255), font=font_large)
                y_position += 50

            # Добавляем разделитель
            draw.line([(50, y_position + 20), (width - 50, y_position + 20)],
                      fill=(255, 215, 0), width=3)

            # Добавляем источник и время
            timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
            source_text = f"📰 {source} | 🕐 {timestamp}"
            bbox = draw.textbbox((0, 0), source_text, font=font_small)
            text_width = bbox[2] - bbox[0]
            draw.text(((width - text_width) // 2, height - 80), source_text,
                      fill=(200, 200, 200), font=font_small)

            # Добавляем призыв к действию
            cta_text = "👉 ПОДПИСЫВАЙСЯ И ЖМИ 👍"
            bbox = draw.textbbox((0, 0), cta_text, font=font_medium)
            text_width = bbox[2] - bbox[0]
            draw.text(((width - text_width) // 2, height - 40), cta_text,
                      fill=(255, 215, 0), font=font_medium)

            img_buffer = io.BytesIO()
            image.save(img_buffer, format='PNG', quality=95)
            img_buffer.seek(0)

            return img_buffer

        except Exception as e:
            logger.error(f"Error creating image: {e}")
            # Запасной вариант
            image = Image.new('RGB', (800, 600), color=(13, 17, 23))
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            return img_buffer

    async def send_photo_message(self, image_buffer, caption):
        """Отправка сообщения с фото в Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendPhoto"

            files = {
                'photo': ('news.png', image_buffer.getvalue(), 'image/png')
            }

            data = {
                'chat_id': self.channel,
                'caption': caption,
                'parse_mode': 'HTML'
            }

            response = requests.post(url, files=files, data=data, timeout=30)

            if response.status_code == 200:
                logger.info("✅ Photo message sent successfully!")
                return True
            else:
                logger.error(f"❌ Failed to send photo: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Error sending photo: {e}")
            return False

    async def get_real_news(self):
        """Получение реальных новостей со всех источников"""
        all_articles = []

        investing_news = await self.get_investing_news()
        all_articles.extend(investing_news)

        cointelegraph_news = await self.get_cointelegraph_news()
        all_articles.extend(cointelegraph_news)

        random.shuffle(all_articles)
        return all_articles[:5]

    def format_post_text(self, article, economic_events=None):
        """Форматирование байтового текста поста"""
        title = article['title']
        source = article['source']
        link = article['link']

        # Байтовое начало
        emoji = random.choice(self.emojis)
        start_phrase = random.choice([
            f"{emoji} ВАЖНЕЙШАЯ ИНФА ПО ТРЕЙДУ!",
            f"{emoji} ХАЙПАНЕМ НА ЭТОЙ НОВОСТИ!",
            f"{emoji} ТО, ЧТО ВСЕ ЖДАЛИ!",
            f"{emoji} СЕКРЕТНЫЙ ИНСАЙД!",
            f"{emoji} ЛУЧШИЙ ПОВОД ДЛЯ ВХОДА!"
        ])

        post_text = f"<b>{start_phrase}</b>\n\n"
        post_text += f"📢 {title}\n\n"

        # Добавляем эмоциональную реакцию
        reaction = random.choice([
            "💥 Это может изменить всё!",
            "🚀 Заряжаем ракеты!",
            "💎 Алмазные руки знают!",
            "🔥 Готовьте свои портфели!",
            "🎯 Идеальный момент для действия!"
        ])
        post_text += f"{reaction}\n\n"

        if link:
            post_text += f"🔗 <a href='{link}'>ЧИТАТЬ ПОДРОБНЕЕ</a>\n\n"

        # Добавляем экономические события если есть
        if economic_events:
            post_text += "📅 <b>СЕГОДНЯ В ФОКУСЕ:</b>\n"
            for event in economic_events[:2]:
                importance_icon = "🔴" if event['importance'] == "Высокая" else "🟡" if event[
                                                                                          'importance'] == "Средняя" else "🟢"
                post_text += f"{importance_icon} {event['time']} - {event['event']}\n"
            post_text += "\n"

        # Призыв к действию
        cta = random.choice([
            "💬 ЖДУ ВАШЕ МНЕНИЕ В КОММЕНТАХ!",
            "👍 ЛАЙК ЕСЛИ АКТУАЛЬНО!",
            "🔔 ПОДПИСЫВАЙСЯ ЧТОБЫ НЕ ПРОПУСТИТЬ!",
            "🔄 РЕПОСТ ДРУЗЬЯМ-ТРЕЙДЕРАМ!"
        ])
        post_text += f"{cta}\n\n"

        # Хештеги
        post_text += "#Crypto #Трейдинг #Инвестиции #Новости"

        # Контекстные хештеги
        if any(word in title.lower() for word in ['bitcoin', 'btc', 'биткоин']):
            post_text += " #Bitcoin #BTC"
        elif any(word in title.lower() for word in ['ethereum', 'eth', 'эфириум']):
            post_text += " #Ethereum #ETH"
        elif any(word in title.lower() for word in ['defi', 'дефи']):
            post_text += " #DeFi"
        elif any(word in title.lower() for word in ['nft', 'энфт']):
            post_text += " #NFT"

        return post_text

    async def publish_news_round(self):
        """Один цикл публикации новостей"""
        try:
            logger.info("🔄 Starting news publishing round...")

            fresh_news = await self.get_real_news()

            if not fresh_news:
                logger.warning("No fresh news found")
                backup_news = [
                    "📊 Рынок криптовалют показывает стабильный рост - идеальное время для инвестиций!",
                    "💡 Новые технологии блокчейн развиваются быстрыми темпами - не пропусти волну!",
                    "🌍 Крипто-индустрия привлекает все больше инвесторов - присоединяйся к успеху!"
                ]
                article = {
                    'title': random.choice(backup_news),
                    'source': 'ANT CAPITAL',
                    'link': '',
                    'id': hash(str(datetime.now()))
                }
                fresh_news = [article]

            economic_events = await self.get_economic_events()
            article = random.choice(fresh_news)

            image = self.create_news_image(article['title'], article['source'])
            post_text = self.format_post_text(article, economic_events)

            success = await self.send_photo_message(image, post_text)

            if success:
                self.published_news.add(article['id'])
                self.save_published_news()
                logger.info(f"✅ Successfully published: {article['title']}")
            else:
                logger.error(f"❌ Failed to publish: {article['title']}")

        except Exception as e:
            logger.error(f"❌ Error in publishing round: {e}")

    async def run(self):
        """Основной цикл бота"""
        await self.init_session()

        logger.info("🤖 ANT CAPITAL Crypto Bot Started!")
        logger.info(f"📢 Channel: {self.channel}")
        logger.info(f"🔑 Using token: {self.token[:10]}...")

        # Байтовое приветственное сообщение
        test_msg = "🚀 <b>ANT CAPITAL В ЭФИРЕ!</b>\n\n💎 Запускаем самый хайповый крипто-канал!\n📈 Только актуальные новости и инсайды\n🎯 То, что нужно каждому трейдеру\n\n🔔 ПОДПИСЫВАЙСЯ И ЖМИ НА КОЛОКОЛЬЧИК!\n\n#ANT_CAPITAL #Запуск #Крипта"
        await self.send_message(test_msg)

        await asyncio.sleep(60)
        await self.publish_news_round()

        # Умный планировщик публикаций
        publish_times = ["09:00", "12:00", "15:00", "18:00", "21:00"]

        while True:
            try:
                current_time = datetime.now().strftime("%H:%M")
                if current_time in publish_times:
                    await self.publish_news_round()
                    # Ждем до следующего времени публикации
                    await asyncio.sleep(3600)  # 1 час
                else:
                    # Проверяем каждые 30 минут
                    await asyncio.sleep(1800)

            except Exception as e:
                logger.error(f"❌ Error in main loop: {e}")
                await asyncio.sleep(300)

    async def send_message(self, text):
        """Отправка простого текстового сообщения"""
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        data = {
            'chat_id': self.channel,
            'text': text,
            'parse_mode': 'HTML'
        }

        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                logger.info("✅ Message sent successfully!")
                return True
            else:
                logger.error(f"❌ Failed to send: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return False


async def main():
    bot = CryptoNewsBot(Config.TELEGRAM_BOT_TOKEN, Config.CHANNEL_ID)
    try:
        await bot.run()
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    finally:
        await bot.close_session()


if __name__ == "__main__":
    asyncio.run(main())