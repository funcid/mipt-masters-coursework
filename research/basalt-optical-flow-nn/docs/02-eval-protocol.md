# Протокол оценки (единое пространство)

Связан с `configs/default.yaml` и `src/compare.py`. Прогоны — на **отдельной** машине (GPU / затем RK3588), не на ноутбуке разработки.

## 1. Датасеты

### 1.1 С плотным GT

| Датасет | Что даёт | Как использовать |
|---------|----------|------------------|
| **MPI Sintel** (clean / final) | synthetic movie, dense flow `.flo` | основная dense-таблица; clean = «лёгкий», final = артефакты/blur |
| **KITTI 2015** | real driving, sparse-ish GT + Fl-all | обобщение на реальность; метрика Fl-all |

Пути по умолчанию: `data/sintel`, `data/kitti2015` (см. README).

### 1.2 Без dense GT (teacher / VIO-реализм)

| Датасет | Роль |
|---------|------|
| EuRoC MAV | stereo + IMU; Basalt SE2 → pseudo-labels / track quality |
| TUM-VI | аналогично |
| Свои записи под целевой робот/камеру | финальная проверка под deployment |

На этих данных **нет** честного dense EPE; метрики: success rate треков, reprojection / VIO ATE при встраивании в Basalt (этап T3+).

## 2. Два протокола в одном эксперименте

### 2.1 Dense protocol

1. Вход: пара кадров \(I_t, I_{t+1}\), GT flow \(F^*\).
2. Метод выдаёт \(F\).
3. Считаем: EPE, % пикселей с ошибкой &lt;1/3/5 px, Fl-all (порог 3 px и 5% от \|F\*\|).
4. Valid mask: по правилам датасета (KITTI) / конечные пиксели Sintel.

Применимо к: Farneback, DIS, всем dense NN.  
**Не** применимо напрямую к LK / Basalt SE2 без растеризации (не делаем без явной оговорки).

### 2.2 Sparse protocol (fair vs Basalt)

1. На \(I_t\) детектируем keypoints **один раз** (Shi-Tomasi или FAST; конфиг `sparse_protocol` в YAML).
2. Те же точки подаём:
   - LK / Basalt как вход трекера;
   - dense-методам: lookup \(F(x,y)\) → \(p_2 = p_1 + F(p_1)\).
3. Если есть dense GT: sparse endpoint = \(\|p_2^{\mathrm{pred}} - (p_1 + F^*(p_1))\|\).
4. Дополнительно: `success_rate` (доля треков со status=1 у LK/Basalt).

Так LK, Basalt и NN сравнимы в **одной** sparse-колонке.

## 3. Разрешения и latency

Фиксируем в конфиге:

- 640×480  
- 1280×720  

Для latency:

1. Warmup: 5 кадров (без записи).
2. Замер: среднее по 50 кадрам, `time.perf_counter` вокруг `predict`.
3. Отдельно документировать: CPU only / CUDA / RK3588 NPU.
4. Батч = 1 (онлайн VIO).

На RK3588 (этап T5): тот же протокол после конвертации ONNX→RKNN; цель **≥20 FPS** на выбранном рабочем разрешении (зафиксировать в статье одно «боевое»).

## 4. Что писать в CSV / таблицу статьи

Минимальные колонки (см. `results/comparison.csv` после прогона):

- `method`, `kind`, `resolution`
- dense: `epe`, `px1`, `px3`, `px5`, `fl_all`
- sparse: `endpoint_epe`, `success_rate`, `n_tracks`
- `latency_ms` (или FPS = 1000/latency_ms)

Строки `status=not_implemented` — stubs (RAFT/Basalt), пока не подключены веса/бинарь.

## 5. Воспроизводимость (ВАК)

- Зафиксировать: git commit, версии `opencv`, `torch`, CUDA, драйвер NPU.
- `experiment.seed` в YAML.
- Не смешивать literature numbers и свои прогоны в одной ячейке без пометки.
- Конфиг эксперимента класть рядом с CSV в `results/`.

## 6. Smoke-тест без датасетов

```bash
cd research/basalt-optical-flow-nn
python -m src.compare --synthetic
```

Синтетическая пара со сдвигом (dx, dy) проверяет LK/Farneback и пайплайн CSV. Нейросети и Basalt останутся `not_implemented`, пока не включены в YAML и не установлены.
