"""
Модели базы данных для бота
"""
from datetime import datetime
from typing import List
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, Table, Column, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# Таблица связи многие-ко-многим для пользователей и тегов
user_tags = Table(
    'user_tags',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

# Таблица связи пользователей и кампаний
user_campaigns = Table(
    'user_campaigns',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('campaign_id', Integer, ForeignKey('campaigns.id'), primary_key=True),
    Column('activated_at', DateTime, default=datetime.utcnow)
)


class User(Base):
    """Модель пользователя"""
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default='en')
    source: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    tags: Mapped[List["Tag"]] = relationship(
        secondary=user_tags,
        back_populates="users"
    )
    campaigns: Mapped[List["Campaign"]] = relationship(
        secondary=user_campaigns,
        back_populates="users"
    )
    
    def __repr__(self):
        return f"<User {self.telegram_id} ({self.full_name})>"


class Tag(Base):
    """Модель тега для сегментации"""
    __tablename__ = 'tags'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Связи
    users: Mapped[List["User"]] = relationship(
        secondary=user_tags,
        back_populates="tags"
    )
    
    def __repr__(self):
        return f"<Tag {self.name}>"


class Settings(Base):
    """Модель настроек бота"""
    __tablename__ = 'settings'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Settings {self.key}={self.value}>"


class AutoMessage(Base):
    """Модель автоматического сообщения с задержкой"""
    __tablename__ = 'auto_messages'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))  # Название для админа
    delay_minutes: Mapped[int] = mapped_column(Integer)  # Задержка в минутах
    
    # Сообщения на разных языках
    message_pt: Mapped[str | None] = mapped_column(Text, nullable=True)
    message_hu: Mapped[str | None] = mapped_column(Text, nullable=True)
    message_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Медиа (photo/video) - file_id или URL
    media_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # photo, video, None
    media_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Кнопки в формате JSON: [{"text": "название", "url": "ссылка"}, ...]
    buttons_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Фильтры (опционально)
    target_language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    target_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def get_message(self, language: str) -> str:
        """Получить сообщение на нужном языке"""
        messages = {
            'pt': self.message_pt,
            'hu': self.message_hu,
            'en': self.message_en
        }
        return messages.get(language) or self.message_en or ""
    
    def __repr__(self):
        return f"<AutoMessage {self.name} delay={self.delay_minutes}min>"


class SentAutoMessage(Base):
    """Лог отправленных автоматических сообщений (чтобы не дублировать)"""
    __tablename__ = 'sent_auto_messages'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    auto_message_id: Mapped[int] = mapped_column(Integer, ForeignKey('auto_messages.id'))
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<SentAutoMessage user={self.user_id} msg={self.auto_message_id}>"


class Language(Base):
    """Supported languages"""
    __tablename__ = 'languages'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True)  # en, pt, hu
    name: Mapped[str] = mapped_column(String(100))  # English, Portuguese
    flag: Mapped[str] = mapped_column(String(10))  # 🇬🇧, 🇵🇹
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Language {self.code} - {self.name}>"


class BotText(Base):
    """All bot messages - editable via admin panel"""
    __tablename__ = 'bot_texts'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(100), index=True)  # welcome, hello, subscribe_channel
    language: Mapped[str] = mapped_column(String(10), index=True)  # en, pt, hu
    text: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)  # For admin reference
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint: one text per key+language
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )
    
    def __repr__(self):
        return f"<BotText {self.key}:{self.language}>"


class Campaign(Base):
    """Модель кампании/оффера"""
    __tablename__ = 'campaigns'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Сообщения по языкам (JSON или отдельные поля)
    message_pt: Mapped[str | None] = mapped_column(Text, nullable=True)
    message_hu: Mapped[str | None] = mapped_column(Text, nullable=True)
    message_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Медиа (photo/video) - file_id или URL
    media_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # photo, video, None
    media_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Кнопки в формате JSON: [{"text": "название", "url": "ссылка"}, ...]
    buttons_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Активность по времени
    active_from: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    active_to: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Флаги
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)  # Если только для одного языка
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Связи
    users: Mapped[List["User"]] = relationship(
        secondary=user_campaigns,
        back_populates="campaigns"
    )
    
    def get_message(self, user_language: str) -> str:
        """Получить сообщение на языке пользователя"""
        messages = {
            'pt': self.message_pt,
            'hu': self.message_hu,
            'en': self.message_en
        }
        return messages.get(user_language) or self.message_en or ""
    
    def is_currently_active(self) -> bool:
        """Проверить, активна ли кампания сейчас"""
        if not self.is_active:
            return False
        
        now = datetime.utcnow()
        if now < self.active_from:
            return False
        
        if self.active_to and now > self.active_to:
            return False
        
        return True
    
    def __repr__(self):
        return f"<Campaign {self.code}>"

