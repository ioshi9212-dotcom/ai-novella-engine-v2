# Source Loading Rules

Этот файл описывает, какие источники ИИ должен подтягивать перед ответом.

## Главное правило

ИИ не должен подтягивать все файлы из `characters/`, `canon/`, `rules/` или `scenes/`.

Каждый ход должен иметь ограниченный список `required_files`.

---

## Always required

Перед любым сценическим ответом нужны:

```text
data/gpt/engine_prompt.md
data/gpt/scene_format.md
data/rules/source_loading_rules.md
data/rules/knowledge_rules.md
data/rules/player_control_rules.md
data/canon/canon_index.md
data/state/current_state.json
data/state/knowledge_state.json
data/state/relationships.json
data/state/inventory_state.json
data/state/scene_history.json
```

Если какого-то state-файла ещё нет, движок должен создать пустой шаблон, а не заменять его догадками.

---

## Always character

Акира — персонаж игрока, поэтому её карточка нужна всегда:

```text
data/characters/main/akira.json
```

Правила управления Акирой должны быть внутри её карточки и в `player_control_rules.md`.

Если карточка Акиры содержит `linked_files`, подтянуть их тоже.

---

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

---

## Active characters

`active_character_ids` — персонажи, которые находятся в активной сцене и могут говорить, действовать или напрямую реагировать.

Для каждого active-персонажа нужно подтягивать его карточку из:

```text
data/characters/character_id_index.json
```

Если карточка содержит `linked_files`, подтянуть их тоже.

---

## Nearby characters

`nearby_character_ids` — персонажи рядом, но не обязательно участвующие в сцене.

Их карточки нужны только если персонаж:

- видит сцену;
- слышит сцену;
- может вмешаться;
- является объектом реплики;
- обязан отреагировать по статусу/должности;
- указан в `scene_participants` как `observing`.

Если nearby-персонаж не видит, не слышит и не влияет на сцену, его карточку не подтягивать.

Если nearby-персонаж подтянут, его `linked_files` тоже подтягиваются.

---

## Speaking characters

Перед каждой репликой NPC ИИ должен проверить карточку говорящего персонажа.

Если персонаж говорит, но его карточки нет в `required_files`, ответ считается непроверенным.

---

## Observing characters

Наблюдающий персонаж не обязан говорить.

Но если его присутствие меняет напряжение сцены, субординацию, безопасность, доступ к информации или реакцию других — карточка нужна.

---

## Scene files

Если `current_scene_id` есть, подтянуть:

```text
data/scenes/{current_scene_id}.json
```

Если текущая сцена свободная и точного `scene_id` нет, использовать `current_state.last_scene_anchor` и state-файлы.

Если файл сцены содержит поля:

```json
{
  "required_files": [],
  "required_canon_files": [],
  "required_character_ids": [],
  "scene_tags": []
}
```

они должны учитываться при сборке `required_files`.

---

## Canon index

Файл:

```text
data/canon/canon_index.md
```

читается всегда как оглавление canon-источников.

Он не заменяет сами canon-файлы.

Он нужен, чтобы выбрать нужный canon-файл под сцену.

---

## Canon files by location

Локационные canon-файлы читаются только при сценах в этой локации.

### Восточная база

Если:

```text
location_id = east_sector_base
```

или сцена происходит на Восточной базе, добавить:

```text
data/canon/east_sector_base.md
```

Этот файл нужен для всех сцен на базе: двор, фонтан, медблок, общежитие, столовая, спортзал, тренировочный зал, баскетбольная площадка, административное здание, рейдовые зоны.

---

## Canon files by scene tags

### Energy

Если `scene_tags` содержит:

```text
energy
training
combat
raid
overload
energy_profile
energy_classification
admission
```

или в сцене есть применение энергии, бой, тренировка, перегруз, допуск, сравнение силы, добавить:

```text
data/canon/energy_system.md
```

### Public world lore

Если `scene_tags` содержит:

```text
world_lore
echo
kairos
border
public_world
```

или в сцене обсуждается общий мир, Эхо, кайросы, границы, вспышки, добавить:

