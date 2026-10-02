# REPORT.md — Advanced Git & GitHub (вариант B)

Выполнен **вариант B** (Tasks 1–5 + Final Challenge). Проект: небольшое Python-приложение «Banking Demo» (`src/`, `tests/`, CI в `.github/workflows/test.yml`).

**Важно о доказательствах.** Все команды выполнены по-настоящему в этом репозитории; вместо скриншотов ниже приведён дословный вывод терминала (команды помечены `$`). Remote `origin` на момент сдачи — локальный bare-репозиторий, поэтому Pull Request'ы эмулированы слиянием `--no-ff` с сообщением `Merge pull request #N from ...`, а результаты GitHub Actions будут доступны только после публикации на GitHub. Скриншоты PR, Actions и branch protection нужно добавить после публикации (см. раздел «Что осталось»).

Итоговый граф истории (`git log --graph --all`) и список веток/тегов — в конце отчёта.

---

## Task 1 — Emergency Authentication Hotfix

**Ситуация.** В v2.1.0 валидные пользователи не могли войти: логин в базе хранится в нижнем регистре, а пользователь вводит `Alice@Bank.example ` (регистр/пробел), и сравнение не совпадает. Параллельно в `develop` идёт разработка новой аутентификации (`feature/new-auth`), которая не готова к production.

**Решение.** `hotfix/login-error` создана от `main` (production-код), исправление — нормализация `username.strip().lower()`; добавлены тесты. Ветка запушена, «PR» смержен в `main`, поставлен тег `v2.1.1`, затем `main` влит в `develop`, чтобы исправление не потерялось (после слияния в `develop` есть и hotfix, и незавершённый токен-код, тесты зелёные).

```
$ git checkout -b hotfix/login-error main
Switched to a new branch 'hotfix/login-error'
--- тесты на hotfix-ветке
$ python -m unittest discover -s tests -t .
.....
----------------------------------------------------------------------
Ran 5 tests in 0.001s

OK
$ git diff main --stat
 src/auth.py        | 1 +
 tests/test_auth.py | 6 ++++++
 2 files changed, 7 insertions(+)
$ git commit -q -m Fix login: normalize username (trim + lowercase) before lookup
$ git push -u origin hotfix/login-error
branch 'hotfix/login-error' set up to track 'origin/hotfix/login-error'.
To C:/Users/ars/AppData/Local/Temp/claude/c--Users-ars-Desktop--------0210/41aef990-0e9b-47b6-bbfb-03308945f5b2/scratchpad/origin.git
 * [new branch]      hotfix/login-error -> hotfix/login-error
--- Pull Request #1 hotfix/login-error -> main (локально эмулирован --no-ff merge)
$ git checkout main
Switched to branch 'main'
$ git merge --no-ff hotfix/login-error -m Merge pull request #1 from hotfix/login-error
Merge made by the 'ort' strategy.
 src/auth.py        | 1 +
 tests/test_auth.py | 6 ++++++
 2 files changed, 7 insertions(+)
$ git tag -a v2.1.1 -m Hotfix 2.1.1: login normalization
$ git push origin main v2.1.1
To C:/Users/ars/AppData/Local/Temp/claude/c--Users-ars-Desktop--------0210/41aef990-0e9b-47b6-bbfb-03308945f5b2/scratchpad/origin.git
   330a346..ba113bf  main -> main
 * [new tag]         v2.1.1 -> v2.1.1
--- синхронизация исправления с develop
$ git checkout develop
Switched to branch 'develop'
$ git merge main -m Merge main (hotfix v2.1.1) into develop
Auto-merging src/auth.py
Merge made by the 'ort' strategy.
 src/auth.py        | 1 +
 tests/test_auth.py | 6 ++++++
 2 files changed, 7 insertions(+)
$ git push origin develop
To C:/Users/ars/AppData/Local/Temp/claude/c--Users-ars-Desktop--------0210/41aef990-0e9b-47b6-bbfb-03308945f5b2/scratchpad/origin.git
   974699f..1886250  develop -> develop
--- проверка: в develop есть и hotfix, и незавершённый новый код
$ python -m unittest discover -s tests -t .
......
----------------------------------------------------------------------
Ran 6 tests in 0.006s

OK
$ git log --oneline --graph --decorate --all
*   1886250 (HEAD -> develop, origin/develop) Merge main (hotfix v2.1.1) into develop
|\  
| *   ba113bf (tag: v2.1.1, origin/main, main) Merge pull request #1 from hotfix/login-error
| |\  
| | * 139f89e (origin/hotfix/login-error, hotfix/login-error) Fix login: normalize username (trim + lowercase) before lookup
| |/  
* |   974699f Merge feature/new-auth into develop
|\ \  
| |/  
|/|   
| * 02f8367 (origin/feature/new-auth, feature/new-auth) WIP: tests for token auth
| * 78683f6 WIP: token based authentication
|/  
* 330a346 (tag: v2.1.0) Add pricing module
* 9c331fb Add authentication module
* c109e88 Initial project structure
```

