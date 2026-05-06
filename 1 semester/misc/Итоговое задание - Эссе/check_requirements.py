"""
Скрипт для проверки соответствия PDF файла всем требованиям задания
"""

import os
import sys

def check_file_exists(filename):
    """Проверяет существование файла"""
    if os.path.exists(filename):
        print(f"✓ Файл существует: {filename}")
        return True
    else:
        print(f"✗ Файл не найден: {filename}")
        return False

def check_filename_format(filename):
    """Проверяет формат имени файла: ФИО_Название магистратуры_МНИ"""
    expected = "Царюк Артём Владимирович_Разработка IT-продукта_МНИ.pdf"
    if filename == expected:
        print(f"✓ Имя файла соответствует формату: {filename}")
        return True
    else:
        print(f"✗ Имя файла не соответствует формату")
        print(f"  Ожидалось: {expected}")
        print(f"  Получено: {filename}")
        return False

def check_text_lengths():
    """Проверяет объемы текстов"""
    try:
        with open('essay_laplace.txt', 'r', encoding='utf-8') as f:
            essay_text = f.read()
        with open('analysis_laplace.txt', 'r', encoding='utf-8') as f:
            analysis_text = f.read()
        
        essay_chars = len(essay_text)
        analysis_chars = len(analysis_text)
        
        # Примерно 2000 символов на страницу при 14pt Arial, 1.5 интервал
        essay_pages = essay_chars / 2000
        analysis_pages = analysis_chars / 2000
        
        print(f"\nОбъемы текстов:")
        print(f"  Эссе: {essay_chars} символов (~{essay_pages:.1f} страниц)")
        print(f"  Анализ: {analysis_chars} символов (~{analysis_pages:.1f} страниц)")
        
        essay_ok = essay_pages >= 10
        analysis_ok = analysis_pages >= 3
        
        if essay_ok:
            print(f"✓ Эссе соответствует требованию (не менее 10 страниц)")
        else:
            print(f"✗ Эссе не соответствует требованию (требуется не менее 10 страниц)")
        
        if analysis_ok:
            print(f"✓ Анализ соответствует требованию (не менее 3 страниц)")
        else:
            print(f"✗ Анализ не соответствует требованию (требуется не менее 3 страниц)")
        
        return essay_ok and analysis_ok
    except Exception as e:
        print(f"✗ Ошибка при проверке объемов: {e}")
        return False

def check_analysis_content():
    """Проверяет, что критический анализ содержит необходимые разделы"""
    try:
        with open('analysis_laplace.txt', 'r', encoding='utf-8') as f:
            analysis_text = f.read().lower()
        
        required_keywords = [
            'адекватность',
            'осмысленность',
            'достоверность'
        ]
        
        found = []
        missing = []
        
        for keyword in required_keywords:
            if keyword in analysis_text:
                found.append(keyword)
            else:
                missing.append(keyword)
        
        print(f"\nПроверка содержания критического анализа:")
        for keyword in found:
            print(f"✓ Найден раздел: {keyword}")
        for keyword in missing:
            print(f"✗ Отсутствует раздел: {keyword}")
        
        return len(missing) == 0
    except Exception as e:
        print(f"✗ Ошибка при проверке содержания: {e}")
        return False

def check_essay_content():
    """Проверяет, что эссе содержит информацию об ИИ системе"""
    try:
        with open('essay_laplace.txt', 'r', encoding='utf-8') as f:
            essay_text = f.read()
        
        # Проверяем наличие темы
        topic_keywords = ['лаплас', 'просвещения', 'механицизм', 'редукционизм', 'детерминизм']
        found_keywords = [kw for kw in topic_keywords if kw.lower() in essay_text.lower()]
        
        print(f"\nПроверка содержания эссе:")
        print(f"✓ Найдены ключевые слова темы: {len(found_keywords)}/{len(topic_keywords)}")
        
        return len(found_keywords) >= 4
    except Exception as e:
        print(f"✗ Ошибка при проверке эссе: {e}")
        return False

def main():
    """Основная функция проверки"""
    print("=" * 70)
    print("ПРОВЕРКА СООТВЕТСТВИЯ ТРЕБОВАНИЯМ ЗАДАНИЯ")
    print("=" * 70)
    
    filename = "Царюк Артём Владимирович_Разработка IT-продукта_МНИ.pdf"
    
    results = []
    
    # Проверка 1: Существование файла
    print("\n1. Проверка существования файла:")
    results.append(check_file_exists(filename))
    
    # Проверка 2: Формат имени файла
    print("\n2. Проверка формата имени файла:")
    results.append(check_filename_format(filename))
    
    # Проверка 3: Объемы текстов
    print("\n3. Проверка объемов текстов:")
    results.append(check_text_lengths())
    
    # Проверка 4: Содержание критического анализа
    print("\n4. Проверка содержания критического анализа:")
    results.append(check_analysis_content())
    
    # Проверка 5: Содержание эссе
    print("\n5. Проверка содержания эссе:")
    results.append(check_essay_content())
    
    # Итоговый результат
    print("\n" + "=" * 70)
    print("ИТОГОВЫЙ РЕЗУЛЬТАТ:")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ ({passed}/{total})")
        print("\nФайл готов к сдаче!")
    else:
        print(f"✗ ПРОЙДЕНО ПРОВЕРОК: {passed}/{total}")
        print("\nТребуется исправление!")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

