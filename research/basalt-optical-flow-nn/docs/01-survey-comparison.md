# Обзор: optical flow в едином пространстве сравнения

Документ для раздела «Обзор» статьи (ВАК). Цель — сопоставить классические, нейросетевые и Basalt SE2 методы по **одним и тем же осям**, без смешения dense EPE и sparse tracking без оговорок.

## 1. Постановка

**Optical flow** — поле соответствий пикселей (или патчей) между двумя кадрами. В Visual-Inertial Odometry / SLAM front-end обычно нужен **sparse tracking** ключевых точек с высокой точностью и предсказуемой задержкой.

**Basalt** (Usenko et al.) использует inverse-compositional patch tracking с варпом в группе **SE(2)** (сдвиг + поворот в плоскости кадра) и фотометрической нормой LSSD. Качество трекинга высокое, но вычислительно тяжело на встраиваемых CPU — отсюда задача **нейросетевой аппроксимации** с целевым realtime **≥20 FPS на RK3588**.

## 2. Оси сравнения (одинаковые для всех методов)

| Ось | Что фиксируем |
|-----|----------------|
| Тип выхода | `dense` 2D flow / `sparse` (tx,ty) / `sparse_se2` (tx,ty,θ[,s]) |
| Модель движения | translation / affine / SE(2) / произвольное dense |
| Нужен ли GT для работы | нет (классика, Basalt) / да на этапе обучения (NN) |
| Качество dense | EPE, % &lt;1/3/5 px, Fl-all (KITTI) |
| Качество sparse | endpoint EPE на общих keypoints, success rate |
| Latency | ms/frame @ 640×480 и 1280×720 (одна машина + отдельно RK3588) |
| Сложность NN | #params, MACs |
| Устойчивость | illumination, large motion, textureless, occlusion |

**Правило:** dense-метрики и sparse-метрики — **две колонки**. Dense NN оценивается на Sintel/KITTI; для fair sparse — семплирование flow в тех же точках, что у LK/Basalt (см. `02-eval-protocol.md`).

## 3. Классические (инженерные) методы

### 3.1 Lucas–Kanade / pyramidal KLT

- **Выход:** sparse translation (2 DoF на точку).
- **Идея:** локальная brightness constancy, линеаризация; пирамида — для large motion.
- **Плюсы:** быстрый, стандарт OpenCV, детерминированный.
- **Минусы:** нет явного вращения/масштаба патча; ломается на сильной ротации, освещении, textureless.
- **Роль в работе:** обязательный baseline.

### 3.2 Farneback

- **Выход:** dense polynomial expansion flow.
- **Плюсы:** нет обучения, плотное поле «из коробки».
- **Минусы:** слабее современных NN по EPE; не SE(2).
- **Роль:** dense classical baseline.

### 3.3 (опционально) DIS / TV-L1

- DIS (Dense Inverse Search) — быстрый dense; TV-L1 — variational.
- Включать, если нужна полнота инженерного спектра; не обязательны для главного тезиса Basalt→NN.

## 4. Basalt SE2 optical flow (teacher)

- **Источник:** Basalt VIO frontend — patch-based OF, inverse compositional, warp \(T \in \mathrm{SE}(2)\).
- **Выход:** sparse SE(2) (типично \(t_x, t_y, \theta\)); паттерн точек в патче (Pattern5x), норма LSSD (устойчивость к scale освещения).
- **Сильные стороны:** точность трекинга под VIO; явная модель поворота патча vs чистый LK.
- **Слабые стороны:** итеративный Gauss–Newton на каждый патч → **медленно** на встраиваемых CPU; не realtime на RK3588 «как есть».
- **Роль:** **teacher** для distillation и верхняя планка sparse-качества.

Связанные работы: интеграция deep OF в Basalt VIO (Feng et al., TUM) — NN как prior + уточнение; LET-SE2-VINS — hybrid LET-NET + SE2 KLT. Наша постановка ближе к **аппроксимации самого SE2-трекера**, а не только к замене prior.

## 5. Нейросетевые методы (представители семейств)

Числа EPE ниже — ориентиры из оригинальных статей / обзоров (train/test и schedule различаются; в эксперименте заполняем **своими** прогонами в одном протоколе).

### 5.1 Исторические CNN

| Метод | Идея | Ориентир Sintel (test, C+T+…) | Заметки |
|-------|------|------------------------------|---------|
| FlowNet2 | stacked encoder–decoder | ~2–4 EPE (зависит от версии) | тяжёлый, устаревший baseline |
| PWC-Net | pyramid + cost volume + warping | ~3.5 / 4.6 (clean/final, типичные отчёты) | компактнее FlowNet2 |

**Обучение (кратко):** FlyingChairs → FlyingThings; fine-tune Sintel/KITTI; L2/L1 на flow. Детали — `03-training-methodology.md`.