**Вопрос: что может произойти, если создать hotfix от `develop`?**
`develop` содержит незавершённый и непротестированный код (`feature/new-auth`: токены, WIP-коммиты). Если ответвиться от него и слить в `main`, вместе с исправлением в production попадёт вся эта недоработанная функциональность: можно сломать то, что работает, открыть дыру в безопасности банковского приложения или выпустить нестабильный релиз. Тег `v2.1.1` перестал бы означать «v2.1.0 + одно исправление», откат стал бы сложнее, а ревью — шире, чем нужно. Hotfix должен содержать минимальный диф относительно того, что реально работает в production, поэтому ветка делается от `main`.

---

## Task 2 — Merge Conflict: API Configuration

Dev A (`feature/api-performance`): `api_timeout` 30→60 (и `cache_ttl` 300). Dev B (`feature/network-fix`): `api_timeout` 30→90 (и `retries` 3). Первое слияние прошло чисто, второе дало конфликт в `config.json` только по `api_timeout`; неконфликтные изменения (`cache_ttl`, `retries`) Git объединил сам.

```
$ git checkout -b feature/api-performance main
Switched to a new branch 'feature/api-performance'
$ git checkout -b feature/network-fix main
Switched to a new branch 'feature/network-fix'
$ git checkout main
Switched to branch 'main'
$ git merge --no-ff feature/api-performance -m Merge feature/api-performance
Merge made by the 'ort' strategy.
 config.json | 4 ++--
 1 file changed, 2 insertions(+), 2 deletions(-)
$ git merge --no-ff feature/network-fix -m Merge feature/network-fix
Auto-merging config.json
CONFLICT (content): Merge conflict in config.json
Automatic merge failed; fix conflicts and then commit the result.
$ git status --short
UU config.json
$ git diff
diff --cc config.json
index e589019,6da20a5..0000000
--- a/config.json
+++ b/config.json
@@@ -1,6 -1,6 +1,13 @@@
  {
++<<<<<<< HEAD
 +  "api_timeout": 60,
 +  "base_url": "https://api.bank.example",
 +  "retries": 1,
 +  "cache_ttl": 300
++=======
+   "api_timeout": 90,
+   "base_url": "https://api.bank.example",
+   "retries": 3,
+   "cache_ttl": 60
++>>>>>>> feature/network-fix
  }
$ git log --merge --oneline
f086da4 Network fix: timeout 30->90 for slow mobile networks, retries 3
f79fb5b API performance: timeout 30->60, cache_ttl 300
$ git log --merge -p -- config.json
commit f086da4f517ba6cdabac3d2abd864d7f15ed73de
Author: Dev B <b@example.com>
Date:   Fri Oct 2 06:26:14 2026 +0500

    Network fix: timeout 30->90 for slow mobile networks, retries 3

diff --git a/config.json b/config.json
index 0b28a48..6da20a5 100644
--- a/config.json
+++ b/config.json
@@ -1,6 +1,6 @@
 {
-  "api_timeout": 30,
+  "api_timeout": 90,
   "base_url": "https://api.bank.example",
-  "retries": 1,
+  "retries": 3,
   "cache_ttl": 60
 }

commit f79fb5b96f305d03fa631bd94a74e3f09249b036
Author: Dev A <a@example.com>
Date:   Fri Oct 2 06:26:14 2026 +0500

    API performance: timeout 30->60, cache_ttl 300

diff --git a/config.json b/config.json
index 0b28a48..e589019 100644
--- a/config.json
+++ b/config.json
@@ -1,6 +1,6 @@
 {
-  "api_timeout": 30,
+  "api_timeout": 60,
   "base_url": "https://api.bank.example",
   "retries": 1,
-  "cache_ttl": 60
+  "cache_ttl": 300
 }
$ git add config.json
$ git commit -q -m Merge feature/network-fix: keep api_timeout=90 (covers slowest case), keep retries=3 and cache_ttl=300
$ git log --oneline --graph --decorate -6
*   a2b1af7 (HEAD -> main) Merge feature/network-fix: keep api_timeout=90 (covers slowest case), keep retries=3 and cache_ttl=300
|\  
| * f086da4 (feature/network-fix) Network fix: timeout 30->90 for slow mobile networks, retries 3
* |   30c5165 Merge feature/api-performance
|\ \  
| |/  
|/|   
| * f79fb5b (feature/api-performance) API performance: timeout 30->60, cache_ttl 300
|/  
*   ba113bf (tag: v2.1.1, origin/main) Merge pull request #1 from hotfix/login-error
|\  
| * 139f89e (origin/hotfix/login-error, hotfix/login-error) Fix login: normalize username (trim + lowercase) before lookup
|/  
$ cat config.json
{
  "api_timeout": 90,
  "base_url": "https://api.bank.example",
  "retries": 3,
  "cache_ttl": 300
}
```

**Какое значение оставлено и почему: `api_timeout = 90`.**
- Ветка B называется `network-fix` и исправляет сбои на медленных (мобильных) сетях: 60 секунд как раз недостаточно для самых медленных запросов, из-за чего баг и был. Значение 90 покрывает оба сценария (A работает и с 90, просто ждёт максимум дольше).
- Значение 60 из A — оптимизация «чтобы не ждать долго»; она не должна ломать корректность запросов. Если нужна быстрая реакция, её нужно получать через `retries`/кэш (они сохранены: `retries=3`, `cache_ttl=300`), а не урезанием таймаута.
- Итоговый файл проверен как валидный JSON; метки конфликта не просто удалены, а значение выбрано осознанно. Риск выбора 90: при зависшем сервере пользователь ждёт дольше (до 90 с × retries) — этот компромисс нужно согласовать с авторами A и B.

