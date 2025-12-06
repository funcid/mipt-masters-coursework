"""
Скрипт для генерации PDF файла с эссе и критическим анализом
для итогового задания.

Требования к оформлению:
- 14 шрифт Arial
- 1,5 интервала
- Первичный текст (эссе) - не менее 10 страниц
- Критический анализ - не менее 3 страниц
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
import os
import sys


def register_arial_font():
    """Регистрирует шрифт Arial для использования в PDF."""
    try:
        # Попытка зарегистрировать Arial (Windows)
        arial_paths = [
            r'C:\Windows\Fonts\arial.ttf',
            r'C:\Windows\Fonts\arialbd.ttf',
            r'C:\Windows\Fonts\ARIAL.TTF',
        ]
        
        for path in arial_paths:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont('Arial', path))
                pdfmetrics.registerFont(TTFont('ArialBold', path))
                return True
        
        # Если Arial не найден, используем стандартный шрифт
        print("Предупреждение: Шрифт Arial не найден. Будет использован стандартный шрифт.")
        return False
    except Exception as e:
        print(f"Предупреждение: Не удалось зарегистрировать Arial: {e}")
        return False


def create_pdf(essay_text, analysis_text, output_filename, ai_system="ChatGPT", ai_link=""):
    """
    Создает PDF файл с эссе и критическим анализом.
    
    Args:
        essay_text: Текст эссе, сгенерированный ИИ
        analysis_text: Текст критического анализа
        output_filename: Имя выходного файла (без расширения)
        ai_system: Название использованной системы ИИ
        ai_link: Ссылка на систему ИИ
    """
    # Регистрируем шрифт
    arial_available = register_arial_font()
    font_name = 'Arial' if arial_available else 'Helvetica'
    bold_font_name = 'ArialBold' if arial_available else 'Helvetica-Bold'
    
    # Создаем документ
    doc = SimpleDocTemplate(
        f"{output_filename}.pdf",
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Создаем стили
    styles = getSampleStyleSheet()
    
    # Стиль для заголовков
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=bold_font_name,
        fontSize=16,
        spaceAfter=12,
        spaceBefore=12,
        alignment=TA_LEFT
    )
    
    # Стиль для основного текста (14pt, 1.5 интервал)
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=14,
        leading=21,  # 1.5 интервал: 14 * 1.5 = 21
        alignment=TA_JUSTIFY,
        spaceAfter=6
    )
    
    # Стиль для информации об ИИ системе
    info_style = ParagraphStyle(
        'CustomInfo',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=12,
        leading=18,
        alignment=TA_LEFT,
        spaceAfter=12
    )
    
    # Собираем содержимое документа
    story = []
    
    # Заголовок: Эссе
    story.append(Paragraph("ЭССЕ", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Информация об использованной системе ИИ
    ai_info = f"<b>Использованная система искусственного интеллекта:</b> {ai_system}"
    if ai_link:
        ai_info += f" ({ai_link})"
    story.append(Paragraph(ai_info, info_style))
    story.append(Spacer(1, 0.3*cm))
    
    # Текст эссе
    essay_paragraphs = essay_text.split('\n\n')
    for para in essay_paragraphs:
        if para.strip():
            # Обрабатываем подзаголовки (строки, которые выглядят как заголовки)
            if para.strip().isupper() or (len(para.strip()) < 100 and not para.strip().endswith('.')):
                story.append(Spacer(1, 0.3*cm))
                story.append(Paragraph(f"<b>{para.strip()}</b>", normal_style))
                story.append(Spacer(1, 0.2*cm))
            else:
                # Обычный параграф
                story.append(Paragraph(para.strip(), normal_style))
    
    # Разрыв страницы перед критическим анализом
    story.append(PageBreak())
    
    # Заголовок: Критический анализ
    story.append(Paragraph("КРИТИЧЕСКИЙ АНАЛИЗ", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Текст критического анализа
    analysis_paragraphs = analysis_text.split('\n\n')
    for para in analysis_paragraphs:
        if para.strip():
            # Обрабатываем подзаголовки
            if para.strip().isupper() or (len(para.strip()) < 100 and not para.strip().endswith('.')):
                story.append(Spacer(1, 0.3*cm))
                story.append(Paragraph(f"<b>{para.strip()}</b>", normal_style))
                story.append(Spacer(1, 0.2*cm))
            else:
                # Обычный параграф
                story.append(Paragraph(para.strip(), normal_style))
    
    # Строим PDF
    doc.build(story)
    print(f"PDF файл успешно создан: {output_filename}.pdf")


def main():
    """Основная функция для интерактивного создания PDF."""
    print("=" * 60)
    print("Генератор PDF для итогового задания")
    print("Тема: Лаплас и наука Просвещения. Механицизм, редукционизм, детерминизм.")
    print("=" * 60)
    print()
    
    # Запрашиваем информацию об ИИ системе
    ai_system = input("Введите название использованной системы ИИ (например, ChatGPT): ").strip()
    if not ai_system:
        ai_system = "ChatGPT"
    
    ai_link = input("Введите ссылку на систему ИИ (необязательно): ").strip()
    
    print("\n" + "-" * 60)
    print("ВВЕДЕНИЕ ТЕКСТА ЭССЕ")
    print("Введите текст эссе (не менее 10 страниц).")
    print("Для завершения ввода введите пустую строку три раза подряд.")
    print("-" * 60)
    
    essay_lines = []
    empty_count = 0
    while True:
        line = input()
        if not line.strip():
            empty_count += 1
            if empty_count >= 3:
                break
        else:
            empty_count = 0
            essay_lines.append(line)
    
    essay_text = '\n'.join(essay_lines)
    
    print("\n" + "-" * 60)
    print("ВВЕДЕНИЕ ТЕКСТА КРИТИЧЕСКОГО АНАЛИЗА")
    print("Введите текст критического анализа (не менее 3 страниц).")
    print("Для завершения ввода введите пустую строку три раза подряд.")
    print("-" * 60)
    
    analysis_lines = []
    empty_count = 0
    while True:
        line = input()
        if not line.strip():
            empty_count += 1
            if empty_count >= 3:
                break
        else:
            empty_count = 0
            analysis_lines.append(line)
    
    analysis_text = '\n'.join(analysis_lines)
    
    # Запрашиваем имя файла
    print("\n" + "-" * 60)
    default_filename = "ФИО_Название_магистратуры_МНИ"
    filename = input(f"Введите имя файла (без расширения) [{default_filename}]: ").strip()
    if not filename:
        filename = default_filename
    
    # Создаем PDF
    try:
        create_pdf(essay_text, analysis_text, filename, ai_system, ai_link)
        print(f"\n✓ Файл {filename}.pdf успешно создан!")
    except Exception as e:
        print(f"\n✗ Ошибка при создании PDF: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Проверяем, есть ли аргументы командной строки для использования файлов
    if len(sys.argv) >= 3:
        # Режим работы с файлами
        essay_file = sys.argv[1]
        analysis_file = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) > 3 else "essay_output"
        ai_system = sys.argv[4] if len(sys.argv) > 4 else "ChatGPT"
        ai_link = sys.argv[5] if len(sys.argv) > 5 else ""
        
        try:
            with open(essay_file, 'r', encoding='utf-8') as f:
                essay_text = f.read()
            with open(analysis_file, 'r', encoding='utf-8') as f:
                analysis_text = f.read()
            
            create_pdf(essay_text, analysis_text, output_file, ai_system, ai_link)
        except Exception as e:
            print(f"Ошибка: {e}")
            sys.exit(1)
    else:
        # Интерактивный режим
        main()

