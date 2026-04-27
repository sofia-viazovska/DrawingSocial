# Лабораторна робота №2: Domain-Driven Design та Шарова архітектура

## Виконання завдання

У ході лабораторної роботи проект було рефакторовано з монолітної структури до чистої архітектури (Clean Architecture). Нижче наведено детальний опис реалізації згідно з вимогами.

### 1. Виділення доменних моделей
Створено доменні моделі, які повністю незалежні від зовнішніх фреймворків та БД (`app/domain/models/models.py`).
- **Моделі**: `User`, `Drawing`, `Layer`.
- **Підхід**: Обрано **Rich Domain Model**. Логіка та захист інваріантів перенесені безпосередньо в класи моделей.
- **Приклади інваріантів**:
    - `User.follow(user_id)`: заборона підписки на самого себе.
    - `Drawing.add_layer(author_id, image_data)`: перевірка на наявність даних зображення.
    - `Drawing.toggle_like(user_id)`: логіка додавання/видалення лайка.
- **Мапінг**: Реалізовано в `app/infrastructure/mappers/mappers.py` (класи `UserMapper`, `DrawingMapper`, `LayerMapper`).

### 2. Реалізація Domain Factory
Створено фабрику (`app/domain/factories/factories.py`) для централізованого створення об'єктів з перевіркою правил.
- **Прості інваріанти**: Перевірка формату email через регулярні вирази, перевірка обов'язковості нікнейму та назви малюнку.
- **Складні інваріанти**: Перевірка унікальності email та нікнейму. Фабрика використовує інтерфейс `UserRepository` для запитів до бази даних.
- **Помилки**: У разі порушень викидаються специфічні доменні помилки: `InvalidEmailError`, `EmailAlreadyExistsError`, `InvariantViolationError` (визначені в `app/domain/exceptions/exceptions.py`).

### 3. Виділення 4 шарів
Проект розділено на чіткі пакети з дотриманням правила залежностей (Presentation -> Application -> Domain <- Infrastructure).

- **Domain Layer** (`app/domain/`):
    - `models/`: Бізнес-сутності.
    - `repositories/`: Інтерфейси для доступу до даних (Ports).
    - `factories/`: Фабрики для створення сутностей.
    - `exceptions/`: Доменні винятки.
- **Application Layer** (`app/application/`):
    - `use_cases/services.py`: Сценарії використання (`UserUseCases`, `DrawingUseCases`). Оркестрація роботи домену та репозиторіїв.
- **Infrastructure Layer** (`app/infrastructure/`):
    - `db/models/`: SQLAlchemy моделі (Entities).
    - `repositories/`: Реалізація репозиторіїв (Adapters).
    - `mappers/`: Перетворення між Domain та DB моделями.
- **Presentation Layer** (`app/presentation/`):
    - `api/`: FastAPI роутери та обробка HTTP.
    - `schemas/`: Pydantic моделі (DTO).

### 4. Рефакторинг тестів
Тести розділені за рівнями відповідальності та запускаються без зайвих залежностей.
- **Unit-тести домену** (`tests/test_domain.py`): Тестування логіки моделей та фабрики без БД. Репозиторії замінені на `MagicMock`.
- **Unit-тести Application Layer** (`tests/test_application.py`): Тестування Use Cases, перевірка правильної послідовності викликів домену та репозиторіїв.
- **Integration-тести** (`tests/test_api.py`): Повна перевірка API ендпоінтів з використанням тестової бази даних `test.db`.

### 5. Аналіз та ADR
- **ADR**: Обґрунтування вибору Rich Domain Model зафіксовано в `docs/adr/001_rich_domain_model.md`.
- **Порівняльний аналіз**: Детальний розбір переваг та недоліків нової архітектури представлено у `docs/analysis/lab2.md`.

## Результати
- Всі 17 тестів (unit та integration) проходять успішно.
- Доменний шар повністю ізольований від інфраструктури (немає імпортів `sqlalchemy` або `fastapi`).
- Реалізовано DIP: інфраструктура залежить від інтерфейсів, визначених у домені.