---

## Task 3 — Accidentally Deleted Code

Из `src/utils.py` пропала функция `mask_account` (и её тест). Расследование:

```
--- Что сейчас: функции нет
$ grep -n mask_account -r src tests
--- Поиск коммитов, меняющих число вхождений строки 'def mask_account' (pickaxe)
$ git log -Sdef mask_account --format=%h %an %ad %s --date=iso -- src/utils.py
917409a Petr Ivanov 2026-10-02 06:26:16 +0500 Cleanup: remove unused helpers, tune logging level
d6c0921 Anna Smirnova 2026-10-02 06:26:16 +0500 Add utils helpers (mask_account, normalize_phone, format_money)
--- коммит, удаливший функцию: 917409a
$ git show --stat --format=commit %h%nAuthor: %an <%ae>%nDate:   %ad%nSubject: %s --date=iso 917409a
commit 917409a
Author: Petr Ivanov <petr@example.com>
Date:   2026-10-02 06:26:16 +0500
Subject: Cleanup: remove unused helpers, tune logging level

 CHANGELOG.md        | 3 +++
 src/log.py          | 2 +-
 src/utils.py        | 6 ------
 tests/test_utils.py | 3 ---
 4 files changed, 4 insertions(+), 10 deletions(-)
--- git blame на родителе (кто написал функцию)
$ git blame -L 1,9 917409a^ -- src/utils.py
d6c09216 (Anna Smirnova 2026-10-02 06:26:16 +0500 1) """Helper functions."""
d6c09216 (Anna Smirnova 2026-10-02 06:26:16 +0500 2) 
d6c09216 (Anna Smirnova 2026-10-02 06:26:16 +0500 3) 
d6c09216 (Anna Smirnova 2026-10-02 06:26:16 +0500 4) def mask_account(number):
d6c09216 (Anna Smirnova 2026-10-02 06:26:16 +0500 5)     """Hide all but the last 4 digits of an account number."""
d6c09216 (Anna Smirnova 2026-10-02 06:26:16 +0500 6)     digits = str(number)
d6c09216 (Anna Smirnova 2026-10-02 06:26:16 +0500 7)     return "*" * (len(digits) - 4) + digits[-4:]
d6c09216 (Anna Smirnova 2026-10-02 06:26:16 +0500 8) 
d6c09216 (Anna Smirnova 2026-10-02 06:26:16 +0500 9) 
--- полный diff удаляющего коммита (видно, что ещё изменилось)
$ git show 917409a --format=%h
917409a

diff --git a/CHANGELOG.md b/CHANGELOG.md
new file mode 100644
index 0000000..bd7be30
--- /dev/null
+++ b/CHANGELOG.md
@@ -0,0 +1,3 @@
+# Changelog
+
+- Cleanup of unused helpers, logging level INFO
diff --git a/src/log.py b/src/log.py
index 595b2f9..39a0965 100644
--- a/src/log.py
+++ b/src/log.py
@@ -1,7 +1,7 @@
 """Logging helper."""
 import logging
 
-LEVEL = logging.DEBUG
+LEVEL = logging.INFO
 
 
 def get_logger(name):
diff --git a/src/utils.py b/src/utils.py
index 2e6a3e0..756bae3 100644
--- a/src/utils.py
+++ b/src/utils.py
@@ -1,12 +1,6 @@
 """Helper functions."""
 
 
-def mask_account(number):
-    """Hide all but the last 4 digits of an account number."""
-    digits = str(number)
-    return "*" * (len(digits) - 4) + digits[-4:]
-
-
 def normalize_phone(phone):
     """Keep only digits of a phone number."""
     return "".join(ch for ch in phone if ch.isdigit())
diff --git a/tests/test_utils.py b/tests/test_utils.py
index fa46731..12a2866 100644
--- a/tests/test_utils.py
+++ b/tests/test_utils.py
@@ -4,9 +4,6 @@ from src import utils
 
 
 class UtilsTest(unittest.TestCase):
-    def test_mask_account(self):
-        self.assertEqual(utils.mask_account("1234567890"), "******7890")
-
     def test_normalize_phone(self):
         self.assertEqual(utils.normalize_phone("+7 (777) 123-45-67"), "77771234567")
 
--- Восстановление: обратный патч ТОЛЬКО для utils.py и tests/test_utils.py
$ git checkout -b fix/restore-mask-account
Switched to a new branch 'fix/restore-mask-account'
$ git apply --index /c/Users/ars/AppData/Local/Temp/claude/c--Users-ars-Desktop--------0210/41aef990-0e9b-47b6-bbfb-03308945f5b2/scratchpad/restore.patch
$ python -m unittest discover -s tests -t .
.........
----------------------------------------------------------------------
Ran 9 tests in 0.001s

OK
$ git diff main --stat
 src/utils.py        | 6 ++++++
 tests/test_utils.py | 3 +++
 2 files changed, 9 insertions(+)
$ git checkout main
Switched to branch 'main'
$ git merge --no-ff fix/restore-mask-account -m Merge fix/restore-mask-account
Merge made by the 'ort' strategy.
 src/utils.py        | 6 ++++++
 tests/test_utils.py | 3 +++
 2 files changed, 9 insertions(+)
$ grep -n def  src/utils.py
4:def mask_account(number):
10:def normalize_phone(phone):
15:def format_money(amount):
$ git push origin main fix/restore-mask-account
To C:/Users/ars/AppData/Local/Temp/claude/c--Users-ars-Desktop--------0210/41aef990-0e9b-47b6-bbfb-03308945f5b2/scratchpad/origin.git
   a2b1af7..eca725f  main -> main
 * [new branch]      fix/restore-mask-account -> fix/restore-mask-account
```

