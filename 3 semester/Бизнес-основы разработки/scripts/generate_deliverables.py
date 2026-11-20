# -*- coding: utf-8 -*-
"""Generate BOR course deliverables: HW1, HW2 and the final pitch deck (PDF)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import Paragraph as _Paragraph
from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle

NBSP = "\u00a0"


def nb(text: str) -> str:
    """Keep '3 000 ₽' and '15 мин' style groups on one line."""
    text = re.sub(r"(?<=\d) (?=\d{3}\b)", NBSP, text)
    return re.sub(r"(?<=\d) (?=₽|%|млн|млрд|тыс\.|мин|мес\.)", NBSP, text)


class Paragraph(_Paragraph):
    def __init__(self, text, *args, **kwargs):
        super().__init__(nb(str(text)), *args, **kwargs)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "работы"
ASSETS = Path(__file__).resolve().parent / "assets"

pdfmetrics.registerFont(TTFont("ArialRU", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("ArialRUB", r"C:\Windows\Fonts\arialbd.ttf"))
pdfmetrics.registerFont(TTFont("ArialRUI", r"C:\Windows\Fonts\ariali.ttf"))
pdfmetrics.registerFont(TTFont("ArialRUBI", r"C:\Windows\Fonts\arialbi.ttf"))
pdfmetrics.registerFontFamily("ArialRU", normal="ArialRU", bold="ArialRUB", italic="ArialRUI", boldItalic="ArialRUBI")
pdfmetrics.registerFontFamily("ArialRUB", normal="ArialRUB", bold="ArialRUB", italic="ArialRUBI", boldItalic="ArialRUBI")

NAVY = colors.HexColor("#102a43")
GREEN = colors.HexColor("#27a844")
LIGHT = colors.HexColor("#eef3f8")
GRID = colors.HexColor("#9fb3c8")
GRAY = colors.HexColor("#52606d")
RED = colors.HexColor("#c0392b")
ORANGE = colors.HexColor("#e67e22")

AUTHOR = "Царюк Артём Владимирович"
GROUP = "102 221"
AI_NOTE = (
    "Использование ИИ: помощь в вёрстке PDF и редактуре текста. Данные, допущения, расчёты и выводы — "
    "из собственных материалов проекта FuncFund (CustDev n=14, финмодель, метрики MVP) и проверены автором."
)


def style(name, font="ArialRU", size=10, leading=None, align=TA_LEFT, color=colors.black, **kw):
    return ParagraphStyle(
        name,
        fontName=font,
        fontSize=size,
        leading=leading or size * 1.35,
        alignment=align,
        textColor=color,
        **kw,
    )


S = {
    "h1": style("h1", "ArialRUB", 16, 20, spaceAfter=6),
    "h2": style("h2", "ArialRUB", 12, 15, spaceBefore=8, spaceAfter=4, color=NAVY),
    "body": style("body", size=10, leading=13.5, align=TA_JUSTIFY, spaceAfter=5),
    "meta": style("meta", size=9, color=GRAY, spaceAfter=4),
    "small": style("small", size=8, leading=10.5, color=GRAY),
    "cell": style("cell", size=8.3, leading=10.5),
    "cellb": style("cellb", "ArialRUB", 8.3, 10.5),
    "s_body": style("s_body", size=13, leading=17.5),
    "s_small": style("s_small", size=10.5, leading=14, color=GRAY),
    "s_big": style("s_big", "ArialRUB", 19, 25, color=NAVY),
    "s_center": style("s_center", "ArialRUB", 15, 20, align=TA_CENTER, color=NAVY),
    "card_t": style("card_t", "ArialRUB", 11, 14, color=NAVY),
    "card_b": style("card_b", size=10.5, leading=13.5),
}


# --------------------------------------------------------------------------- numbers


@dataclass(frozen=True)
class Unit:
    aov: float = 3000.0  # ₽/год, годовой эквивалент оплаты 1 платящего
    acquiring: float = 0.035
    infra_per_payer: float = 120.0  # ₽/год
    churn: float = 0.20  # в год
    cac: float = 900.0
    pilot_fixed_month: float = 1500.0
    year1_fixed_month: float = (6_240_000 + 600_000 + 18_000) / 12  # ФОТ 2 FTE + прочие + инфра (B14)

    @property
    def var_cost(self):
        return self.aov * self.acquiring + self.infra_per_payer

    @property
    def margin(self):
        return (self.aov - self.var_cost) / self.aov

    @property
    def contribution(self):
        return self.aov * self.margin

    @property
    def lt(self):
        return 1 / self.churn

    @property
    def ltv(self):
        return self.aov * self.margin * self.lt

    @property
    def ltv_cac(self):
        return self.ltv / self.cac

    @property
    def payback_months(self):
        return self.cac / self.contribution * 12

    def bep(self, fixed_month):
        per_client = self.contribution - self.cac
        return fixed_month / per_client if per_client > 0 else float("inf")


U = Unit()


def rub(x: float) -> str:
    return f"{x:,.0f}".replace(",", " ") + " ₽"


def num(x: float, d=0) -> str:
    return f"{x:,.{d}f}".replace(",", " ").replace(".", ",")


# --------------------------------------------------------------------------- shared helpers


def tbl(data, widths, header_bg=colors.HexColor("#d9e2ec"), font_size=None):
    cell = S["cell"] if font_size is None else style("c2", size=font_size, leading=font_size * 1.3)
    cellb = S["cellb"] if font_size is None else style("c2b", "ArialRUB", font_size, font_size * 1.3)
    rows = []
    for i, row in enumerate(data):
        rows.append(
            [c if isinstance(c, Paragraph) else Paragraph(str(c).replace("\n", "<br/>"), cellb if i == 0 else cell) for c in row]
        )
    t = Table(rows, colWidths=widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), header_bg),
                ("GRID", (0, 0), (-1, -1), 0.4, GRID),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fafc")]),
            ]
        )
    )
    return t


class Deck:
    """Landscape slide canvas with a common header/footer."""

    def __init__(self, path: Path, title: str, footer: str):
        self.W, self.H = landscape(A4)
        self.c = rl_canvas.Canvas(str(path), pagesize=(self.W, self.H))
        self.c.setTitle(title)
        self.c.setAuthor(AUTHOR)
        self.footer = footer
        self.n = 0
        self.M = 1.4 * cm

    def slide(self, title: str | None):
        if self.n:
            self.c.showPage()
        self.n += 1
        c = self.c
        if title:
            c.setFillColor(NAVY)
            c.rect(0, self.H - 58, self.W, 58, stroke=0, fill=1)
            c.setFillColor(colors.white)
            c.setFont("ArialRUB", 21)
            c.drawString(self.M, self.H - 38, title)
        c.setFillColor(GRAY)
        c.setFont("ArialRU", 8)
        c.drawString(self.M, 16, self.footer)
        c.drawRightString(self.W - self.M, 16, str(self.n))

    @property
    def top(self):
        return self.H - 58 - 18

    def par(self, text, x, ytop, w, st):
        p = Paragraph(text, st)
        _, h = p.wrap(w, 2000)
        p.drawOn(self.c, x, ytop - h)
        return h

    def card(self, x, ytop, w, h, title, body, accent=GREEN, title_style=None, body_style=None):
        c = self.c
        c.setFillColor(LIGHT)
        c.roundRect(x, ytop - h, w, h, 6, stroke=0, fill=1)
        c.setFillColor(accent)
        c.rect(x, ytop - h, 4, h, stroke=0, fill=1)
        th = self.par(title, x + 12, ytop - 9, w - 20, title_style or S["card_t"])
        if body:
            self.par(body, x + 12, ytop - 13 - th, w - 20, body_style or S["card_b"])

    def kpi(self, x, ytop, w, h, value, label, color=NAVY):
        c = self.c
        c.setFillColor(LIGHT)
        c.roundRect(x, ytop - h, w, h, 6, stroke=0, fill=1)
        c.setFillColor(color)
        c.setFont("ArialRUB", 22)
        c.drawCentredString(x + w / 2, ytop - h / 2 + 2, value)
        c.setFillColor(GRAY)
        c.setFont("ArialRU", 9.5)
        c.drawCentredString(x + w / 2, ytop - h + 12, label)

    def image(self, path: Path, x, y, w, h):
        self.c.drawImage(ImageReader(str(path)), x, y, width=w, height=h, preserveAspectRatio=True, anchor="c", mask="auto")

    def table(self, t: Table, x, ytop, w):
        _, h = t.wrapOn(self.c, w, 2000)
        t.drawOn(self.c, x, ytop - h)
        return h

    def arrow(self, x1, y, x2, color=GRAY):
        c = self.c
        c.setStrokeColor(color)
        c.setFillColor(color)
        c.setLineWidth(2)
        c.line(x1, y, x2 - 6, y)
        p = c.beginPath()
        p.moveTo(x2, y)
        p.lineTo(x2 - 8, y + 4)
        p.lineTo(x2 - 8, y - 4)
        p.close()
        c.drawPath(p, stroke=0, fill=1)

    def save(self):
        self.c.save()


def bar_chart(d: Deck, x, y, w, h, series, labels, colors_, y_max, y_step, unit, legend):
    """Grouped vertical bars. series: list of lists (one list per series)."""
    c = d.c
    c.setStrokeColor(GRID)
    c.setLineWidth(0.5)
    c.setFont("ArialRU", 8)
    c.setFillColor(GRAY)
    v = 0
    while v <= y_max + 1e-9:
        yy = y + h * v / y_max
        c.line(x, yy, x + w, yy)
        c.drawRightString(x - 4, yy - 3, f"{num(v)}")
        v += y_step
    c.drawString(x - 4 - 20, y + h + 8, unit)
    groups = len(labels)
    k = len(series)
    gw = w / groups
    bw = gw * 0.7 / k
    for gi, lab in enumerate(labels):
        gx = x + gi * gw + gw * 0.15
        for si in range(k):
            val = series[si][gi]
            bh = h * val / y_max
            c.setFillColor(colors_[si])
            c.rect(gx + si * bw, y, bw - 2, bh, stroke=0, fill=1)
            c.setFillColor(colors.black)
            c.setFont("ArialRUB", 8.5)
            c.drawCentredString(gx + si * bw + bw / 2 - 1, y + bh + 3, num(val, 0 if float(val).is_integer() else 1))
        c.setFillColor(colors.black)
        c.setFont("ArialRU", 9.5)
        c.drawCentredString(x + gi * gw + gw / 2, y - 13, lab)
    lx = x
    for si, name in enumerate(legend):
        c.setFillColor(colors_[si])
        c.rect(lx, y - 32, 9, 9, stroke=0, fill=1)
        c.setFillColor(colors.black)
        c.setFont("ArialRU", 9)
        c.drawString(lx + 13, y - 31, name)
        lx += c.stringWidth(name, "ArialRU", 9) + 35


# --------------------------------------------------------------------------- HW1


def build_hw1(path: Path):
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=1.7 * cm,
        rightMargin=1.7 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.4 * cm,
        title="ДЗ 1. Система метрик продукта FuncFund",
        author=AUTHOR,
    )
    b, h2 = S["body"], S["h2"]
    st = [
        Paragraph("ДЗ 1. Создание системы метрик для продукта", S["h1"]),
        Paragraph(
            f"Бизнес-основы разработки · {AUTHOR} · группа {GROUP} · продукт-кейс: FuncFund (funcfund.ru)",
            S["meta"],
        ),
        Spacer(1, 3 * mm),
        Paragraph("Часть 1. Контекст и выбор продукта", h2),
        tbl(
            [
                ["Параметр", "FuncFund"],
                ["Название", "FuncFund — веб/мобильный сервис учёта личного инвестиционного портфеля."],
                [
                    "Value Proposition",
                    "Все брокерские счета и внешние активы в одном окне: импорт отчётов/API (Сбер, Т-Инвестиции, "
                    "ВТБ, Альфа) + ручной ввод → live-структура и история портфеля за минуты вместо ручной сверки "
                    "в Excel. Без инвестрекомендаций и сигналов buy/sell.",
                ],
                [
                    "Бизнес-модель",
                    "B2C SaaS, freemium → подписка. Бесплатно: 1 источник + ручной ввод. Premium (2+ брокера, "
                    "история, live) — 349 ₽/мес или 2 990 ₽/год, оплата через ЮKassa.",
                ],
                [
                    "Целевая аудитория",
                    "DIY-инвесторы MOEX с 2+ счетами (брокер + второй брокер/банк), которые сами ведут учёт "
                    "в таблицах. В CustDev (n=14) боль мультисчетов назвали все 14 респондентов.",
                ],
            ],
            [3.6 * cm, 14 * cm],
        ),
        Paragraph("Часть 2. Цели и ключевые метрики (AARRR)", h2),
        tbl(
            [
                ["Этап (AARRR)", "Бизнес-цель на этапе", "Ключевая метрика (1–2)", "Почему эта метрика? Как измерять"],
                [
                    "Acquisition (Привлечение)",
                    "Дешёвый приток целевых инвесторов из органических каналов",
                    "1) Регистрации в неделю по каналам (UTM)\n2) Доля регистраций с 2+ счетами (по анкете)",
                    "Регистрация — первое контролируемое действие; разрез по каналам показывает, где ниже CAC. "
                    "Доля «2+ счёта» отсекает нецелевой трафик. События signup + UTM в аналитике.",
                ],
                [
                    "Activation (Активация)",
                    "Пользователь за первую сессию видит весь портфель",
                    "1) Доля регистраций, дошедших до дашборда с данными (Aha)\n2) Медиана time-to-value, мин",
                    "Сам по себе вход ничего не значит — ценность появляется на дашборде с данными. Событие "
                    "first_portfolio_rendered; цель — медиана не больше 15 мин.",
                ],
                [
                    "Retention (Удержание)",
                    "Сверка портфеля становится привычкой (раз в неделю)",
                    "1) Retention D7 / D30 по недельным когортам активации",
                    "Учёт нужен регулярно: если пользователь не вернулся к сверке, платить он не станет. "
                    "Считаем по когортам, чтобы не путать с сезонностью.",
                ],
                [
                    "Revenue (Доход)",
                    "Перевод активных пользователей на Premium",
                    "1) Конверсия активированных в оплату за 30 дней\n2) MRR / ARPU",
                    "Платный триггер — подключение 2-го брокера; метрика показывает, ценна ли агрегация. "
                    "Данные ЮKassa + событие paywall_shown.",
                ],
                [
                    "Referral (Поделиться)",
                    "Рост через инвесторские сообщества, снижение CAC",
                    "1) Доля активных, пригласивших ≥1 пользователя\n2) K-фактор",
                    "Инвесторы обсуждают инструменты в чатах — реферал дешевле рекламы. Реферальная ссылка, "
                    "атрибуция регистрации к пригласившему.",
                ],
            ],
            [2.5 * cm, 3.6 * cm, 4.4 * cm, 7.1 * cm],
        ),
        Spacer(1, 2 * mm),
        Paragraph(
            "<b>Текущий baseline (MVP, ноябрь 2026, дашборд метрик):</b> 9 пользователей, 7 активных аккаунтов, "
            "WAU 6, 5 пользователей с заполненным портфелем, 1 платящий (MRR 349 ₽). Выборка пока мала для "
            "статистических выводов — таблица задаёт систему, которую будем мерить на пилоте.",
            b,
        ),
        Paragraph(
            "<b>Количественные и качественные показатели.</b> Метрики AARRR — количественные: показывают, "
            "<i>что</i> происходит. Чтобы понять <i>почему</i>, к ним добавляем качественные: оценку «закрывает ли "
            "продукт боль сверки» по шкале 1–10 в протоколах бета-теста (цель: ≥7 у 60% участников), причины "
            "отказа из интервью с ушедшими и NPS после 30 дней. <b>Vanity metrics</b>, которые не используем для "
            "решений: общее число регистраций без активации, просмотры лендинга, «суммарные активы под учётом» "
            "(растут вместе с рынком, а не с продуктом).",
            b,
        ),
        Paragraph(
            "<b>Активация и Aha-момент.</b> Пользователь «активировался», когда в первой сессии увидел на одном "
            "экране свой портфель с реальными данными хотя бы одного брокера (импорт или ручной ввод). Aha-момент — "
            "«вот все мои деньги, и мне больше не нужно сводить таблицу»: структура по классам активов и счетам "
            "с текущей стоимостью. Поэтому граница активации — событие first_portfolio_rendered, а не регистрация.",
            b,
        ),
        Paragraph(
            "<b>North Star Metric — число портфелей, сверенных за неделю (Weekly Reconciled Portfolios, WRP):</b> "
            "пользователи, которые за неделю открыли дашборд с актуальными данными из 2+ источников (два брокера "
            "или брокер + ручные активы). Почему она: (1) отражает ядро ценности — единое окно по нескольким "
            "счетам; (2) объединяет активацию и привычку возврата; (3) напрямую связана с выручкой — второй брокер "
            "доступен только в Premium, значит рост WRP тянет конверсию в оплату. Сейчас proxy WRP ≈ 5.",
            b,
        ),
        Paragraph(
            "<b>Связь с бизнес-моделью.</b> Выручка = платящие × ARPU. Платящих создаёт цепочка Acquisition → "
            "Activation → Retention → Revenue: подписку покупают только те, кто регулярно сверяет портфель из "
            "нескольких источников. Retention определяет LT и LTV, Referral снижает CAC — то есть каждая метрика "
            "воронки прямо влияет на юнит-экономику (ДЗ 2).",
            b,
        ),
        Paragraph("Часть 3. Анализ данных и гипотезы — сценарий А", h2),
        Paragraph(
            "<b>Наблюдение:</b> Retention D7 за последний месяц упал на 15% (например, с 40% до 34% у недельных "
            "когорт). Первый шаг — проверить, что это сигнал, а не шум: на текущей базе в 9 пользователей "
            "15% — это один человек, поэтому сценарий разбираем для когорт от ~200 активаций в неделю.",
            b,
        ),
        Paragraph("<b>1. Возможные причины</b>", b),
        tbl(
            [
                ["#", "Тип", "Причина", "Что увидим в данных"],
                [
                    "1",
                    "Внутренняя: техника",
                    "Сломался или замедлился импорт (брокер поменял формат отчёта, истёк токен API Т-Инвестиций) — "
                    "у вернувшихся устаревшие данные",
                    "Рост ошибок импорта, падение D7 у пользователей конкретного брокера",
                ],
                [
                    "2",
                    "Внутренняя: продукт",
                    "Новый релиз усложнил путь к повторной сверке (лишний шаг в онбординге, paywall раньше Aha)",
                    "Падение совпадает с датой релиза, сильнее у новых когорт",
                ],
                [
                    "3",
                    "Внешняя: сезонность / рынок",
                    "Праздники или спокойный рынок — меньше поводов смотреть портфель",
                    "Такое же падение в аналогичный период прошлых данных и у всех каналов",
                ],
                [
                    "4",
                    "Внешняя: качество трафика",
                    "Новый канал привёл нецелевых пользователей (1 счёт, ждали «сигналы»)",
                    "Падение только в когортах нового канала, низкая доля «2+ счёта»",
                ],
            ],
            [0.6 * cm, 3.0 * cm, 7.6 * cm, 6.4 * cm],
        ),
        Spacer(1, 2 * mm),
        Paragraph("<b>2. Гипотезы (по шаблону задания)</b>", b),
        Paragraph(
            "<b>H1.</b> Мы считаем, что падение удержания связано с ошибками импорта отчётов Сбера после смены "
            "формата брокером. Если мы починим парсер и добавим уведомление «данные устарели — обновите отчёт», "
            "то Retention D7 у пользователей Сбера вырастет на 15% (с 34% до ~39%, почти к уровню до падения) "
            "за 2 недели после релиза.",
            b,
        ),
        Paragraph(
            "<b>H2.</b> Мы считаем, что падение удержания связано с тем, что после последнего релиза новые "
            "пользователи упираются в paywall до того, как добавили второй источник и увидели ценность. Если мы "
            "перенесём paywall после первого полного дашборда и дадим 7 дней Premium-триала, то Retention D7 "
            "новых когорт вырастет на 20% (с 34% до ~41%), а конверсия в оплату за 30 дней не упадёт.",
            b,
        ),
        Paragraph("<b>3. Шаги проверки</b>", b),
        Paragraph(
            "1) <b>Диагностика до экспериментов:</b> D7 в разрезе когорт по неделям, брокерам, каналам и версиям "
            "приложения; сравнение с аналогичным периодом (сезонность); лог ошибок импорта и обращений в поддержку. "
            "Это быстро отсекает причины 3 и 4.<br/>"
            "2) <b>H1 — до/после фикса:</b> выкатываем исправленный парсер, сравниваем D7 когорт Сбера до и после "
            "с контрольной группой пользователей других брокеров (difference-in-differences).<br/>"
            "3) <b>H2 — A/B-тест:</b> 50/50 новых активаций, контроль — текущий paywall, тест — paywall после "
            "дашборда + триал. Чтобы заметить рост D7 с 34% до 41% (α = 5%, мощность 80%), нужно ~800 "
            "пользователей в группе — при 200 активациях в неделю это ~8 недель. Эффект меньше (+8%) потребовал "
            "бы ~5 000 на группу, поэтому мелкие правки на нашем трафике проверяем не A/B, а интервью. "
            "Основная метрика — D7, контрольные — конверсия в оплату за 30 дней и WRP.<br/>"
            "4) <b>Качественная проверка:</b> 5–7 коротких интервью с пользователями, которые не вернулись "
            "(«что вы делали, когда последний раз проверяли портфель?») — подтверждаем или опровергаем причину.",
            b,
        ),
        Spacer(1, 3 * mm),
        Paragraph(AI_NOTE, S["small"]),
    ]
    doc.build(st)


# --------------------------------------------------------------------------- HW2


def bep_chart(d: Deck, x, y, w, h):
    """Monthly operating result vs. new paying clients per month (LMS break-even formula)."""
    c = d.c
    fixed = U.year1_fixed_month
    lines = [
        ("CAC 900 ₽ (база)", U.contribution - U.cac, GREEN),
        ("CAC 1 800 ₽ (стресс)", U.contribution - 1800, ORANGE),
    ]
    n_max, y_min, y_max = 700, -600, 800  # тыс. ₽
    sx = lambda n: x + w * n / n_max
    sy = lambda v: y + h * (v - y_min) / (y_max - y_min)
    c.setFont("ArialRU", 8)
    c.setStrokeColor(GRID)
    c.setLineWidth(0.5)
    for v in range(y_min, y_max + 1, 200):
        c.line(x, sy(v), x + w, sy(v))
        c.setFillColor(GRAY)
        c.drawRightString(x - 4, sy(v) - 3, num(v))
    for n in range(0, n_max + 1, 100):
        c.line(sx(n), y, sx(n), y + h)
        c.drawCentredString(sx(n), y - 12, str(n))
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(x, sy(0), x + w, sy(0))
    c.setFillColor(GRAY)
    c.setFont("ArialRU", 9)
    c.drawCentredString(x + w / 2, y - 26, "новых платящих клиентов в месяц")
    c.drawString(x - 4 - 20, y + h + 8, "тыс. ₽ / мес: вклад новых клиентов − постоянные расходы")
    for label, per, col in lines:
        c.setStrokeColor(col)
        c.setLineWidth(2.2)
        c.line(sx(0), sy(-fixed / 1000), sx(n_max), sy((per * n_max - fixed) / 1000))
        bep = fixed / per
        c.setFillColor(col)
        c.circle(sx(bep), sy(0), 4, stroke=0, fill=1)
        c.setFont("ArialRUB", 9)
        c.drawString(sx(bep) + 6, sy(0) + 6 if col == GREEN else sy(0) - 14, f"BEP ≈ {bep:.0f}")
    lx = x + 8
    for label, _, col in lines:
        c.setFillColor(col)
        c.rect(lx, y + h - 14, 9, 9, stroke=0, fill=1)
        c.setFillColor(colors.black)
        c.setFont("ArialRU", 9)
        c.drawString(lx + 13, y + h - 13, label)
        lx += c.stringWidth(label, "ArialRU", 9) + 34


def build_hw2(path: Path):
    d = Deck(path, "ДЗ 2. Юнит-экономика FuncFund", f"ДЗ 2 · Юнит-экономика FuncFund · {AUTHOR} · группа {GROUP}")
    M, W = d.M, d.W - 2 * d.M
    bep_pilot = U.bep(U.pilot_fixed_month)
    bep_y1 = U.bep(U.year1_fixed_month)
    bep_y1_stress = Unit(cac=1800).bep(U.year1_fixed_month)

    # ---- page 1: unit + assumptions
    d.slide("ДЗ 2. Расчёт юнит-экономики · исходные данные")
    y = d.top
    y -= d.par(
        "<b>Часть 1. Юнит = 1 платящий клиент (подписка Premium).</b> FuncFund — B2C SaaS: выручку приносит "
        "подписчик, а не разовая продажа или активный пользователь, поэтому по методике задания юнит — "
        "1 платящий клиент. Расчёт ведём в годовом выражении: «транзакция» = годовой эквивалент оплаты, LT — в годах.",
        M, y, W, S["s_body"],
    ) + 10
    rows = [
        ["Допущение", "Значение", "Обоснование"],
        [
            "AOV — средний чек (годовой эквивалент)",
            rub(U.aov),
            "Прайс: 2 990 ₽/год или 349 ₽/мес. Ожидаемая смесь 70% годовых / 30% месячных даёт ≈3 350 ₽; "
            "берём консервативно 3 000 ₽ (промокоды, месячные платят не весь год).",
        ],
        [
            "Переменные затраты на юнит",
            rub(U.var_cost) + " / год",
            f"Эквайринг ЮKassa 3,5% = {rub(U.aov * U.acquiring)} + доля инфраструктуры (VPS, ClickHouse, котировки) "
            f"≈{rub(U.infra_per_payer)} на платящего в год.",
        ],
        [
            "Отток (churn)",
            "20% в год → LT = 5 лет",
            "Портфельный учёт «липкий»: история и настройки копятся в сервисе, у 70% годовая оплата. Данных "
            "когорт ещё нет — поэтому ниже стресс-тест на 40% и 60%.",
        ],
        [
            "CAC — цель волны 1",
            rub(U.cac),
            "Бюджет месяца: посевы в Telegram-каналах для инвесторов 8 000 ₽ + контент (VC.ru, Shorts) 4 000 ₽ + "
            "12 ч времени основателя × 500 ₽ = 18 000 ₽ на 20 новых платящих.",
        ],
        [
            "Постоянные расходы — пилот",
            rub(U.pilot_fixed_month) + " / мес",
            "Фактический кеш: VPS, домен, ClickHouse. Время основателя не оплачивается (соло-проект).",
        ],
        [
            "Постоянные расходы — год 1 (команда)",
            rub(U.year1_fixed_month) + " / мес",
            "Финмодель года 1: ФОТ 2 FTE с взносами 6,24 млн + сервисы/юрист/бухгалтерия 0,6 млн + "
            "базовая инфраструктура 18 тыс. ₽ в год.",
        ],
    ]
    d.table(tbl(rows, [5.3 * cm, 3.6 * cm, W - 8.9 * cm], font_size=9.5), M, y, W)

    # ---- page 2: full calculation table
    d.slide("Таблица расчётов (части 2–5)")
    y = d.top
    calc = [
        ["Часть", "Показатель", "Формула", "Расчёт", "Результат"],
        ["2", "AOV", "средняя оплата за период", "см. допущения", rub(U.aov)],
        ["2", "Margin", "(AOV − переменные) / AOV", f"({num(U.aov)} − {num(U.var_cost)}) / {num(U.aov)}", f"{num(U.margin * 100, 1)}%"],
        ["2", "LT", "1 / churn", "1 / 0,20", "5 лет"],
        ["2", "LTV", "AOV × Margin × LT", f"{num(U.aov)} × {num(U.margin, 3)} × 5", rub(U.ltv)],
        ["3", "CAC", "маркетинг / новые платящие", "18 000 / 20", rub(U.cac)],
        ["4", "LTV / CAC", "LTV / CAC", f"{num(U.ltv)} / {num(U.cac)}", f"{num(U.ltv_cac, 1)}× (норма ≥ 3×)"],
        [
            "4",
            "CAC Payback",
            "CAC / (AOV × Margin)",
            f"{num(U.cac)} / {num(U.contribution)} = {num(U.cac / U.contribution, 2)} года",
            f"{num(U.payback_months, 1)} мес.",
        ],
        [
            "5",
            "Break-even, пилот",
            "Fixed / (AOV × Margin − CAC)",
            f"{num(U.pilot_fixed_month)} / ({num(U.contribution)} − {num(U.cac)})",
            f"{num(bep_pilot, 1)} → 1 новый платящий/мес",
        ],
        [
            "5",
            "Break-even, год 1",
            "Fixed / (AOV × Margin − CAC)",
            f"{num(U.year1_fixed_month)} / {num(U.contribution - U.cac)}",
            f"≈{bep_y1:.0f} новых платящих/мес",
        ],
    ]
    h = d.table(tbl(calc, [1.7 * cm, 3.6 * cm, 5.4 * cm, 7.4 * cm, W - 18.1 * cm], font_size=10), M, y, W)
    y -= h + 14
    d.par(
        "Проверка для месячного тарифа: маржа 349 ₽ после эквайринга и инфраструктуры ≈ 327 ₽/мес, "
        "payback = 900 / 327 ≈ 2,8 мес. — вывод тот же. "
        "В финмодели ВКРС LTV считался как ARPU / churn = 15 000 ₽ без учёта маржи; здесь по формуле задания "
        f"с маржой — {rub(U.ltv)}.",
        M, y, W, S["s_small"],
    )

    # ---- slide 1
    d.slide("Слайд 1. Проект и юнит")
    y = d.top
    col = (W - 20) / 2
    d.card(
        M, y, col, 130, "Проект",
        "FuncFund — сервис учёта личного инвестиционного портфеля: все брокерские счета и внешние активы "
        "в одном окне, без инвестрекомендаций.<br/><br/>Модель: freemium → Premium 349 ₽/мес или 2 990 ₽/год.<br/>"
        "ЦА: DIY-инвесторы MOEX с 2+ счетами.",
    )
    d.card(
        M + col + 20, y, col, 130, "Юнит = 1 платящий клиент",
        "Подписочный SaaS: деньги приносит подписчик, а не транзакция или DAU.<br/><br/>"
        f"AOV {rub(U.aov)}/год · переменные {rub(U.var_cost)} · маржа {num(U.margin * 100, 1)}%.<br/>"
        "Текущий факт MVP: 9 пользователей, 1 платящий (MRR 349 ₽).",
    )
    d.par("Дашборд метрик MVP FuncFund, ноябрь 2026:", M, y - 155, W, S["s_small"])
    d.image(ASSETS / "metrics.png", M, y - 300, W, 130)
    d.par(
        "Выборка пока мала, поэтому CAC и отток в расчётах — целевые допущения, а устойчивость проверена "
        "стресс-тестом (слайд 2).",
        M, y - 320, W, S["s_body"],
    )

    # ---- slide 2
    d.slide("Слайд 2. Ключевые метрики")
    y = d.top
    kw = (W - 3 * 14) / 4
    for i, (v, lab, colr) in enumerate(
        [
            (rub(U.ltv), "LTV = AOV × Margin × LT", NAVY),
            (rub(U.cac), "CAC (цель волны 1)", NAVY),
            (f"{num(U.ltv_cac, 1)}×", "LTV / CAC (норма ≥ 3×)", GREEN),
            (f"{num(U.payback_months, 1)} мес.", "CAC Payback", GREEN),
        ]
    ):
        d.kpi(M + i * (kw + 14), y, kw, 80, v, lab, colr)
    y -= 100
    d.par(
        "Правило LTV > CAC выполняется с большим запасом: один клиент за жизнь приносит в 15 раз больше маржи, "
        "чем стоит его привлечение, а затраты на привлечение возвращаются за первые 4 месяца подписки. "
        "Значит, рост можно финансировать из выручки, а не из инвестиций — при условии, что CAC и отток подтвердятся.",
        M, y, W, S["s_body"],
    )
    sens = [
        ["Сценарий", "Churn / год", "CAC", "LTV", "LTV / CAC", "Вывод"],
        ["База", "20%", "900 ₽", rub(U.ltv), f"{num(U.ltv_cac, 1)}×", "здоровый"],
    ]
    for name, ch, cac in [("Отток ×2", 0.4, 900), ("Отток ×3", 0.6, 900), ("CAC ×2", 0.2, 1800), ("Отток ×2 и CAC ×2", 0.4, 1800), ("Отток ×3 и CAC ×2", 0.6, 1800)]:
        u = Unit(churn=ch, cac=cac)
        verdict = "здоровый" if u.ltv_cac >= 3 else "ниже нормы 3×"
        sens.append([name, f"{ch * 100:.0f}%", rub(cac), rub(u.ltv), f"{num(u.ltv_cac, 1)}×", verdict])
    d.table(tbl(sens, [5 * cm, 2.6 * cm, 2.6 * cm, 3 * cm, 2.8 * cm, W - 16 * cm], font_size=10), M, y - 70, W)

    # ---- slide 3
    d.slide("Слайд 3. Точка безубыточности")
    y = d.top
    d.par(
        f"Формула задания: Fixed / (AOV × Margin − CAC). С первого года каждый новый клиент даёт "
        f"{rub(U.contribution)} − {rub(U.cac)} = <b>{rub(U.contribution - U.cac)}</b>.",
        M, y, W, S["s_body"],
    )
    bep_chart(d, M + 40, 95, W * 0.62, d.top - 160)
    rx = M + 40 + W * 0.62 + 30
    rw = d.W - M - rx
    d.card(
        rx, d.top - 40, rw, 120, "Пилот (соло)",
        f"Fixed {rub(U.pilot_fixed_month)}/мес → <b>≈1 новый платящий в месяц</b>. Уже достижимо: первый платящий есть.",
    )
    d.card(
        rx, d.top - 175, rw, 150, "Год 1 (команда 2 FTE)",
        f"Fixed {rub(U.year1_fixed_month)}/мес → <b>≈{bep_y1:.0f} новых платящих/мес</b> "
        f"(при CAC 1 800 ₽ — ≈{bep_y1_stress:.0f}). Это ×300 к текущему темпу.",
        accent=ORANGE,
    )

    # ---- slide 4
    d.slide("Слайд 4. Выводы: устойчива ли модель")
    y = d.top
    col = (W - 2 * 16) / 3
    for i, (t, body, acc) in enumerate(
        [
            (
                "Юнит устойчив",
                f"LTV/CAC = {num(U.ltv_cac, 1)}×, payback {num(U.payback_months, 1)} мес. Даже при оттоке 60% в год "
                "соотношение 5,1× — выше нормы. Маржа 92,5%: переменные затраты почти нулевые.",
                GREEN,
            ),
            (
                "Слабое место — объём и CAC",
                f"Проблема не в марже, а в масштабе: для покрытия команды нужно ≈{bep_y1:.0f} новых платящих "
                "в месяц, сейчас — 1. CAC 900 ₽ пока цель, а не факт: органика не проверена на объёме.",
                ORANGE,
            ),
            (
                "Опасная комбинация",
                "Если отток 60% и CAC удвоится до 1 800 ₽, LTV/CAC падает до 2,6× — ниже нормы. "
                "Верхняя граница CAC, при которой клиент окупается за 1-й год, — 2 775 ₽.",
                RED,
            ),
        ]
    ):
        d.card(M + i * (col + 16), y, col, 120, t, body, accent=acc)
    scen = [("База", 0.2, 900), ("Отток ×2", 0.4, 900), ("Отток ×3", 0.6, 900), ("CAC ×2", 0.2, 1800),
            ("Отток×2+CAC×2", 0.4, 1800), ("Отток×3+CAC×2", 0.6, 1800)]
    vals = [round(Unit(churn=ch, cac=cac).ltv_cac, 1) for _, ch, cac in scen]
    cx, cy, cw, chh = M + 30, 95, W * 0.62, y - 270
    bar_chart(d, cx, cy, cw, chh, [vals], [s[0] for s in scen], [GREEN], 16, 4, "LTV / CAC, ×", ["LTV / CAC по сценариям"])
    norm_y = cy + chh * 3 / 16
    d.c.setStrokeColor(RED)
    d.c.setLineWidth(1.2)
    d.c.setDash(4, 3)
    d.c.line(cx, norm_y, cx + cw, norm_y)
    d.c.line(cx + 190, cy - 27, cx + 214, cy - 27)
    d.c.setDash()
    d.c.setFillColor(colors.black)
    d.c.setFont("ArialRU", 9)
    d.c.drawString(cx + 220, cy - 31, "норма LTV / CAC = 3×")
    d.card(
        cx + cw + 24, y - 150, d.W - M - (cx + cw + 24), 170, "Итог",
        "На уровне юнита бизнес устойчив; на уровне компании устойчивость зависит от скорости "
        "привлечения при CAC ≤ 900 ₽. Пилот безубыточен уже сейчас, команду можно нанимать только после "
        "подтверждения каналов.",
        accent=NAVY,
    )

    # ---- slide 5
    d.slide("Слайд 5. Рекомендации")
    y = d.top
    recs = [
        ("1. Подтвердить CAC на пилоте", "3 месяца органики (Telegram, контент, рефералы) с UTM; цель — 10–12 оплат и фактический CAC ≤ 900 ₽."),
        ("2. Снизить CAC через рефералы", "Месяц Premium за приглашённого инвестора с 2+ счетами: в чатах инвесторов сарафан дешевле посевов."),
        ("3. Удерживать, а не только привлекать", "Мерить отток по когортам с первого месяца; уведомление «данные устарели» и годовой тариф по умолчанию."),
        ("4. Найм за выручкой", f"Второго разработчика брать только при стабильном темпе ≈{bep_y1:.0f} новых платящих в месяц или под грант/акселератор."),
        ("5. Тестировать цену вверх", "ARPU 3 000 ₽/год (≈250 ₽/мес) ниже входного тарифа Snowball (от 299 ₽/мес): тариф Pro поднимет LTV без роста CAC."),
    ]
    rh = 62
    for i, (t, body) in enumerate(recs):
        d.card(M, y - i * (rh + 8), W, rh, t, body)
    d.save()


# --------------------------------------------------------------------------- final pitch


def build_final(path: Path):
    d = Deck(path, "FuncFund — питч-дек", "FuncFund · итоговое задание «Бизнес-основы разработки» · 2026")
    M, W, H = d.M, d.W - 2 * d.M, d.H
    c = d.c

    # 1 Title
    d.slide(None)
    c.setFillColor(NAVY)
    c.rect(0, 0, d.W * 0.6, H, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("ArialRUB", 46)
    c.drawString(M + 10, H - 190, "FuncFund")
    c.setFont("ArialRU", 18)
    c.drawString(M + 12, H - 228, "Все брокерские счета — в одном окне,")
    c.drawString(M + 12, H - 252, "без советов buy/sell")
    c.setFillColor(GREEN)
    c.rect(M + 12, H - 272, 80, 4, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("ArialRUB", 13)
    c.drawString(M + 12, 150, AUTHOR)
    c.setFont("ArialRU", 11.5)
    c.drawString(M + 12, 132, "основатель: продукт и разработка (соло-проект)")
    c.drawString(M + 12, 100, "funcfund.ru  ·  rtem903134@gmail.com")
    c.setFont("ArialRU", 9.5)
    c.drawString(M + 12, 60, f"Итоговое задание · Бизнес-основы разработки · группа {GROUP}")
    d.image(ASSETS / "dashboard.png", d.W * 0.6 + 20, 40, d.W * 0.4 - 40, H - 80)

    # 2 Problem
    d.slide("Problem — проблема")
    y = d.top
    y -= d.par(
        "Сегодня частный инвестор с несколькими брокерскими счетами сталкивается с тем, что его деньги разбросаны "
        "по приложениям Сбера, Т-Банка, ВТБ и Excel. Это приводит к ручной сверке каждый месяц и к тому, "
        "что он не видит реальную структуру и доходность своего портфеля.",
        M, y, W, S["s_big"],
    ) + 18
    fw = (W - 2 * 16) / 3
    for i, (v, lab, src) in enumerate(
        [
            ("35,1 млн", "частных инвесторов на Мосбирже, 10,2 млн совершали сделки в 2024", "Мосбиржа, Интерфакс"),
            ("14 из 14", "респондентов CustDev держат 2+ счёта и сводят их вручную", "CustDev FuncFund, n=14"),
            ("9,1 / 10", "важность автоагрегации — фактор выбора №1 среди 10 характеристик", "CustDev, приоритизация"),
        ]
    ):
        x = M + i * (fw + 16)
        d.kpi(x, y, fw, 95, v, "", GREEN)
        d.par(lab, x + 10, y - 62, fw - 20, style("pl", size=10.5, leading=13, align=TA_CENTER))
        d.par(src, x + 10, y - 110, fw - 20, style("ps", size=8.5, color=GRAY, align=TA_CENTER))
    fy, fh, sbw, sgap = y - 145, 62, 92, 12
    for i, name in enumerate(["Сбер", "Т-Банк", "ВТБ", "Excel"]):
        x = M + i * (sbw + sgap)
        c.setFillColor(colors.HexColor("#d9e2ec"))
        c.roundRect(x, fy - fh, sbw, fh, 6, stroke=0, fill=1)
        c.setFillColor(NAVY)
        c.setFont("ArialRUB", 12)
        c.drawCentredString(x + sbw / 2, fy - fh / 2 - 4, name)
    ax = M + 4 * (sbw + sgap)
    d.arrow(ax, fy - fh / 2, ax + 50, RED)
    d.card(
        ax + 60, fy, d.W - M - ax - 60, fh, "Ручная сверка каждый месяц",
        "15–20 минут — несколько часов; общей структуры и доходности не видно", accent=RED,
    )
    d.par(
        "<b>Для кого:</b> DIY-инвесторы MOEX с 2+ счетами, которые сами принимают решения и тратят на учёт "
        "от 15–20 минут до нескольких часов в месяц.",
        M, fy - fh - 24, W, S["s_body"],
    )

    # 3 Solution
    d.slide("Solution — решение")
    y = d.top - 20
    d.par(
        "Мы предлагаем <font color='#27a844'>FuncFund</font> — сервис учёта портфеля, который позволяет за 15 минут "
        "собрать все брокерские счета и активы на одном экране, решая проблему ручной сверки в Excel.",
        M + 30, y, W - 60, style("sol", "ArialRUB", 22, 30, align=TA_CENTER, color=NAVY),
    )
    steps = [
        ("1. Подключить", "отчёт или API брокера: Сбер, Т, ВТБ, Альфа"),
        ("2. Увидеть", "весь портфель: классы активов, счета, динамика"),
        ("3. Контролировать", "сверка за минуты вместо часов, без «советов»"),
    ]
    sw, gap = (W - 2 * 50) / 3, 50
    for i, (t, b) in enumerate(steps):
        x = M + i * (sw + gap)
        d.card(x, 375, sw, 90, t, b)
        if i < 2:
            d.arrow(x + sw + 8, 330, x + sw + gap - 8)
    kw = (W - 2 * 16) / 3
    for i, (v, lab) in enumerate(
        [
            ("15 мин", "от регистрации до полного портфеля"),
            ("4 брокера", "Сбер, Т-Инвестиции, ВТБ, Альфа"),
            ("0 советов", "только факты о портфеле, без buy/sell"),
        ]
    ):
        d.kpi(M + i * (kw + 16), 240, kw, 95, v, lab, GREEN)

    # 4 Product
    d.slide("Product — продукт: 3 ключевые функции")
    y = d.top
    lw = W * 0.55
    feats = [
        ("Импорт из любых брокеров", "HTML/XLSX-отчёты Сбера, ВТБ, Альфы и read-only API Т-Инвестиций + ручной ввод вкладов и валюты."),
        ("Единый live-дашборд", "Сумма на всех счетах, структура по классам активов и счетам, изменение за период — на одном экране."),
        ("Учёт без рекомендаций", "Только факты о портфеле: никаких сигналов buy/sell — честно и без регуляторных рисков."),
    ]
    for i, (t, b) in enumerate(feats):
        d.card(M, y - i * 112, lw, 100, t, b)
    d.par(
        "<b>Уникальность:</b> кросс-брокерный учёт MOEX с первого экрана. Кабинет брокера видит только себя, "
        "Excel требует ручного ввода.",
        M, y - 345, lw, S["s_small"],
    )
    iw = (W - lw - 30) / 2
    d.image(ASSETS / "dashboard.png", M + lw + 20, 40, iw, d.top - 50)
    d.image(ASSETS / "import.png", M + lw + 30 + iw, 40, iw, d.top - 50)

    # 5 Market
    d.slide("Market Size — рынок (top-down)")
    y = d.top
    levels = [
        ("TAM ≈ 105 млрд ₽/год", "35,1 млн частных инвесторов × 3 000 ₽/год — потолок, если бы подписку платили все", 1.0, colors.HexColor("#9fb3c8")),
        ("SAM ≈ 13,1 млрд ₽/год", "4,26 млн пользователей в 4 нишах: DIY-инвесторы, накопители с несколькими банками, ИП, crypto/FX", 0.78, colors.HexColor("#486581")),
        ("Ниша волны 1 ≈ 6,1 млрд ₽/год", "2,04 млн DIY-инвесторов MOEX с мультисчетами × 3 000 ₽", 0.58, NAVY),
        ("SOM ≈ 600 млн ₽/год", "200 тыс. платящих к 3-му году ≈ 9,8% ниши волны 1", 0.38, GREEN),
    ]
    bh = 72
    for i, (t, b, frac, col) in enumerate(levels):
        bw = W * 0.62 * frac
        x = M + (W * 0.62 - bw) / 2
        yy = y - (i + 1) * (bh + 6)
        c.setFillColor(col)
        c.roundRect(x, yy, bw, bh, 6, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("ArialRUB", 14)
        c.drawCentredString(x + bw / 2, yy + bh / 2 - 5, t)
        d.par(b, M + W * 0.62 + 20, yy + bh - 8, W * 0.38 - 20, style("mk", size=10.5, leading=13.5))
    d.par(
        "Источники: Мосбиржа (число инвесторов), Интерфакс (активные), Банк России (обзор брокеров), "
        "тарифы Snowball как ценовой ориентир. ARPU 3 000 ₽/год (≈250 ₽/мес) — консервативно ниже аналогов.",
        M, 58, W, S["s_small"],
    )

    # 6 Business model
    d.slide("Business Model — как зарабатываем")
    y = d.top - 10
    boxes = [
        ("Кто клиент", "DIY-инвестор MOEX с 2+ счетами"),
        ("Что покупает", "Premium: 2+ брокера, история, live-котировки"),
        ("Сколько платит", "349 ₽/мес или 2 990 ₽/год"),
    ]
    bw, gap = (W - 2 * 46) / 3, 46
    for i, (t, b) in enumerate(boxes):
        x = M + i * (bw + gap)
        d.card(x, y, bw, 95, t, b, body_style=style("bm", "ArialRUB", 13, 17))
        if i < 2:
            d.arrow(x + bw + 8, y - 48, x + bw + gap - 8, GREEN)
    d.par(
        "<b>Монетизация — freemium:</b> бесплатно 1 источник + ручной ввод (доходим до Aha-момента), "
        "платный триггер — подключение второго брокера. Оплата через ЮKassa.",
        M, y - 115, W, S["s_body"],
    )
    kw = (W - 3 * 14) / 4
    for i, (v, lab, colr) in enumerate(
        [
            (rub(U.ltv), "LTV", NAVY),
            (rub(U.cac), "CAC (цель)", NAVY),
            (f"{num(U.ltv_cac, 1)}×", "LTV / CAC", GREEN),
            (f"{num(U.payback_months, 1)} мес.", "окупаемость CAC", GREEN),
        ]
    ):
        d.kpi(M + i * (kw + 14), y - 190, kw, 85, v, lab, colr)
    by = y - 335
    d.par(
        f"<b>Один платящий клиент приносит в {num(U.ltv_cac, 0)} раз больше маржи, чем стоит его привлечение:</b>",
        M, by + 22, W, S["s_body"],
    )
    full = W - 160
    for i, (name, val, colr) in enumerate([("LTV", U.ltv, GREEN), ("CAC", U.cac, ORANGE)]):
        yy = by - 32 - i * 40
        c.setFillColor(colors.black)
        c.setFont("ArialRUB", 12)
        c.drawString(M, yy + 8, name)
        c.setFillColor(colr)
        c.rect(M + 50, yy, full * val / U.ltv, 28, stroke=0, fill=1)
        c.setFillColor(colors.black)
        c.drawString(M + 58 + full * val / U.ltv, yy + 9, rub(val))

    # 7 Competition
    d.slide("Competition — конкуренты")
    y = d.top
    gx, gy, gw, gh = M + 40, 70, W * 0.55, d.top - 100
    c.setStrokeColor(GRID)
    c.setLineWidth(1)
    c.rect(gx, gy, gw, gh, stroke=1, fill=0)
    c.line(gx + gw / 2, gy, gx + gw / 2, gy + gh)
    c.line(gx, gy + gh / 2, gx + gw, gy + gh / 2)
    c.setFillColor(GRAY)
    c.setFont("ArialRU", 9.5)
    c.drawCentredString(gx + gw / 2, gy - 16, "Цена для пользователя →  (бесплатно … дороже)")
    c.saveState()
    c.translate(gx - 14, gy + gh / 2)
    c.rotate(90)
    c.drawCentredString(0, 0, "Учёт нескольких брокеров MOEX в одном окне →")
    c.restoreState()
    pts = [
        ("Кабинеты брокеров (Сбер, Т, ВТБ)", 0.08, 0.18, colors.HexColor("#829ab1")),
        ("Excel / Google Sheets", 0.06, 0.48, colors.HexColor("#829ab1")),
        ("Zenmoney (бюджет)", 0.45, 0.28, colors.HexColor("#829ab1")),
        ("Intelinvest", 0.62, 0.66, colors.HexColor("#829ab1")),
        ("Snowball Income", 0.80, 0.78, colors.HexColor("#829ab1")),
        ("FuncFund", 0.40, 0.88, GREEN),
    ]
    for name, px, py, col in pts:
        cx, cy = gx + gw * px, gy + gh * py
        c.setFillColor(col)
        c.circle(cx, cy, 9 if name == "FuncFund" else 6, stroke=0, fill=1)
        c.setFillColor(colors.black)
        c.setFont("ArialRUB" if name == "FuncFund" else "ArialRU", 10 if name == "FuncFund" else 9)
        if px > 0.7:
            c.drawRightString(cx - 10, cy - 3, name)
        else:
            c.drawString(cx + 11, cy - 3, name)
    rx, rw = gx + gw + 30, d.W - M - (gx + gw + 30)
    d.card(rx, y, rw, 128, "Почему мы лучше", "Брокеры видят только свои счета. Excel — ручной ввод. Snowball и Intelinvest — сильный учёт, но дороже (Snowball 299–890 ₽/мес).")
    d.card(
        rx, y - 142, rw, 150, "УТП",
        "Все счета MOEX за 15 минут: импорт Сбера, ВТБ, Альфы + API Т-Инвестиций, бесплатный старт, "
        "годовой Premium 2 990 ₽ — на нижней границе цен ниши. Без советов buy/sell.",
        accent=GREEN,
    )
    d.par("Позиции на матрице — экспертная оценка по конкурентному анализу (10 критериев, CustDev).", rx, y - 305, rw, S["s_small"])

    # 8 Marketing & Traction
    d.slide("Marketing & Traction — первые 1000 пользователей")
    y = d.top
    d.par("<b>Что уже есть</b> (дашборд метрик MVP, ноябрь 2026):", M, y, W, S["s_body"])
    d.image(ASSETS / "metrics.png", M, y - 125, W, 100)
    y -= 140
    col = (W - 2 * 14) / 3
    chans = [
        ("Telegram-чаты и каналы инвесторов", "Посты «сверка портфеля за 15 минут» + бета-инвайты. Цель: 500 регистраций."),
        ("Контент: VC.ru, Хабр, Shorts", "Разборы «как свести счета разных брокеров». Цель: 300 регистраций."),
        ("Рефералы и CustDev-база", "14 респондентов с согласием на бету; месяц Premium за друга. Цель: 200 регистраций."),
    ]
    for i, (t, b) in enumerate(chans):
        d.card(M + i * (col + 14), y, col, 85, t, b)
    d.par(
        "Прогресс: MVP в проде с 31.10.2026 (импорт 4 брокеров, OAuth, оплата ЮKassa), CustDev n=14, "
        "участие в акселераторе ВТБ «Финтех без границ» (спринт 1 сдан). Следующий шаг — 5+ протоколов бета-теста.",
        M, y - 97, W, S["s_small"],
    )
    fy = y - 145
    d.par("<b>Целевая воронка первой 1000</b> (гипотеза для пилота, метрики AARRR):", M, fy, W, S["s_body"])
    funnel = [
        ("1 000 регистраций", 1.0, colors.HexColor("#9fb3c8")),
        ("600 активаций — увидели свой портфель (60%)", 0.6, colors.HexColor("#486581")),
        ("250 возвращаются еженедельно (25%)", 0.25, NAVY),
        ("50 платящих Premium (5%)", 0.05, GREEN),
    ]
    fw_max = W * 0.55
    for i, (lab, frac, colr) in enumerate(funnel):
        yy = fy - 24 - (i + 1) * 30
        c.setFillColor(colr)
        c.rect(M, yy, max(fw_max * frac, 14), 24, stroke=0, fill=1)
        c.setFillColor(colors.black)
        c.setFont("ArialRU", 10.5)
        c.drawString(M + max(fw_max * frac, 14) + 10, yy + 8, lab)

    # 9 Financials
    d.slide("Financials — финансы")
    y = d.top
    lw = W * 0.44
    fin = [
        ["Год 1 (2027), базовый сценарий", "тыс. ₽"],
        ["Выручка (7 500 средних платящих × 3 000 ₽)", "22 500"],
        ["Эквайринг и инфраструктура", "−1 706"],
        ["<b>Валовая прибыль (маржа 92%)</b>", "<b>20 795</b>"],
        ["Маркетинг (16 500 привлечённых × 900 ₽)", "−14 850"],
        ["ФОТ 2 FTE с взносами", "−6 240"],
        ["Прочие (юрист, бухгалтерия, сервисы)", "−600"],
        ["<b>EBITDA</b>", "<b>−896</b>"],
        ["Налог УСН 6%", "−1 350"],
        ["<b>Чистая прибыль</b>", "<b>−2 246</b>"],
    ]
    rows = [[Paragraph(a, style("fh", "ArialRUB", 10, 13) if i == 0 else style("f", size=10, leading=13)), Paragraph(b, style("fr", "ArialRUB" if i == 0 else "ArialRU", 10, 13, align=2))] for i, (a, b) in enumerate(fin)]
    t = Table(rows, colWidths=[lw - 2.6 * cm, 2.6 * cm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9e2ec")), ("GRID", (0, 0), (-1, -1), 0.4, GRID), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    th = d.table(t, M, y, lw)
    d.par(
        "Окупаемость по накопленному денежному потоку — во 2-м году. <b>Ищем 3 млн ₽</b>: дефицит года 1 "
        "(2,2 млн) + запас на кассовые разрывы.",
        M, y - th - 12, lw, style("fn", size=11, leading=14.5),
    )
    bar_chart(
        d, M + lw + 70, 110, W - lw - 90, d.top - 175,
        [[22.5, 112.5, 390], [9, 45, 156]], ["2027", "2028", "2029"], [GREEN, colors.HexColor("#829ab1")],
        400, 100, "Выручка, млн ₽", ["база: 15 → 60 → 200 тыс. платящих", "пессимистичный: 6 → 24 → 80 тыс."],
    )

    # 10 Ask
    d.slide("Ask — что просим")
    y = d.top
    d.par("Ищем <font color='#27a844'>3 млн ₽ на 12 месяцев</font> на запуск роста волны 1 — двумя траншами по результатам пилота.", M, y, W, S["s_big"])
    y -= 70
    parts = [
        ("Маркетинг", 0.40, "1,2 млн ₽ — тест и масштаб каналов, ~1 300 платящих при CAC 900 ₽", GREEN),
        ("Разработка", 0.30, "0,9 млн ₽ — 2-й разработчик на 6 мес.: CSV/новые брокеры, онбординг", NAVY),
        ("Зарплаты", 0.20, "0,6 млн ₽ — поддержка и контент (part-time)", colors.HexColor("#486581")),
        ("Операционные", 0.10, "0,3 млн ₽ — инфраструктура, юрист, бухгалтерия", colors.HexColor("#829ab1")),
    ]
    bx, bw = M, W * 0.5
    for i, (name, share, desc, col) in enumerate(parts):
        yy = y - i * 48
        c.setFillColor(col)
        c.rect(bx + 110, yy - 26, bw * share / 0.4, 26, stroke=0, fill=1)
        c.setFillColor(colors.black)
        c.setFont("ArialRUB", 11)
        c.drawString(bx, yy - 18, name)
        c.setFillColor(colors.white)
        c.drawString(bx + 116, yy - 18, f"{share * 100:.0f}%")
        d.par(desc, bx + 120 + bw, yy - 2, W - bw - 120, style("ad", size=10, leading=12.5))
    y -= 4 * 48 + 20
    d.par("<b>Вехи</b>", M, y, W, S["s_body"])
    ms = [
        ("3 мес.", "10–12 оплат, CAC ≤ 900 ₽ подтверждён → 2-й транш"),
        ("6 мес.", "1 000 платящих, импорт без ошибок ≥ 80%"),
        ("12 мес.", "6 000–15 000 платящих (пессимистичный — базовый план); в базе EBITDA > 0 во 2-м году"),
    ]
    mw = (W - 2 * 14) / 3
    for i, (t, b) in enumerate(ms):
        d.card(M + i * (mw + 14), y - 22, mw, 80, t, b)
    d.save()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    targets = {
        "ДЗ 1_Царюк АВ_102 221.pdf": build_hw1,
        "ДЗ 2_Царюк АВ_102 221.pdf": build_hw2,
        "Итог_Царюк АВ_102 221.pdf": build_final,
    }
    for name, fn in targets.items():
        fn(OUT / name)
        print("OK", OUT / name)


if __name__ == "__main__":
    main()
