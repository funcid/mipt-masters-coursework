# Нейросетевая аппроксимация Basalt SE2 optical flow (ВАК)

Исследовательский каркас: единое сравнение классики / нейросетей / Basalt SE2, методика обучения и заготовка бенчмарка.

**Прогоны считайте на другой машине** (GPU Ubuntu + позже RK3588). Этот репозиторий на Mac — для кода и текстов.

## Цель

Teacher: **Basalt SE2** sparse optical flow (качество высокое, медленный).  
Student: компактная NN → качество ≈ Basalt, **≥20 FPS на RK3588**.

Документы:

| Файл | Содержание |
|------|------------|
| [docs/01-survey-comparison.md](docs/01-survey-comparison.md) | Обзор и единая таблица сравнения |
| [docs/02-eval-protocol.md](docs/02-eval-protocol.md) | Протокол метрик и датасетов |
| [docs/03-training-methodology.md](docs/03-training-methodology.md) | Методика обучения NN + distillation |

## Структура

```text
research/basalt-optical-flow-nn/
  configs/default.yaml
  docs/
  src/
    compare.py          # entrypoint → results/*.csv
    metrics.py
    runners/            # LK, Farneback, stubs RAFT/Basalt
  data/                 # датасеты (не в git)
  results/              # CSV/MD после прогона
```

## Установка (машина с CUDA)

```bash
cd research/basalt-optical-flow-nn
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Для нейросетей (пример):
# pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

Системные зависимости: OpenCV ставится из pip; для Basalt — сборка C++ (ниже).

## Датасеты

Положите под `data/` (или поправьте пути в `configs/default.yaml`):

**Sintel** — [MPI Sintel](http://sintel.is.tue.mpg.de/):  
`data/sintel/training/{clean,final,flow}/...`

**KITTI 2015** — [KITTI flow](https://www.cvlibs.net/datasets/kitti/eval_scene_flow.php?benchmark=flow):  
`data/kitti2015/...`

**EuRoC** (teacher, опционально на T3): `data/euroc/...`

## Быстрый прогон

Список методов:

```bash
python -m src.compare --list-methods
```

Smoke-тест без датасетов (синтетический сдвиг; LK + Farneback):

```bash
python -m src.compare --synthetic
```

Если Sintel лежит в `data/sintel`, достаточно:

```bash
python -m src.compare --config configs/default.yaml
```

Пара кадров вручную:

```bash
python -m src.compare --pair /path/a.png /path/b.png --flow-gt /path/gt.flo
```

Результаты: `results/comparison.csv`, `results/comparison.md`.

В `configs/default.yaml` по умолчанию **включены** только `opencv_lk` и `opencv_farneback`. RAFT/Basalt — stubs (`enabled: false`).

## Подключение нейросетей (T2)

1. Клонировать официальный репозиторий (RAFT / SEA-RAFT / GMFlow / …).
2. Скачать pretrained weights.
3. В YAML: `methods[].enabled: true`, указать `weights` и `device: cuda`.
4. Реализовать загрузку в `src/runners/raft_stub.py` (или отдельный runner) — интерфейс `predict(img1, img2) -> FlowResult` с `flow_dense` HxWx2.

Пока stub поднимает `NotImplementedError` → в CSV строка `status=not_implemented`.

## Basalt SE2 (teacher)

1. Собрать [Basalt](https://gitlab.com/VladyslavUsenko/basalt) на Linux (зависимости: Eigen, Sophus, OpenCV, TBB и т.д. — см. upstream README).
2. Написать тонкий CLI или pybind: пара кадров (+ keypoints) → `points1`, `points2`, `status`, опционально `se2_params`.
3. В YAML:

```yaml
  - id: basalt_se2
    enabled: true
    kind: sparse_se2
    binary: /path/to/basalt_of_cli
    config: /path/to/basalt_config.json
```

4. Дописать I/O в `src/runners/basalt_stub.py` (сейчас — контракт и заглушка).

## RK3588 (этап T5, не T1)

После обучения student: экспорт ONNX → RKNN Toolkit 2 → замер FPS тем же протоколом разрешения. Цель: **≥20 FPS**. Python-каркас здесь только для сравнения; прод-инференс на плате обычно C++/RKNN runtime.

## Этапы

| Этап | Статус |
|------|--------|
| T1 Обзор + протокол + каркас бенчмарка | этот каталог |
| T2 Прогон baselines на GPU | на вашей машине |
| T3 Basalt teacher / labels | |
| T4 Обучение student + distillation | |
| T5 RK3588 ≥20 FPS | |
| T6 Черновик статьи ВАК | |

## Цитирование идей (не полный список)

Basalt (Usenko et al.); RAFT; SEA-RAFT; GMFlow; FlowFormer; PWC-Net; LiteFlowNet; FastFlowNet — см. `docs/01-survey-comparison.md`.
