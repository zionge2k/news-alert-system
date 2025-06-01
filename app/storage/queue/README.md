# Queue 시스템 문서

MongoDB 기반의 뉴스 기사 큐 시스템입니다. 크롤링된 기사를 Discord에 발행하기 전에 버퍼링하고 관리합니다.

## 목차
- [전체 아키텍처](#전체-아키텍처-다이어그램)
- [큐 아이템 상태](#큐-아이템-상태-다이어그램)
- [주요 메서드 흐름](#주요-메서드-흐름도)
- [클래스 구조](#클래스-관계-다이어그램)
- [데이터 흐름](#데이터-흐름-시퀀스-다이어그램)

## 전체 아키텍처 다이어그램

```mermaid
graph TB
    subgraph "데이터 소스"
        A[MongoDB Articles Collection]
    end
    
    subgraph "Queue 시스템"
        B[QueueInterface<br/>추상 인터페이스]
        C[MongoDBQueue<br/>구현체]
        D[QueueService<br/>비즈니스 로직]
        E[MongoDB Queue Collection]
    end
    
    subgraph "발행 시스템"
        F[Discord Publisher Service]
        G[Published Articles Storage]
    end
    
    A -->|기사 조회| D
    B -.->|구현| C
    D -->|사용| C
    C <-->|CRUD| E
    D -->|큐 아이템 제공| F
    F -->|발행 완료| G
    F -->|상태 업데이트| D
```

## 큐 아이템 상태 다이어그램

```mermaid
stateDiagram-v2
    [*] --> PENDING: enqueue()
    PENDING --> PROCESSING: dequeue()
    PROCESSING --> COMPLETED: mark_as_completed()
    PROCESSING --> FAILED: mark_as_failed()
    FAILED --> PENDING: retry_failed()<br/>(retry_count < max_retries)
    FAILED --> [*]: 최대 재시도 초과
    COMPLETED --> [*]: clean_completed()
    
    note right of PENDING
        대기 중인 상태
        - 새로 추가된 아이템
        - 재시도 대기 아이템
    end note
    
    note right of PROCESSING
        처리 중인 상태
        - dequeue()로 가져간 아이템
        - Discord 발행 진행 중
    end note
    
    note right of COMPLETED
        완료된 상태
        - Discord 발행 성공
        - published_at 기록
    end note
    
    note right of FAILED
        실패한 상태
        - 발행 중 오류 발생
        - retry_count 증가
        - error_message 저장
    end note
```

## 주요 메서드 흐름도

```mermaid
flowchart TD
    Start([시작])
    
    subgraph "기사 추가 프로세스"
        A1[add_articles_from_db]
        A2{플랫폼/카테고리<br/>필터링}
        A3[MongoDB에서<br/>기사 조회]
        A4{이미 발행됨?}
        A5{중복 체크}
        A6[QueueItem 생성]
        A7[enqueue 호출]
        A8[MongoDB에 저장]
    end
    
    subgraph "기사 처리 프로세스"
        B1[get_pending_articles]
        B2[dequeue 호출]
        B3[find + find_one_and_update<br/>atomic operation]
        B4{업데이트 성공?}
        B5[상태를 PROCESSING으로 변경]
        B6[QueueItem 반환]
    end
    
    subgraph "발행 후 처리"
        C1{발행 성공?}
        C2[mark_as_completed]
        C3[mark_as_failed]
        C4[retry_count 증가]
        C5{재시도 가능?}
        C6[retry_failed]
    end
    
    Start --> A1
    A1 --> A2
    A2 --> A3
    A3 --> A4
    A4 -->|아니오| A5
    A4 -->|예| End1([건너뜀])
    A5 -->|중복 아님| A6
    A5 -->|중복| End2([건너뜀])
    A6 --> A7
    A7 --> A8
    
    A8 --> B1
    B1 --> B2
    B2 --> B3
    B3 --> B4
    B4 -->|예| B5
    B4 -->|아니오<br/>Race Condition| End3([다른 워커가 처리])
    B5 --> B6
    
    B6 --> C1
    C1 -->|성공| C2
    C1 -->|실패| C3
    C3 --> C4
    C4 --> C5
    C5 -->|예| C6
    C6 --> B1
    C5 -->|아니오| End4([최종 실패])
```

## 클래스 관계 다이어그램

```mermaid
classDiagram
    class QueueInterface {
        <<interface>>
        +enqueue(item: QueueItem) bool
        +dequeue(limit: int) List~QueueItem~
        +mark_as_completed(item_id: str) bool
        +mark_as_failed(item_id: str, error_message: str) bool
        +retry_failed(max_retries: int) int
        +is_duplicate(unique_id: str) bool
        +get_status() dict
        +clean_completed() int
    }
    
    class MongoDBQueue {
        -collection_name: str
        +collection: Collection
        +enqueue(item: QueueItem) bool
        +dequeue(limit: int) List~QueueItem~
        +mark_as_completed(item_id: str) bool
        +mark_as_failed(item_id: str, error_message: str) bool
        +retry_failed(max_retries: int) int
        +is_duplicate(unique_id: str) bool
        +get_status() dict
        +clean_completed() int
    }
    
    class QueueService {
        -queue: QueueInterface
        +add_articles_from_db(platform, category, limit, hours) int
        +get_pending_articles(limit: int) List~QueueItem~
        +mark_article_published(unique_id: str) bool
        +mark_article_failed(unique_id: str, error_message: str) bool
        +retry_failed_articles(max_retries: int) int
        +get_queue_status() dict
        +clean_old_articles() int
    }
    
    class QueueItem {
        +article_id: str
        +platform: str
        +title: str
        +url: str
        +unique_id: str
        +content: Optional~str~
        +category: Optional~str~
        +published_at: Optional~datetime~
        +status: str
        +retry_count: int
        +error_message: Optional~str~
        +created_at: datetime
        +updated_at: datetime
    }
    
    class QueueStatus {
        <<enumeration>>
        PENDING
        PROCESSING
        COMPLETED
        FAILED
    }
    
    QueueInterface <|.. MongoDBQueue : implements
    QueueService --> QueueInterface : uses
    QueueService --> QueueItem : manages
    QueueItem --> QueueStatus : uses
    MongoDBQueue --> MongoDB : connects to
```

## 데이터 흐름 시퀀스 다이어그램

```mermaid
sequenceDiagram
    participant Article as MongoDB Articles
    participant Service as QueueService
    participant Queue as MongoDBQueue
    participant QueueDB as Queue Collection
    participant Publisher as Discord Publisher
    
    Note over Article,Publisher: 기사 큐 추가 프로세스
    Article->>Service: 기사 조회
    Service->>Service: 발행 여부 확인
    Service->>Queue: is_duplicate()
    Queue->>QueueDB: find_one()
    QueueDB-->>Queue: 중복 여부
    Queue-->>Service: false (중복 아님)
    Service->>Queue: enqueue(QueueItem)
    Queue->>QueueDB: insert_one()
    QueueDB-->>Queue: 성공
    
    Note over Article,Publisher: 기사 처리 프로세스
    Publisher->>Service: get_pending_articles()
    Service->>Queue: dequeue(limit)
    Queue->>QueueDB: find(PENDING).sort()
    loop 각 문서에 대해
        Queue->>QueueDB: find_one_and_update()<br/>PENDING→PROCESSING
        QueueDB-->>Queue: updated_doc or None
    end
    Queue-->>Service: List[QueueItem]
    Service-->>Publisher: 처리할 기사들
    
    Note over Article,Publisher: 발행 후 처리
    alt 발행 성공
        Publisher->>Service: mark_article_published()
        Service->>Queue: mark_as_completed()
        Queue->>QueueDB: update_one()<br/>→COMPLETED
    else 발행 실패
        Publisher->>Service: mark_article_failed()
        Service->>Queue: mark_as_failed()
        Queue->>QueueDB: update_one()<br/>→FAILED, retry_count++
    end
```

## 주요 기능

### 1. 중복 방지
- `unique_id`를 통한 중복 체크
- MongoDB unique index로 보장

### 2. 동시성 처리
- `find_one_and_update()`를 사용한 atomic operation
- Race condition 방지

### 3. 재시도 로직
- 실패한 아이템의 `retry_count` 관리
- 최대 재시도 횟수 제한

### 4. 상태 관리
- PENDING → PROCESSING → COMPLETED/FAILED
- 각 상태별 타임스탬프 기록