**Ответы.**
- *Кто удалил / в каком коммите / когда:* см. вывод `git log -S"def mask_account"` и `git show --stat` выше — удалил Petr Ivanov в коммите «Cleanup: remove unused helpers, tune logging level» (хэш в логе); функцию написала Anna Smirnova (`git blame` на родителе).
- *Что ещё изменилось в этом коммите:* поменялся уровень логирования в `src/log.py` (DEBUG→INFO), создан `CHANGELOG.md`, удалён тест `test_mask_account` — это легитимные изменения.

**Выбранный метод и обоснование.** Применён обратный патч только для двух файлов: `git diff <bad> <bad>^ -- src/utils.py tests/test_utils.py | git apply --index`. Почему не другие варианты:
- `git revert <bad>` откатил бы и полезные изменения из этого коммита (логирование, CHANGELOG);
- `git restore --source=<bad>^ src/utils.py` заменил бы файл целиком и **стёр бы более новое изменение** `format_money` (разделитель тысяч);
- `git cherry-pick` здесь не подходит: нужно вернуть удалённое, а не повторить чужой коммит.
Обратный патч затрагивает только удалённые строки, поэтому новые изменения остаются (тесты после восстановления: `OK`, функция и её тест вернулись, `format_money` сохранил разделитель). Исправление оформлено веткой `fix/restore-mask-account` и слито в `main`.

---

## Task 4 — Recover from a Git Mistake

Три локальных коммита в `local-work`, затем `git reset --hard HEAD~3`, затем восстановление:

```
$ git checkout -b local-work main
Switched to a new branch 'local-work'
--- история до ошибки
$ git log --oneline -5
9c569b6 Local work 3: add note 3
2c489a1 Local work 2: add note 2
d833280 Local work 1: add note 1
eca725f Merge fix/restore-mask-account
fc2afbf Restore mask_account removed by 917409a (keep later format_money change)
--- ОШИБКА
$ git reset --hard HEAD~3
HEAD is now at eca725f Merge fix/restore-mask-account
$ git log --oneline -3
eca725f Merge fix/restore-mask-account
fc2afbf Restore mask_account removed by 917409a (keep later format_money change)
2b8120b README: clarify usage
$ ls
CHANGELOG.md
README.md
config.json
src
tests
--- reflog хранит прежние позиции HEAD
$ git reflog -8
eca725f HEAD@{0}: reset: moving to HEAD~3
9c569b6 HEAD@{1}: commit: Local work 3: add note 3
2c489a1 HEAD@{2}: commit: Local work 2: add note 2
d833280 HEAD@{3}: commit: Local work 1: add note 1
eca725f HEAD@{4}: checkout: moving from main to local-work
eca725f HEAD@{5}: merge fix/restore-mask-account: Merge made by the 'ort' strategy.
2b8120b HEAD@{6}: checkout: moving from fix/restore-mask-account to main
fc2afbf HEAD@{7}: commit: Restore mask_account removed by 917409a (keep later format_money change)
--- восстановление: HEAD@{1} - состояние до reset
$ git reset --hard HEAD@{1}
HEAD is now at 9c569b6 Local work 3: add note 3
$ git log --oneline -5
9c569b6 Local work 3: add note 3
2c489a1 Local work 2: add note 2
d833280 Local work 1: add note 1
eca725f Merge fix/restore-mask-account
fc2afbf Restore mask_account removed by 917409a (keep later format_money change)
$ ls
CHANGELOG.md
README.md
config.json
docs_note1.md
docs_note2.md
docs_note3.md
src
tests
$ git merge --no-ff local-work -m Merge local-work (recovered commits)
Merge made by the 'ort' strategy.
 docs_note1.md | 1 +
 docs_note2.md | 1 +
 docs_note3.md | 1 +
 3 files changed, 3 insertions(+)
 create mode 100644 docs_note1.md
 create mode 100644 docs_note2.md
 create mode 100644 docs_note3.md
```

**Что хранит `git reflog`?** Локальный журнал перемещений `HEAD` и ссылок веток: каждый коммит, checkout, reset, merge, rebase, amend записывается с предыдущим и новым хэшем (`HEAD@{n}`). Он хранится только локально и не пушится.

**Почему помогает восстановить «удалённые» коммиты?** `reset --hard` лишь переставляет указатель ветки; сами объекты коммитов остаются в `.git/objects`, пока их не удалит сборщик мусора. Reflog хранит хэш состояния до reset (`HEAD@{1}`), поэтому `git reset --hard HEAD@{1}` (или `git branch rescue <hash>`) возвращает коммиты.

