## Project audit report — 2026-03-10

### Summary

- Добавлен запуск `pytest` в CI и базовый набор smoke/security/permissions тестов (ветка `audit/pr1-ci-tests`).
- Для тестов проекту требуется Postgres (SQLite ломается из-за `CheckConstraint` с `Now()`/`strftime`).
- В проекте есть чувствительная зона: `/qz/sign/` (CSRF-exempt) и использование приватного ключа с диска.
- Репозиторий содержит `private-key.pem` (найдено вне ветки PR1; файл игнорируется `.gitignore`, но наличие в репо — риск).

---

### Findings

| Severity | Area | What | Risk | Fix |
|---|---|---|---|---|
| **blocker** | CI | Workflow делал только `migrate`, тесты не запускались | Регрессии не ловятся автоматически | **PR1**: добавить шаг `pytest -q` |
| **blocker** | Secrets | В репозитории присутствует `private-key.pem` | Компрометация ключа подписи / полный компромисс доверия | Удалить из VCS, перевыпустить ключ, хранить вне репо (secret store), добавить ротацию |
| **high** | Security | `/qz/sign/` помечен `@csrf_exempt` | Возможны CSRF-атаки (если endpoint доступен из браузера/сессии) + злоупотребление подписью | Ограничить доступ (authn/authz), origin checks, rate limit, отдельный service user, аудит логов |
| **high** | Testability / Security | Жёсткий путь к ключу мешал тестам | Тесты падали / стимулирует хранить ключ рядом с кодом | **PR1**: добавить `QZ_PRIVATE_KEY_PATH` в settings и использовать в `qz_sign` |
| **medium** | Testing | SQLite не подходит для тестов из-за `CheckConstraint` на “не прошлую дату” | Локальные тесты могут вводить в заблуждение | Документировать Postgres как обязательный backend для тестов |
| **medium** | Auth | DRF использует `SessionAuthentication` + `BasicAuthentication` | Basic auth может быть нежелателен в prod; риск неправильной экспозиции | Пересмотреть требования; возможно оставить только Session/Token |
| **low** | Logging | Warnings: “Accessing the database during app initialization” | Потенциальные скрытые запросы при импорте | Найти и устранить запросы при import/ready, если подтвердится |
| **low** | Labels/IO | `label_service` читает файлы по имени (images) | Возможны ошибки/попытки path traversal при плохой валидации входа | Убедиться, что `filename` приходит только из allowlist/админки; добавить валидацию |

---

### What PR1 covers

- **CI**: запускает `pytest`.
- **Tests**:
  - `/health/` (минимальный smoke + требование auth).
  - `/post_login_redirect/` (нет open redirect, allowlist origins).
  - `/qz/sign/` (405/400/200 + base64 подпись с временным ключом).
  - `orders` permissions: contractor видит только свои заявки.

---

### PR2 backlog (next)

- **Serializer tests**: `api/v1/orders/serializers.py` (валидация date, items, ошибки для чужих contractor_user).
- **Service tests**: `orders/services/order_excel_service.py` (минимальная генерация файла, ключевые поля/заголовки).
- **Labels tests**: `api/v1/labels/*` (контракты и статусы), и валидация входных параметров для чтения изображений/шаблонов.
- **Security hardening**: обсудить стратегию защиты `qz_sign` (authn/authz, отдельный ключ/сервис, rate limits, audit logs).

