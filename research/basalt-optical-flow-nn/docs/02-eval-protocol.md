# Протокол оценки (единое пространство)

Связан с `configs/default.yaml` и `src/compare.py`.

**Eval-машина (T2):** Windows 10, NVIDIA GeForce RTX 4080, драйвер NVIDIA 610.88 / CUDA UMD 13.3, runtime PyTorch CUDA **12.4**. Дальше — RK3588 (T5).

## 1. Датасеты

### 1.1 С плотным GT

| Датасет | Что даёт | Как использовать |
|---------|----------|------------------|
| **MPI Sintel** (clean / final) | synthetic movie, dense flow `.flo` | основная dense-таблица; clean = «лёгкий», final = артефакты/blur |
| **KITTI 2015** | real driving, sparse-ish GT + Fl-all | обобщение на реальность; метрика Fl-all |

Пути по умолчанию: `data/sintel`, `data/kitti2015` (см. README). На T2: Sintel распакован; KITTI в YAML `enabled: false`.

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

Строки `status=not_implemented` — stubs (FlowFormer / Lite/FastFlowNet / Basalt), пока не подключены веса/бинарь.  
На T2 рабочие runners: LK, Farneback, DIS, RAFT, SEA-RAFT, GMFlow.

## 5. Воспроизводимость (ВАК)

Зафиксированный стек T2 (этот ПК):

| Компонент | Версия |
|-----------|--------|
| Python | 3.11.0 |
| OpenCV (`opencv-python`) | 5.0.0 |
| NumPy | 2.4.6 |
| SciPy | 1.17.1 |
| PyTorch | 2.6.0+cu124 |
| CUDA (torch) | 12.4 |
| GPU | NVIDIA GeForce RTX 4080 |
| NVIDIA driver | 610.88 |
| RAFT | `princeton-vl/RAFT` + `raft-sintel.pth`, iters=20 |

Также: git commit репозитория, `experiment.seed` в YAML.  
Не смешивать literature numbers и свои прогоны в одной ячейке без пометки.  
Конфиг эксперимента класть рядом с CSV в `results/`.

Текущий `compare.py` берёт **одну** первую доступную Sintel-пару (smoke / protocol check). Полный average по training — отдельный цикл (следующий шаг после T2).

## 6. Smoke-тест без датасетов

```powershell
cd research/basalt-optical-flow-nn
.\.venv\Scripts\Activate.ps1
python -m src.compare --synthetic
```

Синтетическая пара со сдвигом (dx, dy) проверяет LK / Farneback / RAFT и пайплайн CSV. Basalt и прочие stubs останутся `not_implemented`, пока не включены в YAML.
