# Запись в автомастерскую

Учебный backend-проект к [концепту шиномонтажа](../tire/).
Django, Django REST Framework, PostgreSQL / SQLite. Это отдельное приложение:
существующий статический сайт не отправляет в него заявки.

Клиент выбирает услугу и желаемое время, оставляет телефон, видит свои заявки
и может отменить запись. Администратор подтверждает время через Django Admin.
Все цены демонстрационные; реальная мастерская к проекту не подключена.

## Запуск

Python 3.12 или новее. Из корня репозитория:

```powershell
cd workshop-backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_services
python manage.py createsuperuser
python manage.py runserver
```

Linux / macOS: вместо команды активации выше используйте `source .venv/bin/activate`.

Откройте http://127.0.0.1:8000/ и войдите с созданным аккаунтом.
Заявки и услуги доступны администратору по /admin/.
Для второго клиента создайте обычного пользователя через админку.
Регистрации по email и восстановления пароля в этой версии нет.

По умолчанию используется SQLite: для знакомства отдельный сервер БД не нужен.
Для PostgreSQL создайте базу и задайте переменные **до** migrate:

```powershell
$env:POSTGRES_DB = "workshop"
$env:POSTGRES_USER = "workshop"
$env:POSTGRES_PASSWORD = "<ваш пароль>"
$env:POSTGRES_HOST = "127.0.0.1"
$env:POSTGRES_PORT = "5432"
python manage.py migrate
```

Пароль не хранится в репозитории. Файл .env автоматически не загружается.

## REST API

API принимает JSON. Для запросов из браузерного интерфейса используются сессии
и CSRF; для внешнего клиента — токен. Получите токен существующего пользователя:

```console
python manage.py drf_create_token <username>
```

| Метод | Адрес | Доступ и результат |
| --- | --- | --- |
| GET | /api/services/ | Публичный список активных услуг, 200 |
| POST | /api/bookings/ | Создание своей заявки, 201 |
| GET | /api/bookings/ | Только свои заявки, 200 |
| GET | /api/bookings/{id}/ | Своя заявка, 200; чужая или отсутствующая — 404 |
| POST | /api/bookings/{id}/cancel/ | Отмена своей заявки, 200; повторная отмена допустима |

Списки возвращают `count`, `next`, `previous`, `results`. По 20 записей на страницу.

Пример для PowerShell (ID услуги возьмите из GET /api/services/):

```powershell
$headers = @{Authorization = "Token <ваш токен>"}
$body = @{
    service = 1
    requested_at = (Get-Date).AddDays(1).ToString("o")
    phone = "+7 900 123-45-67"
    comment = "Сезонная смена шин"
} | ConvertTo-Json

Invoke-RestMethod http://127.0.0.1:8000/api/services/
Invoke-RestMethod http://127.0.0.1:8000/api/bookings/ -Method Post -Headers $headers -ContentType "application/json" -Body $body
Invoke-RestMethod http://127.0.0.1:8000/api/bookings/ -Headers $headers
```

Невалидные поля, прошедшее время и повторная активная заявка возвращают 400.
Без токена или сессии защищённые API возвращают 401.
При сессионном POST без CSRF — 403. PATCH и DELETE не поддерживаются (405).
Владелец и статус назначаются сервером: передать чужой user или подтвердить
заявку через POST нельзя.

## Устройство

- `models.py`: Service и Booking; пользователь связан через стандартную модель Django.
- `serializers.py` / `forms.py`: проверка данных API и HTML-формы.
- `services.py`: создание и отмена; журнал содержит ID, без телефонов и комментариев.
- `views.py`: API и страницы на Django templates. Выборка заявок ограничена владельцем.
- `admin.py`: редактирование услуг и статусов заявок.
- `migrations/`: схема БД и ограничения.

Уникальное ограничение БД не даёт создать две активные заявки одного клиента
на одну услугу и время, включая одновременные запросы. Отменённая заявка
остаётся в истории. `select_related("service")` загружает услуги без отдельного
запроса для каждой строки списка.

Пример SQL со связями:

```sql
SELECT b.id, u.username, s.name, b.requested_at, b.status
FROM bookings_booking AS b
JOIN auth_user AS u ON u.id = b.user_id
JOIN bookings_service AS s ON s.id = b.service_id
WHERE b.user_id = 1
ORDER BY b.created_at DESC;
```

Это приём пожеланий по времени, а не календарь свободных слотов.
Разные клиенты могут предложить одно время; доступность проверяет администратор.
Уведомлений, оплаты и внешнего сервера нет.

## Проверка и отладка

```console
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test --verbosity 2
```

Тесты проверяют создание, ошибки данных, ограничения БД, доступ к чужим
заявкам, повторную отмену, HTML-формы, CSRF и экранирование комментариев.
GitHub Actions запускает проверки на SQLite и PostgreSQL.

Для отладки: воспроизведите запрос, прочитайте traceback в терминале,
поставьте `breakpoint()` в нужном месте и повторите запрос с
`python manage.py runserver --noreload`. В pdb: `p request.user`,
`n` (следующая строка), `c` (продолжить). Уберите breakpoint перед коммитом.

Для работы с изменениями: создайте ветку, внесите правку, запустите тесты,
откройте pull request и опишите поведение до и после изменения.

## Размещение

GitHub Pages показывает только статическое описание; Django там не запускается.
Настройки по умолчанию рассчитаны на локальную разработку. Для публикации нужны
WSGI-сервер, PostgreSQL, HTTPS, раздача staticfiles, резервные копии,
мониторинг и ограничение частоты запросов на прокси.
Задайте DJANGO_DEBUG=0, случайный DJANGO_SECRET_KEY и DJANGO_ALLOWED_HOSTS,
затем выполните `python manage.py check --deploy`.