**Когда восстановление невозможно?**
- запись в reflog истекла (по умолчанию ~90 дней для достижимых, 30 дней для недостижимых записей) и выполнен `git gc`/`git prune`;
- репозиторий склонирован заново или `.git` удалён — reflog локален;
- сделан `git reflog expire --expire=now --all` + `git gc --prune=now`;
- коммиты никогда не были закоммичены (незакоммиченные изменения `reset --hard` стирает безвозвратно, их нет в reflog).

---

## Task 5 — Secure GitHub Repository

Полный отчёт: [SECURITY_REPORT.md](SECURITY_REPORT.md). Реализовано в ветке `security/hardening` (слита в `main`): workflow CI (Build/Test/Lint/Security), `dependabot.yml`, `CODEOWNERS`, обновлённый `.gitignore`, `.env.example`, скрипт `scripts/apply_branch_protection.sh` (branch protection, ревью PR, secret scanning, push protection, Dependabot alerts). Доказательство проблемы с ключом (ключ фейковый) и локальный прогон проверок CI:

```
$ git checkout -b security/hardening main
Switched to a new branch 'security/hardening'
--- имитация проблемы: секрет в истории (ключ ФЕЙКОВЫЙ)
--- поиск секрета в истории
$ git log -SFAKE_sk_live --oneline --all
3b833c0 Remove .env (key stays in history!)
f1819ba Add env file with API key
$ git grep -n FAKE_sk_live f1819ba0147eded037a42ba943dc32ef3461db76
f1819ba0147eded037a42ba943dc32ef3461db76:.env:1:API_KEY=FAKE_sk_live_0123456789abcdef
--- локальная проверка того, что будет делать CI
$ python -m unittest discover -s tests -t .
.........
----------------------------------------------------------------------
Ran 9 tests in 0.001s

OK
$ python -m flake8 src tests
C:\Users\ars\AppData\Local\Programs\Python\Python37\python.exe: No module named flake8
$ python -m bandit -r src
C:\Users\ars\AppData\Local\Programs\Python\Python37\python.exe: No module named bandit
$ git push -u origin security/hardening
branch 'security/hardening' set up to track 'origin/security/hardening'.
To C:/Users/ars/AppData/Local/Temp/claude/c--Users-ars-Desktop--------0210/41aef990-0e9b-47b6-bbfb-03308945f5b2/scratchpad/origin.git
 * [new branch]      security/hardening -> security/hardening
$ git checkout main
Switched to branch 'main'
$ git merge --no-ff security/hardening -m Merge pull request #5 from security/hardening
Merge made by the 'ort' strategy.
 .env.example                       |  1 +
 .github/CODEOWNERS                 |  4 +++
 .github/dependabot.yml             | 10 ++++++
 .github/workflows/test.yml         | 58 +++++++++++++++++++++++++++++++++++
 .gitignore                         |  7 +++++
 SECURITY_REPORT.md                 | 62 ++++++++++++++++++++++++++++++++++++++
 requirements.txt                   |  3 ++
 scripts/apply_branch_protection.sh | 35 +++++++++++++++++++++
 setup.cfg                          |  3 ++
 9 files changed, 183 insertions(+)
 create mode 100644 .env.example
 create mode 100644 .github/CODEOWNERS
 create mode 100644 .github/dependabot.yml
 create mode 100644 .github/workflows/test.yml
 create mode 100644 SECURITY_REPORT.md
 create mode 100644 requirements.txt
 create mode 100644 scripts/apply_branch_protection.sh
 create mode 100644 setup.cfg
$ git push origin main
To C:/Users/ars/AppData/Local/Temp/claude/c--Users-ars-Desktop--------0210/41aef990-0e9b-47b6-bbfb-03308945f5b2/scratchpad/origin.git
   eca725f..e37aabb  main -> main
```

Branch protection и secret scanning настраиваются на стороне GitHub (скрипт готов, но к репозиторию на GitHub ещё не применён).

---

## Final Challenge

Постановка: `feature-A` и `feature-B` разрабатываются параллельно, `main` меняется, плохой коммит, конфликт, лишний коммит не в той ветке, откат, CI перед слиянием. Выбор команд:

| Ситуация | Команда | Почему |
|---|---|---|
| Коммит «shipping» сделан в `feature-B`, а относится к `feature-A` | `git cherry-pick` + `git reset --hard HEAD~1` | Нужно перенести один коммит; ветка не опубликована, поэтому reset безопасен |
| `main` ушёл вперёд | `git rebase main` для `feature-B` | Линейная история, ветка локальная и не опубликована; для общих веток rebase не используем |
| Плохой коммит (обрезаются копейки) | `git bisect run` → `git revert` | bisect находит первый плохой коммит автоматически по тестам; revert не переписывает историю |
| Конфликт `Features:` в README | `git merge` + ручное объединение | Нужны обе правки; метки конфликта не просто удалены |
| Релиз | `git tag -a v2.2.0` | Фиксирует выпуск |
| CI | `.github/workflows/test.yml` + branch protection | Слияние только после зелёных проверок |