### 5.2 Iterative refinement

| Метод | Идея | Ориентир | Заметки |
|-------|------|----------|---------|
| RAFT | all-pairs correlation + GRU updates | Sintel test ~1.61 / 2.86 (warm-start*); KITTI Fl-all ~5.1 | de-facto baseline с 2020 |
| SEA-RAFT | упрощённый/ускоренный RAFT | конкурентоспособен с RAFT, быстрее | кандидат accuracy–speed |
| GMA | RAFT + global motion aggregation | лучше RAFT на occlusion | тяжелее |

### 5.3 Global matching / Transformer

| Метод | Идея | Ориентир | Заметки |
|-------|------|----------|---------|
| GMFlow | global matching + transformer | сильный C+T generalization | быстрее тяжёлых iterative |
| FlowFormer (+MCVA) | cost-volume transformer | лидер Sintel/KITTI среди published (на момент статей) | много параметров; плох как student для RK3588 |

### 5.4 Лёгкие / mobile-ориентированные (кандидаты в student)

| Метод | Идея | Заметки |
|-------|------|---------|
| LiteFlowNet / LiteFlowNet2/3 | compact pyramid | исторический light baseline |
| FastFlowNet | ускоренный lightweight | ориентир под embedded |
| Кастомный student (цель работы) | distillation Basalt SE2 + GT | целевой деплой RKNN INT8 |

## 6. Сводная таблица

**T2 (этот ПК):** Windows, RTX 4080, CUDA 12.4; `python -m src.compare --config configs/default.yaml`; MPI Sintel training/clean — **первая пара** (не полный leaderboard); resize GT nearest; 500 общих Shi-Tomasi keypoints; latency = mean 50 frames после warmup 5. RAFT: `raft-sintel.pth`, iters=20.

Цифры ниже: **640×480** (в скобках — 1280×720). Полный CSV: `results/comparison.csv` (локально).

| Метод | Выход | Движение | GT для инференса | Dense EPE* | Sparse EPE* | Latency* ms | #params | Роль |
|-------|-------|----------|------------------|------------|-------------|-------------|---------|------|
| OpenCV LK | sparse | transl. | нет | — | **0.37** (0.48) | **1.4** (2.4) | — | baseline |
| Farneback | dense | dense | нет | **0.59** (1.44) | **0.32** (0.46)† | **36.8** (115) | — | baseline |
| DIS (opt.) | dense | dense | нет | TBD | TBD† | TBD | — | baseline |
| Basalt SE2 | sparse_se2 | SE(2) | нет | — | TBD | TBD (медл.) | — | **teacher** |
| FlowNet2 | dense | dense | нет | lit. | TBD† | TBD | ~160M | hist. |
| PWC-Net | dense | dense | нет | lit. | TBD† | TBD | ~9M | hist. |
| RAFT | dense | dense | нет | **0.14** (0.13) | **0.12** (0.14)† | **60.7** (136) | ~5M | NN baseline |
| SEA-RAFT | dense | dense | нет | lit. | TBD† | TBD | ~ | speed NN |
| GMFlow | dense | dense | нет | lit. | TBD† | TBD | ~ | matching |
| FlowFormer | dense | dense | нет | lit. | TBD† | TBD | ~ | SOTA acc. |
| Lite/FastFlowNet | dense | dense | нет | lit. | TBD† | TBD | ~1–5M | student cand. |
| **Our student** | TBD | TBD | нет | TBD | TBD | **≥20 FPS RK3588** | TBD | **вклад** |

\* Свои прогоны T2 vs lit. (литература) — не смешивать в одной ячейке статьи без пометки.  
† Sparse из dense = семплирование в общих keypoints.

## 7. Выводы для дизайна student-сети

1. **Не сравнивать** Basalt SE2 только по dense Sintel EPE — у teacher другой выход; нужен sparse protocol.
2. Pareto для RK3588: смотреть Lite/Fast/SEA-RAFT-подобные архитектуры, не FlowFormer.
3. Distillation: Basalt даёт сильный **sparse SE(2) prior** на реальных VIO-последовательностях без dense GT.
4. Итоговая таблица статьи = этот шаблон + latency на GPU (T2 частично заполнен) и RK3588 (T5).

## 8. Ключевые ссылки

- Basalt: Usenko et al.; репозиторий https://gitlab.com/VladyslavUsenko/basalt  
- Lucas–Kanade unifying framework (Baker & Matthews)  
- RAFT (Teed & Deng, ECCV 2020); SEA-RAFT (ECCV 2024)  
- GMFlow; FlowFormer / FlowFormer++  
- PWC-Net; LiteFlowNet; FastFlowNet  
- Feng et al. — Integration of Deep Optical Flow in VIO (Basalt)  
- LET-SE2-VINS (Sensors 2025) — hybrid SE2 + lightweight CNN  
