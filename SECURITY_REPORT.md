# SECURITY_REPORT.md

Репозиторий: Banking Demo. Отчёт описывает найденные проблемы, риски, доказательства и исправления.
Ключ в примере — **фейковый** (`FAKE_sk_live_...`), использован только для демонстрации.

## 1. Найденные проблемы

| # | Проблема | Риск | Доказательство | Исправление |
|---|----------|------|----------------|-------------|
| 1 | Любой может сделать push в `main` | Непроверенный или вредоносный код попадает в production | Нет правил защиты ветки | Branch protection (п. 2.1) |
| 2 | Нет ревью Pull Request | Ошибки и уязвимости не замечаются, нет принципа «четырёх глаз» | PR можно смержить без одобрений | Обязательное ревью + CODEOWNERS |
| 3 | Нет автоматических тестов | Сломанный код доходит до `main` (как баг логина в v2.1.0) | В v2.1.0 не было workflow | `.github/workflows/test.yml` как обязательная проверка |
| 4 | API-ключ закоммичен | Компрометация внешнего сервиса, утечка денег и данных | `git log -S"FAKE_sk_live" --oneline --all` находит коммиты `Add env file with API key` и `Remove .env`; ключ читается из старого коммита командой `git show <commit>:.env` | Отозвать и перевыпустить ключ, очистить историю, secret scanning, `.gitignore` |
| 5 | Зависимости устарели | Известные CVE в библиотеках | Нет автоматического контроля версий | Dependabot + `pip-audit` в CI |
| 6 | В `.gitignore` не было `.env`, `*.key`, `*.pem` | Повторный случайный коммит секретов | Исходный `.gitignore` содержал только `__pycache__/` и `*.pyc` | Обновлённый `.gitignore`, шаблон `.env.example` |
| 7 | Права доступа не ограничены | Лишние люди могут менять настройки и секреты | — | Принцип наименьших привилегий (п. 2.6) |

Важно по пункту 4: удаление файла новым коммитом **не убирает** секрет из истории. Ключ нужно считать скомпрометированным, сразу отозвать и выпустить новый.

## 2. Что настроено и как

### 2.1 Branch protection для `main`
Применяется скриптом [scripts/apply_branch_protection.sh](scripts/apply_branch_protection.sh) (`./scripts/apply_branch_protection.sh OWNER/REPO`, нужны права администратора). Параметры:
- прямой push запрещён, изменения только через Pull Request;
- обязательны проверки `Build and Test`, `Lint`, `Security Check`, ветка должна быть актуальной (`strict`);
- 1 одобрение, устаревшие одобрения сбрасываются при новых коммитах;
- обязательное ревью владельцев кода (CODEOWNERS);
- обсуждения должны быть закрыты;
- force-push и удаление `main` запрещены;
- правила действуют и на администраторов (`enforce_admins`).

Того же можно добиться в интерфейсе: Settings → Branches → Add rule → `main`.

### 2.2 Pull Request review
Файл [.github/CODEOWNERS](.github/CODEOWNERS): изменения в `.github/` и `src/auth.py` требуют одобрения владельца.

### 2.3 GitHub Actions
Файл [.github/workflows/test.yml](.github/workflows/test.yml) запускается при создании PR в `main`/`develop`:
- **Build and Test**: checkout, установка зависимостей, компиляция, `unittest`;
- **Lint**: `flake8`;
- **Security Check**: `bandit` (статический анализ), `pip-audit` (уязвимые зависимости), `gitleaks` (поиск секретов в истории).
Права токена ограничены `contents: read`.

### 2.4 Secret scanning
Включается тем же скриптом: `secret_scanning` и `secret_scanning_push_protection` (GitHub блокирует push с известными форматами ключей). В CI дополнительно работает gitleaks.
План по утёкшему ключу: 1) отозвать ключ у провайдера; 2) выпустить новый и положить в GitHub Secrets / менеджер секретов; 3) при необходимости очистить историю (`git filter-repo --path .env --invert-paths`) и сделать force-push, после чего все клонируют репозиторий заново.

### 2.5 Dependabot
Файл [.github/dependabot.yml](.github/dependabot.yml): еженедельные обновления для `pip` и `github-actions`; скрипт также включает Dependabot alerts и security updates.

### 2.6 Права доступа
- роли: Read для наблюдателей, Triage/Write для разработчиков, Admin только 1–2 человека;
- права выдаются командам, а не отдельным людям;
- обязателен 2FA для организации;
- секреты хранятся только в Actions Secrets, не в коде.

### 2.7 `.gitignore`
Добавлены `.env`, `.env.*` (кроме `.env.example`), `*.pem`, `*.key`, `venv/`.

## 3. Итоговый процесс

Developer → Feature Branch → Pull Request → (Code Review + CI Tests + Security Checks) → Protected `main` → Release (тег `vX.Y.Z`).
