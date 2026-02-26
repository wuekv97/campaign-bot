"""
Утилиты для работы с deep links
"""
from urllib.parse import quote


def generate_start_link(bot_username: str, payload: str = None) -> str:
    """
    Генерация ссылки для старта бота с payload
    
    Args:
        bot_username: Username бота (без @)
        payload: Payload для передачи (source, campaign code, etc)
    
    Returns:
        Готовая ссылка для распространения
    
    Examples:
        >>> generate_start_link("MyCampaignBot", "offer_black_friday")
        'https://t.me/MyCampaignBot?start=offer_black_friday'
        
        >>> generate_start_link("MyCampaignBot", "email_campaign_01")
        'https://t.me/MyCampaignBot?start=email_campaign_01'
    """
    if payload:
        return f"https://t.me/{bot_username}?start={quote(payload)}"
    return f"https://t.me/{bot_username}"


def generate_campaign_link(bot_username: str, campaign_code: str) -> str:
    """
    Генерация ссылки для кампании/оффера
    
    Args:
        bot_username: Username бота (без @)
        campaign_code: Код кампании
    
    Returns:
        Ссылка для активации кампании
    """
    return generate_start_link(bot_username, campaign_code)


def generate_source_link(bot_username: str, source: str) -> str:
    """
    Генерация ссылки с меткой источника
    
    Args:
        bot_username: Username бота (без @)
        source: Источник трафика
    
    Returns:
        Ссылка с меткой источника
    """
    return generate_start_link(bot_username, source)


def print_campaign_links(bot_username: str, campaigns: list):
    """
    Вывести красиво отформатированные ссылки для кампаний
    
    Args:
        bot_username: Username бота
        campaigns: Список кампаний
    """
    print("\n" + "=" * 60)
    print(f"🔗 ССЫЛКИ ДЛЯ РАСПРОСТРАНЕНИЯ (@{bot_username})")
    print("=" * 60)
    
    for campaign in campaigns:
        link = generate_campaign_link(bot_username, campaign.code)
        print(f"\n📍 {campaign.title}")
        print(f"   Код: {campaign.code}")
        print(f"   Ссылка: {link}")
        
        # Примеры использования
        print(f"\n   📱 HTML для email/сайта:")
        print(f'   <a href="{link}">Получить бонус!</a>')
        
        print(f"\n   📝 Markdown для Telegram:")
        print(f'   [Получить бонус!]({link})')
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Примеры использования
    bot_username = "MyCampaignBot"  # Замените на username вашего бота
    
    print("\n🔗 Примеры генерации ссылок:\n")
    
    # Кампания
    campaign_link = generate_campaign_link(bot_username, "offer_black_friday")
    print(f"Кампания Black Friday:\n{campaign_link}\n")
    
    # Источник
    source_link = generate_source_link(bot_username, "instagram_story_2025_11_30")
    print(f"Instagram Story:\n{source_link}\n")
    
    # Email кампания
    email_link = generate_source_link(bot_username, "email_newsletter_001")
    print(f"Email рассылка #001:\n{email_link}\n")