```
$ git checkout -b feature-A main
Switched to a new branch 'feature-A'
$ git checkout -b feature-B main
Switched to a new branch 'feature-B'
--- Проблема 1: коммит B3 сделан не в той ветке -> cherry-pick в feature-A, из feature-B убрать
$ git checkout feature-A
Switched to branch 'feature-A'
$ git cherry-pick 0780e81
[feature-A 7da06ea] B3: shipping module (MISTAKE: belongs to feature-A)
 Date: Fri Oct 2 06:26:25 2026 +0500
 1 file changed, 5 insertions(+)
 create mode 100644 src/shipping.py
$ git checkout feature-B
Switched to branch 'feature-B'
(B3 ещё не опубликован, поэтому reset безопасен)
$ git reset --hard HEAD~1
HEAD is now at 6e10d7b B2: add report module
$ git log --oneline -4 feature-A
7da06ea B3: shipping module (MISTAKE: belongs to feature-A)
2f119e3 A3: shipping docs
e921c2e A2: optimize price calculation (BAD COMMIT: truncates cents)
86826d3 A1: README - announce pricing and shipping
$ git log --oneline -3 feature-B
6e10d7b B2: add report module
5428f17 B1: README - announce reports
e37aabb Merge pull request #5 from security/hardening
--- Проблема 2: main ушёл вперёд, пока шла разработка
$ git log --oneline --graph --all -12
* 7da06ea B3: shipping module (MISTAKE: belongs to feature-A)
* 2f119e3 A3: shipping docs
* e921c2e A2: optimize price calculation (BAD COMMIT: truncates cents)
* 86826d3 A1: README - announce pricing and shipping
| * 97426af main: update CHANGELOG
|/  
| * 6e10d7b B2: add report module
| * 5428f17 B1: README - announce reports
|/  
*   e37aabb Merge pull request #5 from security/hardening
|\  
| * 70eac2b Security hardening: CI, Dependabot, CODEOWNERS, gitignore, branch protection script, report
| * 3b833c0 Remove .env (key stays in history!)
| * f1819ba Add env file with API key
|/  
* 1137541 Move recovered notes to docs/
--- rebase feature-B на актуальный main (история ещё не опубликована)
$ git checkout feature-B
Switched to branch 'feature-B'
$ git rebase main
Rebasing (1/2)
Rebasing (2/2)
Successfully rebased and updated refs/heads/feature-B.
$ git log --oneline --graph -6
* 28d2b55 B2: add report module
* c94a00b B1: README - announce reports
* 97426af main: update CHANGELOG
*   e37aabb Merge pull request #5 from security/hardening
|\  
| * 70eac2b Security hardening: CI, Dependabot, CODEOWNERS, gitignore, branch protection script, report
| * 3b833c0 Remove .env (key stays in history!)
--- Проблема 3: плохой коммит в feature-A -> git bisect
$ git checkout feature-A
Switched to branch 'feature-A'
$ git bisect start
status: waiting for both good and bad commits
$ git bisect bad HEAD
status: waiting for good commit(s), bad commit known
$ git bisect good 86826d3
Bisecting: 0 revisions left to test after this (roughly 1 step)
[2f119e3ff74c529bea8b85599298206e5685a10d] A3: shipping docs
$ git bisect run python -m unittest discover -s tests -t .
running 'python' '-m' 'unittest' 'discover' '-s' 'tests' '-t' '.'
...FF....
======================================================================
FAIL: test_discount (tests.test_pricing.PricingTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "<path>\������ 0210\tests\test_pricing.py", line 11, in test_discount
    self.assertEqual(pricing.calc_total([19.99, 10.00], 10), 26.99)
AssertionError: 26 != 26.99

======================================================================
FAIL: test_total (tests.test_pricing.PricingTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "<path>\������ 0210\tests\test_pricing.py", line 8, in test_total
    self.assertEqual(pricing.calc_total([19.99, 10.00]), 29.99)
AssertionError: 29 != 29.99

----------------------------------------------------------------------
Ran 9 tests in 0.005s

FAILED (failures=2)
Bisecting: 0 revisions left to test after this (roughly 0 steps)
[e921c2ea9301281167fb0274961956b179c0e5ba] A2: optimize price calculation (BAD COMMIT: truncates cents)
running 'python' '-m' 'unittest' 'discover' '-s' 'tests' '-t' '.'
...FF....
======================================================================
FAIL: test_discount (tests.test_pricing.PricingTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "<path>\������ 0210\tests\test_pricing.py", line 11, in test_discount
    self.assertEqual(pricing.calc_total([19.99, 10.00], 10), 26.99)
AssertionError: 26 != 26.99

======================================================================
FAIL: test_total (tests.test_pricing.PricingTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "<path>\������ 0210\tests\test_pricing.py", line 8, in test_total
    self.assertEqual(pricing.calc_total([19.99, 10.00]), 29.99)
AssertionError: 29 != 29.99

----------------------------------------------------------------------
Ran 9 tests in 0.001s

FAILED (failures=2)
e921c2ea9301281167fb0274961956b179c0e5ba is the first bad commit
commit e921c2ea9301281167fb0274961956b179c0e5ba
Author: ars <arseniy.sapranidi@narxoz.kz>
Date:   Fri Oct 2 06:26:24 2026 +0500

    A2: optimize price calculation (BAD COMMIT: truncates cents)

 src/pricing.py | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
bisect found first bad commit
$ git bisect reset
Previous HEAD position was e921c2e A2: optimize price calculation (BAD COMMIT: truncates cents)
Switched to branch 'feature-A'
$ git show --stat --format=Bad commit: %h%nAuthor: %an%nDate: %ad%nSubject: %s --date=iso e921c2e
Bad commit: e921c2e
Author: ars
Date: 2026-10-02 06:26:24 +0500
Subject: A2: optimize price calculation (BAD COMMIT: truncates cents)

 src/pricing.py | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
--- исправление: revert (история не переписывается, ветка уже могла быть опубликована)
$ git revert --no-edit e921c2e
[feature-A c24d717] Revert "A2: optimize price calculation (BAD COMMIT: truncates cents)"
 Date: Fri Oct 2 06:26:28 2026 +0500
 1 file changed, 1 insertion(+), 1 deletion(-)
$ python -m unittest discover -s tests -t .
.........
----------------------------------------------------------------------
Ran 9 tests in 0.001s

OK
$ git log --oneline -6
c24d717 Revert "A2: optimize price calculation (BAD COMMIT: truncates cents)"
7da06ea B3: shipping module (MISTAKE: belongs to feature-A)
2f119e3 A3: shipping docs
e921c2e A2: optimize price calculation (BAD COMMIT: truncates cents)
86826d3 A1: README - announce pricing and shipping
e37aabb Merge pull request #5 from security/hardening
--- Слияние в main
$ git checkout main
Switched to branch 'main'
$ git merge --no-ff feature-A -m Merge feature-A
Merge made by the 'ort' strategy.
 README.md        | 2 +-
 docs/shipping.md | 1 +
 src/shipping.py  | 5 +++++
 3 files changed, 7 insertions(+), 1 deletion(-)
 create mode 100644 docs/shipping.md
 create mode 100644 src/shipping.py
$ git merge --no-ff feature-B -m Merge feature-B
Auto-merging README.md
CONFLICT (content): Merge conflict in README.md
Automatic merge failed; fix conflicts and then commit the result.
$ git status --short
UU README.md
A  src/report.py
$ git diff
diff --cc README.md
index 566677b,920afe4..0000000
--- a/README.md
+++ b/README.md
@@@ -1,6 -1,6 +1,10 @@@
  # Banking Demo
  
++<<<<<<< HEAD
 +Features: pricing, shipping
++=======
+ Features: basic login, reports
++>>>>>>> feature-B
  
  ## Usage (run tests)
  
$ cat README.md
# Banking Demo

Features: basic login, pricing, shipping, reports


## Usage (run tests)

    python -m unittest discover -s tests -t .
$ git add README.md
$ git commit -q -m Merge feature-B: combine Features line from both branches
$ python -m unittest discover -s tests -t .
.........
----------------------------------------------------------------------
Ran 9 tests in 0.001s

OK
$ git tag -a v2.2.0 -m Release 2.2.0
$ git push origin main feature-A feature-B v2.2.0
To C:/Users/ars/AppData/Local/Temp/claude/c--Users-ars-Desktop--------0210/41aef990-0e9b-47b6-bbfb-03308945f5b2/scratchpad/origin.git
   e37aabb..b787c84  main -> main
 * [new branch]      feature-A -> feature-A
 * [new branch]      feature-B -> feature-B
 * [new tag]         v2.2.0 -> v2.2.0
$ git log --oneline --graph --decorate -20
*   b787c84 (HEAD -> main, tag: v2.2.0, origin/main) Merge feature-B: combine Features line from both branches
|\  
| * 28d2b55 (origin/feature-B, feature-B) B2: add report module
| * c94a00b B1: README - announce reports
* |   96440c1 Merge feature-A
|\ \  
| |/  
|/|   
| * c24d717 (origin/feature-A, feature-A) Revert "A2: optimize price calculation (BAD COMMIT: truncates cents)"
| * 7da06ea B3: shipping module (MISTAKE: belongs to feature-A)
| * 2f119e3 A3: shipping docs
| * e921c2e A2: optimize price calculation (BAD COMMIT: truncates cents)
| * 86826d3 A1: README - announce pricing and shipping
* | 97426af main: update CHANGELOG
|/  
*   e37aabb Merge pull request #5 from security/hardening
|\  
| * 70eac2b (origin/security/hardening, security/hardening) Security hardening: CI, Dependabot, CODEOWNERS, gitignore, branch protection script, report
| * 3b833c0 Remove .env (key stays in history!)
| * f1819ba Add env file with API key
|/  
* 1137541 Move recovered notes to docs/
*   75250ee Merge local-work (recovered commits)
|\  
| * 9c569b6 (local-work) Local work 3: add note 3
| * 2c489a1 Local work 2: add note 2
| * d833280 Local work 1: add note 1
|/  
*   eca725f Merge fix/restore-mask-account
|\
```

