# Persistent Storage Rules

## Назначение файла

Этот файл фиксирует, как движок должен работать с постоянным хранилищем на Railway.

Цель: после redeploy / restart / rebuild не терять:

- текущую сцену;
- state;
- отношения;
- знания;
- инвентарь;
- историю сцен;
- runtime-сессии;
- логи и бэкапы.

---

## Главное правило

Репозиторий хранит canon.

Railway Volume хранит runtime-state.

Нельзя хранить активное состояние игры только внутри репозитория или ephemeral-диска контейнера.

---

## Что остаётся в репозитории

В репозитории остаются стабильные файлы:

```text
data/canon/
data/rules/
data/characters/
data/scenes/
data/gpt/
data/calendar/
data/state/  # только шаблоны / стартовые state-файлы
```

Эти файлы считаются source-of-truth для канона и структуры.

Они не должны перезаписываться runtime-логикой.

---

## Что должно жить в volume

На Railway Volume должны жить runtime-файлы:

```text
{RUNTIME_DATA_ROOT}/state/current_state.json
{RUNTIME_DATA_ROOT}/state/knowledge_state.json
{RUNTIME_DATA_ROOT}/state/relationships.json
{RUNTIME_DATA_ROOT}/state/inventory_state.json
{RUNTIME_DATA_ROOT}/state/scene_history.json
{RUNTIME_DATA_ROOT}/sessions/
{RUNTIME_DATA_ROOT}/logs/
{RUNTIME_DATA_ROOT}/backups/
{RUNTIME_DATA_ROOT}/exports/
{RUNTIME_DATA_ROOT}/tmp/
```

---

## Runtime data root

Путь к runtime-хранилищу определяется так:

1. `NOVELLA_RUNTIME_DATA_ROOT`, если задан;
2. `RAILWAY_VOLUME_MOUNT_PATH`, если задан Railway;
3. `./runtime_data` для локального запуска.

Рекомендуемый Railway mount path:

```text
/data
```

Рекомендуемая переменная:

```text
NOVELLA_RUNTIME_DATA_ROOT=/data
```

---

## Инициализация при старте

При старте приложения:

1. Определить `RUNTIME_DATA_ROOT`.
2. Создать папки:

```text
state/
sessions/
logs/
backups/
exports/
tmp/
```

3. Проверить runtime state files.
4. Если какого-то runtime-state файла нет, скопировать шаблон из:

```text
./data/state/
```

5. Если runtime-state файл уже есть — не перезаписывать его.

---

## Важное правило Railway

Railway Volume доступен только во время runtime.

Не рассчитывать на volume во время build/pre-deploy.

Инициализацию папок и state-файлов делать при старте приложения, а не на этапе сборки.

---

## Запрещено

Запрещено:

- писать текущий runtime state обратно в `./data/state` в production;
- перезаписывать runtime state шаблонами после redeploy;
- хранить активные сессии только в памяти процесса;
- хранить единственную копию прогресса в `/tmp`;
- делать миграцию state без backup;
- чистить volume при restart;
- считать, что redeploy сохранит файлы вне volume.

---

## Бэкапы

Перед рискованными изменениями state делать backup:

```text
{RUNTIME_DATA_ROOT}/backups/YYYY-MM-DD_HH-mm-ss/
```

Минимум бэкапить:

```text
current_state.json
knowledge_state.json
relationships.json
inventory_state.json
scene_history.json
```

---

## Локальная разработка

Если volume-переменные не заданы, использовать:

```text
./runtime_data
```

`runtime_data/` не должен коммититься в репозиторий.

Добавить в `.gitignore`:

```text
runtime_data/
```

---

## Короткое правило для ИИ / движка

Canon читается из репозитория.

Живое состояние читается и пишется в Railway Volume.

При первом старте volume инициализируется шаблонами из `data/state`, но потом runtime-файлы больше не перезаписываются шаблонами.
