# Railway Volume Setup

## Зачем нужен volume

Railway Volume нужен, чтобы runtime-state не терялся после redeploy/restart.

В репозитории остаётся canon:

```text
data/canon/
data/rules/
data/characters/
data/scenes/
data/gpt/
data/calendar/
```

В volume хранится живое состояние:

```text
state/
sessions/
logs/
backups/
exports/
tmp/
```

---

## Настройка в Railway

1. Открыть проект Railway.
2. Открыть нужный service.
3. Найти раздел Volumes.
4. Создать новый volume.
5. Указать mount path:

```text
/data
```

6. В Variables добавить:

```text
NOVELLA_RUNTIME_DATA_ROOT=/data
```

Railway также может дать переменную:

```text
RAILWAY_VOLUME_MOUNT_PATH
```

Движок должен использовать её как fallback, если `NOVELLA_RUNTIME_DATA_ROOT` не задан.

---

## Важное ограничение Railway

Volume доступен только во время runtime.

Не использовать volume на этапе build/pre-deploy.

Инициализацию папок и state-файлов делать при запуске приложения.

---

## Что приложение должно сделать при старте

1. Определить runtime root:

```text
NOVELLA_RUNTIME_DATA_ROOT
или RAILWAY_VOLUME_MOUNT_PATH
или ./runtime_data локально
```

2. Создать папки:

```text
/data/state
/data/sessions
/data/logs
/data/backups
/data/exports
/data/tmp
```

3. Если в `/data/state` нет state-файлов, скопировать шаблоны из:

```text
./data/state/
```

4. Если файлы уже есть, не перезаписывать.

---

## State-файлы, которые должны жить в volume

```text
/data/state/current_state.json
/data/state/knowledge_state.json
/data/state/relationships.json
/data/state/inventory_state.json
/data/state/scene_history.json
```

---

## Локально

Для локального запуска без Railway:

```text
NOVELLA_RUNTIME_DATA_ROOT=./runtime_data
```

`runtime_data/` уже добавлен в `.gitignore`.

---

## Проверка после deploy

После деплоя проверить:

- volume mounted at `/data`;
- переменная `NOVELLA_RUNTIME_DATA_ROOT=/data` есть;
- приложение создало `/data/state`;
- state-файлы появились в `/data/state`;
- после restart файлы не исчезли;
- после redeploy файлы не перезаписались шаблонами.

---

## Связанные файлы

```text
data/config/storage_paths.json
data/rules/persistent_storage_rules.md
.env.example
.gitignore
```
