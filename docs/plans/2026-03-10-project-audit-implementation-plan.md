## Project Audit — Implementation Plan

> **For Cursor agent:** Execute task-by-task, keep PRs small, validate by running targeted `pytest` locally after each slice.

**Goal:** Добавить проверяемый CI + недостающие тесты для критичных точек, затем провести audit-итерации по приоритетам и оформить отчёт + PR(ы).

**Architecture:** Risk-first. Сначала включаем “quality gate” (pytest в CI) и минимальную тест-инфраструктуру, затем точечно покрываем критичные endpoints/permissions. Дальше — сериализаторы/сервисы. Отдельно фиксируем findings в отчёте.

**Tech Stack:** Django, DRF, pytest/pytest-django, Poetry, GitHub Actions.

---

### Task 1: Make CI actually run tests (PR1)

**Files:**
- Modify: `.github/workflows/ci.yml`

**Step 1: Add pytest step**
- Добавить шаг после `Run migrations`:
  - Run: `pytest -q`

---

### Task 2: Add minimal pytest structure + fixtures (PR1)

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_smoke.py`
- Create: `core/test_settings.py`
- Modify: `pytest.ini`

**Step 1: Make pytest self-contained**
- `pytest` должен стартовать без локального `.env`.

---

### Task 3: Security-critical endpoint tests (PR1)

**Files:**
- Create: `tests/test_post_login_redirect.py`
- Create: `tests/test_qz_sign.py`
- Modify: `core/views.py` / `core/settings.py` (если нужно для тестируемости)

**Step 1: `post_login_redirect`**
- Без `url` → редирект на админку (в текущей конфигурации это `/`).
- `url` с origin НЕ из allowlist → редирект в админку.
- `url` с origin из allowlist → редирект на целевой URL.

**Step 2: `qz_sign`**
- Пустое тело → 400.
- POST с телом → 200 и base64-строка подписи.
- Путь к приватному ключу должен быть конфигурируемым для тестов (например, `QZ_PRIVATE_KEY_PATH`).

---

### Task 4: Permissions/data isolation tests for orders (PR1)

**Files:**
- Create: `tests/api/v1/orders/test_contractor_orders_permissions.py`

**Tests:**
- Contractor видит только свои заявки в `list`.
- Contractor не может `retrieve` чужого contractor_user (403/404).

---

### Task 5: Audit report + prioritize PR2 work

**Files:**
- Create: `docs/audit/2026-03-10-project-audit.md`

**Include:**
- Отсутствие тестов и отсутствующий `pytest` шаг в CI (blocker/high).
- `private-key.pem` в репозитории (blocker).
- `qz_sign` CSRF-exempt + file-based key path (high).

