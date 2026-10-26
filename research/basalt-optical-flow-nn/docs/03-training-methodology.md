# Методика обучения нейросетевых optical flow

Раздел для статьи (ВАК) и для этапа T4 (student). Классика и Basalt SE2 **не обучаются** — ниже только NN.

## 1. Общий пайплайн supervised optical flow

Типичная схема (RAFT / PWC / FlowFormer и др.):

```text
FlyingChairs (C)
    → FlyingThings3D (T)
        → fine-tune: Sintel + KITTI + HD1K  (S+K+H)
```

Обозначения в таблицах статей: **C+T** (zero-shot generalization на Sintel/KITTI train) и **C+T+S+K+H** (финтюн под бенчмарк).

### 1.1 Датасеты обучения

| Датасет | Тип | Зачем |
|---------|-----|--------|
| FlyingChairs | synthetic chairs on backgrounds | быстрый старт, крупные смещения |
| FlyingThings3D | synthetic 3D | сложные сцены, occlusion |
| Sintel (train) | movie synthetic | domain для бенчмарка |
| KITTI (train) | real | real-world fine-tune |
| HD1K | real | доп. diversity |
| AutoFlow / др. | synthetic large-scale | альтернатива C (Perceiver IO, часть новых работ) |

### 1.2 Loss (supervised)

Пусть \(F_k\) — предсказание на итерации/уровне \(k\), \(F^*\) — GT:

\[
\mathcal{L}_{\mathrm{sup}} = \sum_k w_k \, \rho\bigl(F_k - F^*\bigr)
\]

где \(\rho\) — L1, L2 или robust (Smooth L1 / Charlier). Веса \(w_k\) растут к финальному выходу (как в RAFT).

Опционально:

- occlusion mask (не штрафовать окклюзии, если есть разметка / forward–backward);
- edge-aware smoothness (реже в современных iterative моделях).

### 1.3 Инференс-трюки (не путать с обучением)

- **Warm-start** (RAFT*): инициализация flow с предыдущей пары кадров в видео — улучшает Sintel test, но это не «два кадра независимо».
- **Tile** на больших разрешениях (FlowFormer†) — режет картинку на тайлы.

В нашем протоколе сравнения по умолчанию: **два кадра, cold start**, без warm-start — честнее для VIO frame-to-frame.

## 2. Методики по семействам (кратко для таблицы обзора)

| Семейство | Архитектурная суть | Типичный schedule | Loss |
|-----------|--------------------|-------------------|------|
| FlowNet / FlowNet2 | encoder–decoder / stack | C→T→S/K | L2 |
| PWC-Net | pyramid + CV + warp | C→T→S/K | multi-scale L2 |
| Lite/FastFlowNet | compact PWC-like | C→T→S/K | multi-scale |
| RAFT / SEA-RAFT | correlation lookup + GRU | C→T (+S+K+H) | weighted L1 по итерациям |
| GMA / CRAFT / SKFlow | RAFT + attention / priors | как RAFT | как RAFT |
| GMFlow | global matching + transformer | C→T (+fine-tune) | L1 + matching |
| FlowFormer (+MCVA) | cost-volume transformer; MAE pretrain | C→T→S+K+H; MCVA на unlabeled | L1 + pretrain recon |

Pretrained weights: для T2-сравнения допустимы **официальные чекпоинты** при условии, что schedule и resolution задокументированы; для fair student — одинаковый train protocol.

## 3. Методика для нашей student-сети (цель работы)

Гипотеза: аппроксимировать **Basalt SE2** быстрее, сохранив sparse-качество.

### 3.1 Teacher labels

На последовательностях без dense GT (EuRoC / свои):

1. Прогнать Basalt SE2 → треки \((p_1, p_2)\) и/или SE(2)-параметры патча.
2. Опционально растеризовать sparse в dense prior только в окрестности патчей (не полный dense GT).

На Sintel/KITTI teacher не заменяет GT, а добавляет **distillation** на тех же точках/патчах.

### 3.2 Составной loss (план T4)

\[
\mathcal{L} = \alpha\,\mathcal{L}_{\mathrm{EPE}}(F, F^{\mathrm{GT}})
+ \beta\,\mathcal{L}_{\mathrm{distill}}(F, F^{\mathrm{Basalt}})
+ \gamma\,\mathcal{L}_{\mathrm{temp}}
\]

- \(\mathcal{L}_{\mathrm{EPE}}\) — только где есть GT.
- \(\mathcal{L}_{\mathrm{distill}}\) — L1/L2 на flow в keypoints / на SE(2)-параметрах патча (предпочтительнее для teacher SE2).
- \(\mathcal{L}_{\mathrm{temp}}\) — согласованность соседних пар (опционально).

Коэффициенты \(\alpha,\beta,\gamma\) — предмет ablation в статье.

### 3.3 Архитектура student

Критерии выбора (после T2 Pareto):

- мало MACs / params;
- экспорт в ONNX → RKNN INT8;
- достаточная точность на sparse protocol vs Basalt.

Кандидаты: FastFlowNet, LiteFlowNet3, SEA-RAFT-small, кастомный CNN/RAFT-tiny.

### 3.4 Аугментации (стандарт OF)

Photometric (brightness/contrast/gamma), spatial (crop, scale, flip, rotation), occlusion / eraser — как в RAFT codebase. Для distillation на реальных кадрах Basalt — осторожнее с геометрией (согласовать teacher и student на одной аугментации).

## 4. Что фиксировать в статье

1. Полный schedule (эпохи, LR, batch, crop size).
2. Источник pretrained (URL + hash), если использовался.
3. Ablation: \(\beta=0\) (без Basalt) vs с distillation.
4. Отдельная таблица: качество **до** квантизации (GPU FP32) и **после** RKNN INT8.

## 5. Связь с репозиторием

- Сравнение pretrained / классики: `src/compare.py` (T2).
- Обучение student: отдельный модуль на этапе T4 (пока не в каркасе T1).
- Конфиг экспериментов: `configs/default.yaml` (+ будущие `configs/train_*.yaml`).
