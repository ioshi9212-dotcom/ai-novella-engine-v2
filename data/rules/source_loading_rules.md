# Source Loading Rules

Этот файл описывает, какие источники ИИ должен подтягивать перед ответом.

## Главное правило

ИИ не должен подтягивать все файлы из `characters/`, `canon/`, `rules/` или `scenes/`.

Каждый ход должен иметь ограниченный список `required_files`.

## Always required

Перед любым сценическим ответом нужны:

```text
data/gpt/engine_prompt.md
data/gpt/scene_format.md
data/rules/source_loading_rules.md
data/rules/knowledge_rules.md
data/rules/player_control_rules.md
data/state/current_state.json
data/state/knowledge_state.json
data/state/relationships.json
data/state/inventory_state.json
data/state/scene_history.json
```

Если какого-то state-файла ещё нет, движок должен создать пустой шаблон, а не заменять его догадками.

## Always character

Акира — персонаж игрока, поэтому её карточка нужна всегда:

```text
data/characters/main/akira.json
```

Правила управления Акирой должны быть внутри её карточки и в `player_control_rules.md`.

## Linked files

Основная карточка персонажа может содержать поле:

```json
{
  "linked_files": [
    "data/characters/main/akira_history.json"
  ]
}
```

Если основной файл персонажа попал в `required_files`, все файлы из его `linked_files` тоже должны быть автоматически добавлены в `required_files`.

`linked_files` нужны для расширенной информации, которую нельзя держать в основной карточке:

- прошлое;
- скрытая биография;
- подробная временная линия;
- травмы и триггеры;
- связи через прошлые события;
- длинные правила раскрытия;
- расширенные детали отношений.

Главное правило: основной файл должен быть быстрым для сцены, а linked-файл должен давать глубину, если персонаж активен.

Нельзя использовать linked-файлы как способ подтянуть весь лор мира.

## Active characters

`active_character_ids` — персонажи, которые находятся в активной сцене и могут говорить, действовать или напрямую реагировать.

Для каждого active-персонажа нужно подтягивать его карточку из `data/characters/character_id_index.json`.

Если карточка содержит `linked_files`, подтянуть их тоже.

## Nearby characters

`nearby_character_ids` — персонажи рядом, но не обязательно участвующие в сцене.

Их карточки нужны только если персонаж:

- видит сцену;
- слышит сцену;
- может вмешаться;
- является объектом реплики;
- обязан отреагировать по статусу/должности;
- указан в scene_participants как observing.

Если nearby-персонаж не видит, не слышит и не влияет на сцену, его карточку не подтягивать.

Если nearby-персонаж подтянут, его `linked_files` тоже подтягиваются.

## Speaking characters

Перед каждой репликой NPC ИИ должен проверить карточку говорящего персонажа.

Если персонаж говорит, но его карточки нет в required_files, ответ считается непроверенным.

## Observing characters

Наблюдающий персонаж не обязан говорить.

Но если его присутствие меняет напряжение сцены, субординацию, безопасность, доступ к информации или реакцию других — карточка нужна.

## Scene files

Если `current_scene_id` есть, подтянуть:

```text
data/scenes/{current_scene_id}.json
```

Если текущая сцена свободная и точного scene_id нет, использовать `current_state.last_scene_anchor` и state-файлы.

## Canon files by location

Локационные canon-файлы читаются только при сценах в этой локации.

Пример:

```text
location_id = east_sector_base
required_files includes data/canon/east_sector_base.md
```

## Forbidden loading

Нельзя подтягивать:

- карточки всех персонажей сразу;
- hidden lore без явной причины;
- будущие события как текущую правду;
- старые scene-файлы, если current_state уже ушёл дальше;
- rules/locks, не относящиеся к сцене;
- NPC registry как замену карточке конкретного NPC.

## Required files output

Каждый turn-contract должен возвращать:

```json
{
  "required_files": [],
  "active_character_ids": [],
  "nearby_character_ids": [],
  "scene_participants": [],
  "forbidden_files": [],
  "required_checks_before_answer": []
}
```

## Минимальный self-check перед ответом

Перед генерацией сцены ИИ должен проверить:

1. Загружена ли карточка Акиры.
2. Загружены ли карточки говорящих NPC.
3. Подтянуты ли `linked_files` для загруженных персонажей.
4. Проверен ли `knowledge_state` перед утверждениями NPC.
5. Не попал ли hidden lore в реплику персонажа.
6. Не пишет ли ИИ решение за Акиру.
7. Не подтянуты ли лишние персонажи.
8. Соответствует ли локация нужному canon-файлу.
