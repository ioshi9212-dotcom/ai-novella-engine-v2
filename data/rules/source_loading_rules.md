# Source Loading Rules

## Назначение файла

Этот файл описывает, какие источники ИИ должен подтягивать перед ответом.

Главная задача — собрать **точный минимальный контекст**, а не весь репозиторий.

---

## Главное правило

ИИ не должен подтягивать все файлы из:

```text
characters/
canon/
rules/
scenes/
```

Каждый ход должен иметь ограниченный список `required_files` по текущей сцене.

---

## Always required

Перед любым сценическим ответом нужны:

```text
data/canon/novella_goal.md
data/canon/inner_subtext_style.md
data/gpt/engine_prompt.md
data/gpt/scene_format.md
data/rules/source_loading_rules.md
data/rules/knowledge_rules.md
data/rules/player_control_rules.md
data/rules/relationship_state_rules.md
data/rules/character_rotation_rules.md
data/rules/npc_creation_rules.md
data/state/memory_update_rules.md
data/canon/canon_index.md
data/calendar/story_calendar.json
data/calendar/character_availability.json
data/state/current_state.json
data/state/knowledge_state.json
data/state/relationships.json
data/state/inventory_state.json
data/state/scene_history.json
```

Если state-файла нет, движок должен создать пустой шаблон, а не заменять его догадками.

---

## Knowledge / memory update rules

`data/state/memory_update_rules.md` обязателен, потому что он объясняет, как фиксировать знания персонажей после сцены.

Персонажи не получают знания автоматически.

Если персонаж что-то узнал, увидел, услышал, прочитал, понял, неправильно понял или наоборот не мог знать — это должно быть сохранено в:

```text
data/state/knowledge_state.json
data/state/scene_history.json
```

После раскрытия имени надо фиксировать `names_revealed_to_akira` и `speaker_labels`, чтобы ИИ не возвращался к старым дескрипторам вроде `женский голос снизу` после того, как имя уже известно.

Hidden lore нельзя записывать в `knows`, если персонаж не узнал это сценой.

---

## Calendar rules

`data/calendar/story_calendar.json` — единый источник календарных событий.

Его нужно учитывать перед:

- пропуском времени;
- переходом даты;
- появлением обязательной сцены;
- появлением персонажа, который доступен только после даты/события;
- рейдом;
- сценой Эхо;
- медблоком после прибытия на базу;
- сценами с Рэем до 7 сентября;
- возвращением Хару 21 сентября.

Календарь важнее импровизации.

Если игрок пропускает время, остановить пропуск на ближайшем `required=true` событии.

Если игрок активно действует, не прыгать резко к следующей дате.

Если событие уже произошло из-за действий игрока раньше, не повторять его дословно, а отметить как completed и двигаться дальше.

---

## Always character

Акира — персонаж игрока, поэтому всегда подтягивать:

```text
data/characters/main/akira.json
```

Если карточка Акиры содержит `linked_files`, подтянуть их тоже.

---

## Linked files

Если основной файл персонажа попал в `required_files`, все файлы из его `linked_files` автоматически добавляются в `required_files`.

`linked_files` нужны для:

- прошлого;
- скрытой биографии;
- травм и триггеров;
- подробных отношений;
- длинных правил раскрытия;
- расширенной истории персонажа.

Нельзя использовать `linked_files` как способ подтянуть весь лор мира.

---

## Active / nearby / speaking characters

### Active

Для каждого `active_character_ids` подтянуть карточку через:

```text
data/characters/character_id_index.json
```

и все его `linked_files`.

### Nearby

`nearby_character_ids` подтягивать только если персонаж:

- видит сцену;
- слышит сцену;
- может вмешаться;
- обязан реагировать по роли;
- влияет на напряжение;
- указан как observing.

### Speaking

Если NPC говорит, его карточка обязана быть в `required_files`.

Если карточки нет, реплика считается непроверенной.

---

## Scene file

Если есть `current_scene_id`, подтянуть:

```text
data/scenes/{current_scene_id}.json
```

Если сцена свободная и точного `scene_id` нет, использовать:

```text
data/state/current_state.json
data/state/scene_history.json
data/calendar/story_calendar.json
data/state/memory_update_rules.md
```

Если scene-файл содержит `required_files`, `required_canon_files`, `required_character_ids`, `scene_tags` — учитывать их.

---

## Canon by location

### Восточная база

Если `location_id = east_sector_base` или сцена происходит на Восточной базе, добавить:

```text
data/canon/east_sector_base.md
data/canon/relationships/east_sector_command_links.md
```

---

## Canon by scene tags / topic

### Energy

Если сцена содержит энергию, бой, тренировку, допуск, перегруз, рейд, энергетический профиль или классификацию:

```text
data/canon/energy_system.md
```

### Public world lore

Если сцена обсуждает общий мир, Эхо, кайросов, границу, публичные слухи и устройство мира:

```text
data/canon/world_public_lore.md
```

### Hidden world lore

Если сцене нужна скрытая причинность: баланс, реакция Эхо на Акиру, поиск источника, странные пространственные реакции:

```text
data/canon/world_hidden_lore.md
```

Важно: hidden-lore не даёт NPC автоматическое знание.

### Akira hidden past