---

## Итоговые ветки, теги и история

```
$ git branch -a -vv
  develop                                 1886250 Merge main (hotfix v2.1.1) into develop
  feature-A                               c24d717 Revert "A2: optimize price calculation (BAD COMMIT: truncates cents)"
  feature-B                               28d2b55 B2: add report module
  feature/api-performance                 f79fb5b API performance: timeout 30->60, cache_ttl 300
  feature/network-fix                     f086da4 Network fix: timeout 30->90 for slow mobile networks, retries 3
  feature/new-auth                        02f8367 WIP: tests for token auth
  fix/restore-mask-account                fc2afbf Restore mask_account removed by 917409a (keep later format_money change)
  hotfix/login-error                      139f89e [origin/hotfix/login-error] Fix login: normalize username (trim + lowercase) before lookup
  local-work                              9c569b6 Local work 3: add note 3
* main                                    b787c84 Merge feature-B: combine Features line from both branches
  security/hardening                      70eac2b [origin/security/hardening] Security hardening: CI, Dependabot, CODEOWNERS, gitignore, branch protection script, report
  remotes/origin/develop                  1886250 Merge main (hotfix v2.1.1) into develop
  remotes/origin/feature-A                c24d717 Revert "A2: optimize price calculation (BAD COMMIT: truncates cents)"
  remotes/origin/feature-B                28d2b55 B2: add report module
  remotes/origin/feature/api-performance  f79fb5b API performance: timeout 30->60, cache_ttl 300
  remotes/origin/feature/network-fix      f086da4 Network fix: timeout 30->90 for slow mobile networks, retries 3
  remotes/origin/feature/new-auth         02f8367 WIP: tests for token auth
  remotes/origin/fix/restore-mask-account fc2afbf Restore mask_account removed by 917409a (keep later format_money change)
  remotes/origin/hotfix/login-error       139f89e Fix login: normalize username (trim + lowercase) before lookup
  remotes/origin/main                     b787c84 Merge feature-B: combine Features line from both branches
  remotes/origin/security/hardening       70eac2b Security hardening: CI, Dependabot, CODEOWNERS, gitignore, branch protection script, report
$ git log --oneline --graph --decorate --all
*   b787c84 (HEAD -> main, tag: v2.2.0, origin/main) Merge feature-B: combine Features line from both branches
|\  
| * 28d2b55 (origin/feature-B, feature-B) B2: add report module
| * c94a00b B1: README - announce reports
* |   96440c1 Merge feature-A
|\ \  
| |/  
|/|   
| * c24d717 (origin/feature-A, feature-A) Revert "A2: optimize price calculation (BAD COMMIT: truncates cents)"
| * 7da06ea B3: shipping module (MISTAKE: belongs to feature-A)
| * 2f119e3 A3: shipping docs
| * e921c2e A2: optimize price calculation (BAD COMMIT: truncates cents)
| * 86826d3 A1: README - announce pricing and shipping
* | 97426af main: update CHANGELOG
|/  
*   e37aabb Merge pull request #5 from security/hardening
|\  
| * 70eac2b (origin/security/hardening, security/hardening) Security hardening: CI, Dependabot, CODEOWNERS, gitignore, branch protection script, report
| * 3b833c0 Remove .env (key stays in history!)
| * f1819ba Add env file with API key
|/  
* 1137541 Move recovered notes to docs/
*   75250ee Merge local-work (recovered commits)
|\  
| * 9c569b6 (local-work) Local work 3: add note 3
| * 2c489a1 Local work 2: add note 2
| * d833280 Local work 1: add note 1
|/  
*   eca725f Merge fix/restore-mask-account
|\  
| * fc2afbf (origin/fix/restore-mask-account, fix/restore-mask-account) Restore mask_account removed by 917409a (keep later format_money change)
|/  
* 2b8120b README: clarify usage
* 6cd08e7 format_money: thousands separator
* 917409a Cleanup: remove unused helpers, tune logging level
* 0c06a19 Add logging helper
* d6c0921 Add utils helpers (mask_account, normalize_phone, format_money)
*   a2b1af7 Merge feature/network-fix: keep api_timeout=90 (covers slowest case), keep retries=3 and cache_ttl=300
|\  
| * f086da4 (origin/feature/network-fix, feature/network-fix) Network fix: timeout 30->90 for slow mobile networks, retries 3
* |   30c5165 Merge feature/api-performance
|\ \  
| |/  
|/|   
| * f79fb5b (origin/feature/api-performance, feature/api-performance) API performance: timeout 30->60, cache_ttl 300
|/  
| *   1886250 (origin/develop, develop) Merge main (hotfix v2.1.1) into develop
| |\  
| |/  
|/|   
* |   ba113bf (tag: v2.1.1) Merge pull request #1 from hotfix/login-error
|\ \  
| * | 139f89e (origin/hotfix/login-error, hotfix/login-error) Fix login: normalize username (trim + lowercase) before lookup
|/ /  
| * 974699f Merge feature/new-auth into develop
|/| 
| * 02f8367 (origin/feature/new-auth, feature/new-auth) WIP: tests for token auth
| * 78683f6 WIP: token based authentication
|/  
* 330a346 (tag: v2.1.0) Add pricing module
* 9c331fb Add authentication module
* c109e88 Initial project structure
$ git tag -n
v2.1.0          Release 2.1.0 (contains login bug)
v2.1.1          Hotfix 2.1.1: login normalization
v2.2.0          Release 2.2.0
```

## Что осталось (требует GitHub)

1. Создать репозиторий на GitHub и запушить ветки/теги (`git remote set-url origin <url>`, `git push --all`, `git push --tags`).
2. Открыть реальные PR, дождаться запусков GitHub Actions и добавить скриншоты (PR, Actions, ветки, конфликт) в этот отчёт.
3. Выполнить `./scripts/apply_branch_protection.sh OWNER/REPO`, чтобы включить обязательные проверки/ревью.
