# Discord 뉴스 알림 봇

## 소개

이 모듈은 Discord를 통해 뉴스 알림을 제공하는 간단한 봇을 구현합니다. 크롤링되어 정제된 데이터(ArticleDTO)를 이용해 채널 채팅방에 타이틀, 링크, 설명을 전송합니다.

## 기능

- 뉴스 기사 알림 전송 (임베드 형식)
- 정제된 ArticleDTO를 이용한 간단한 메시지 포맷팅

## 사용 방법

### 봇 설정하기

1. [Discord Developer Portal](https://discord.com/developers/applications)에서 봇을 생성하고 토큰을 얻습니다.
2. 프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가합니다:

```text
# MongoDB 연결 설정
MONGODB_URL=mongodb://root:1234@localhost:27017
MONGODB_DB_NAME=news_alert

# Discord 봇 설정
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# 로깅 설정
LOG_LEVEL=INFO
```

3. `DISCORD_BOT_TOKEN` 값을 Discord Developer Portal에서 얻은 토큰으로 변경합니다.

### 봇 실행하기

다음 명령어로 봇을 실행합니다:

```bash
python scripts/run_discord_bot.py
```

### 코드에서 사용하기

다음과 같이 코드에서 뉴스 알림을 전송할 수 있습니다:

```python
from app.notifier.discord.bot import NewsAlertBot

# 봇 인스턴스 생성
bot = NewsAlertBot()

# ArticleDTO 객체와 채널 ID가 있을 때
await bot.send_news_alert(article_dto, channel_id)
```

## 개발자 정보

### 코드 구조

- `interfaces.py`: 메시지 포맷팅 인터페이스를 정의합니다.
  - `MessageFormatter`: 메시지 포맷팅 인터페이스

- `services.py`: 인터페이스 구현체를 제공합니다.
  - `NewsEmbedFormatter`: 뉴스 임베드 포매터 구현

- `bot.py`: Discord 봇 구현을 담당합니다.
  - `NewsAlertBot`: 메인 봇 클래스
  - `run_bot()`: 봇 실행 함수

### 확장하기

새로운 포맷터를 추가하려면 `MessageFormatter` 인터페이스를 구현하면 됩니다:

```python
from app.notifier.discord.interfaces import MessageFormatter

class SimpleMessageFormatter(MessageFormatter):
    """간단한 포맷의 메시지 포매터"""
    
    def create_embed(self, article):
        # 간단한 임베드 생성 로직
        return discord.Embed(title=article.title, url=article.url) 