Если сцена касается скрытого прошлого Акиры, Самуэля, Ирэя, Юны, Хару, причины амнезии, пустого гроба, старых медицинских фактов, старой утраты, срыва, шрама Рэя или того, кто что знает о прошлом:

```text
data/canon/akira_hidden_past.md
```

Важно: не превращать этот файл в прямой монолог и не давать персонажам знание без основания.

### Kairos lore

Если сцена содержит кайросов, беловолосых, материк кайросов, Ирэя, Эмму, Самуэля, попытку забрать Акиру или риск ложного вывода “вернуть Акиру домой”:

```text
data/canon/kairos_public_and_hidden.md
```

Главное: Акира никогда не была на материке кайросов. Материк кайросов не её дом.

### Akira + Raiden connection

Если сцена содержит Акиру и Райдена вместе, напряжение, защиту, ревность, странную синхронизацию, намёк на прошлую связь или выбор игрока между линиями:

```text
data/canon/relationships/akira_raiden_connection.md
```

Связь важная, но не клетка. Игрок не обязан выбирать Райдена.

### Raiden + Haru friendship

Если активен Райден или Хару и сцена может затронуть их дружбу, совместное прошлое, реакцию одного на другого или социальную динамику вокруг Акиры:

```text
data/canon/relationships/raiden_haru_friendship.md
```

Не вводить обоих всегда, но проверять, не должен ли второй быть рядом, в фоне, в реакции или следующей сцене.

### Inner subtext style

`inner_subtext_style.md` читается всегда.

Если сцена содержит внутренние мысли, телесные реакции, флешбеки, намёки, чувство без памяти, странную реакцию Райдена/Акиры/Хару — использовать:

```text
data/canon/inner_subtext_style.md
```

Мысли — это след, а не объяснение hidden-lore.

---

## Rule files by scene tags

### Start scene continuation

Если сцена — start_scene или непосредственное продолжение после первого действия игрока:

```text
data/rules/start_scene_continuation_rules.md
data/calendar/story_calendar.json
data/state/memory_update_rules.md
```

### Timeline / Echo

Если дата раньше `1206-09-15` или есть риск случайно ввести Эхо до первого рейда:

```text
data/rules/timeline_event_rules.md
data/calendar/story_calendar.json
```

До первого рейда активные Эхо не появляются, но энергия персонажей разрешена.

### Akira current overrides

Если сцена касается текущей памяти, инвентаря, ограничений Рэя, ранней Академии, пространственных сбоев или текущего состояния Акиры:

```text
data/rules/akira_current_overrides.md
```

---

## Role / calendar loading

### Medical scene

Если сцена в медблоке, содержит осмотр, травму, восстановление, медицинский протокол или нужен именной медик:

```text
data/characters/main/yuna.json
data/characters/main/yuna_history.json
data/calendar/character_availability.json
data/calendar/story_calendar.json
data/rules/npc_creation_rules.md
```

Если сцена касается старых шрамов, Самуэля, перегрузов, странного узнавания Юны или скрытых медицинских фактов Акиры, добавить:

```text
data/canon/akira_hidden_past.md
```

Юна доступна — не создавать случайного врача.

### Echo / energy specialist after contact

Если после контакта Акиры с Эхо нужен специалист по кайросам, энергии, гибридам или аномальной реакции:

```text
data/characters/main/natsu.json
data/characters/main/natsu_history.json
data/calendar/character_availability.json
data/calendar/story_calendar.json
```

Нацу не появляется до первого контакта Акиры с Эхо или его последствий.

### New NPC request

Если сцена требует нового NPC или служебную роль, сначала проверить:

```text
data/rules/character_rotation_rules.md
data/rules/npc_creation_rules.md
data/calendar/character_availability.json
data/calendar/story_calendar.json
data/characters/character_id_index.json
data/state/memory_update_rules.md
```

Новый NPC допустим только если нет канонного или уже закреплённого персонажа для этой роли.

---

## Active / nearby shortcuts

Если в active/nearby есть:

```text
irey
emma
samuel
```

добавить:

```text
data/canon/kairos_public_and_hidden.md
```

Если в active/nearby есть `yuna` и сцена касается Акиры, тела, шрамов, Самуэля, старых медицинских фактов или странного узнавания:

```text
data/canon/akira_hidden_past.md
```

Если в active/nearby есть `irey` и сцена касается прошлого Акиры, Самуэля, амнезии или поиска за два года:

```text
data/canon/akira_hidden_past.md
```

Если есть одновременно `akira` и `raiden` и сцена эмоционально/лично значима:

```text
data/canon/relationships/akira_raiden_connection.md
```

Если есть `raiden` или `haru` и сцене важна их связка:

```text
data/canon/relationships/raiden_haru_friendship.md
```

---

## Forbidden loading

Нельзя подтягивать:

- все карточки персонажей сразу;
- все canon-файлы сразу;
- hidden lore без явной причины;
- future/hidden relationship lore без нужной сцены;
- старые scene-файлы, если `current_state` ушёл дальше;
- случайного врача вместо Юны;
- случайного специалиста вместо Нацу после события Эхо;
- NPC registry как замену конкретной карточке.

Нельзя превращать календарь в автоспойлер: future events направляют порядок, но не раскрываются игроку прямым текстом.