```text
data/canon/world_public_lore.md
```

### Hidden world lore

Если `scene_tags` содержит:

```text
hidden_world_lore
akira_balance
echo_reaction
space_anomaly
```

или нужно внутренне понять странную реакцию Эхо на Акиру, рост Эхо после её пропажи, поиск источника баланса, добавить:

```text
data/canon/world_hidden_lore.md
```

Важно: `world_hidden_lore.md` не даёт NPC автоматическое знание. Он нужен для поведения мира и скрытой причинности.

### Kairos lore

Если `scene_tags` содержит:

```text
kairos
kairos_hidden
irey
emma
samuel
white_haired
kairos_mainland
```

или в сцене есть кайросы, беловолосые, материк кайросов, попытка забрать Акиру, Ирей, Эмма, Самуэль или риск ложного вывода “вернуть Акиру домой”, добавить:

```text
data/canon/kairos_public_and_hidden.md
```

Главное правило: Акира никогда не была на материке кайросов. Материк кайросов не является её домом. Ирэй, Эмма и Самуэль не должны трактоваться как персонажи, которые хотят “вернуть её к своим”.

### Akira and Raiden connection

Если `scene_tags` содержит:

```text
akira_raiden_connection
relationship_tension
romance_tension
raiden_jealousy
raiden_protection
raiden_memory_tension
reincarnation_cycle
```

или в сцене есть Акира и Райден вместе, их напряжение, защита, ревность, странная синхронизация, выбор между Райденом и другим персонажем, добавить:

```text
data/canon/relationships/akira_raiden_connection.md
```

Важно: файл связи не заставляет игрока выбирать Райдена. Он нужен для естественной реакции Райдена, Акиры и окружающих.

---

## Canon files by active/nearby characters

Если в `active_character_ids` или подтянутых `nearby_character_ids` есть:

```text
irey
emma
samuel
```

добавить:

```text
data/canon/kairos_public_and_hidden.md
```

Если в сцене есть одновременно:

```text
akira
raiden
```

и сцена содержит эмоциональное напряжение, защиту, ревность, личный конфликт, странную реакцию или намёк на прошлую связь, добавить:

```text
data/canon/relationships/akira_raiden_connection.md
```

Если в сцене есть Эхо или странная реакция Эхо на Акиру, добавить:

```text
data/canon/world_public_lore.md
data/canon/world_hidden_lore.md
```

Если персонаж применяет энергию или обсуждает профиль/допуск, добавить:

```text
data/canon/energy_system.md
```

---

## Forbidden loading

Нельзя подтягивать:

- карточки всех персонажей сразу;
- все canon-файлы сразу;
- hidden lore без явной причины;
- future/hidden relationship lore без сцены, где это реально нужно;
- будущие события как текущую правду;
- старые scene-файлы, если `current_state` уже ушёл дальше;
- rules/locks, не относящиеся к сцене;
- NPC registry как замену карточке конкретного NPC.

Нельзя превращать hidden-lore в реплику NPC.

---

## Required files output

Каждый `turn-contract` должен возвращать:

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

---

## Минимальный self-check перед ответом

Перед генерацией сцены ИИ должен проверить:

1. Загружена ли карточка Акиры.
2. Подтянуты ли `linked_files` Акиры.
3. Загружены ли карточки говорящих NPC.
4. Подтянуты ли `linked_files` для загруженных персонажей.
5. Проверен ли `knowledge_state` перед утверждениями NPC.
6. Не попал ли hidden lore в реплику персонажа.
7. Не пишет ли ИИ решение за Акиру.
8. Не подтянуты ли лишние персонажи.
9. Соответствует ли локация нужному canon-файлу.
10. Подтянут ли `energy_system.md`, если в сцене есть энергия.
11. Подтянут ли `kairos_public_and_hidden.md`, если в сцене есть кайросы, Ирэй, Эмма или Самуэль.
12. Не сделан ли ложный вывод, что Акиру хотят вернуть на материк кайросов.
13. Если подтянут `akira_raiden_connection.md`, не сводит ли ИИ Акиру и Райдена насильно и не обесценивает ли выбор игрока.
