import json
import re
import csv
import argparse
import os
import sys

def get_unit(i):
    units = ['', 'km/h', 'mph', 'km', 'miles', 'kPa', 'rpm', '°', 'g/sec', 'kg/min', 'V', 'Pa', 'L/h',
             'Nm', '%', '°C', '°F', 'sec', 'min', 'mA', 'meters', 'ft.', 'l/100km', 'MPG', 'L', 'gal.',
             'Ohm', 'kOhm', 'MOhm', 'MHz', 'Hz', 'V/msec', 'Pa/sec.', 'kg/h', 'g/cylinder', 'g/stroke',
             'mm', 'lbs', 'g.', 'nV/sec', 'gpm', 'ppm', 'g', 'm/s²', 'ms', 'hp', 'kW', 'psi', 'bar',
             'mV', 'km/L', 'μs', 'mbar', 'W', 'h', 'm^3/h', 'mg/c', 'days', '$', 'A', 'kWh', 'Wh', 'Ah',
             'Hours', 'μs', 'g_L', 'kPsi', 'mm3', 'mg_stroke', 'hPa', 'revs'] #TODO
    if i is not None and 0 < i < len(units):
        return units[i]
    else:
        return ''


def clean_diagnostic_string(value):
    """Очищает строки BCM и ACM от элементов с префиксом 'ATFC'"""
    if not value or not isinstance(value, str):
        return ''

    elements = value.split(';')
    filtered = [elem for elem in elements if not elem.startswith('ATFC')]

    return '\\'.join(filtered)

def transform_tvv_string(tvv_string):
    """Преобразует строку TVV по заданному образцу"""
    if not tvv_string:
        return ''

    # Словарь замены символов для str.translate
    replacement_map = {
        ord(' '): '_',  # пробел на подчеркивание
        ord('('): '<',  # открывающая скобка на квадратную скобку
        ord(')'): '>',  # закрывающая скобка на квадратную скобку
    }

    parts = tvv_string.split(';')
    transformed_parts = []

    for part in parts:
        if '=' in part:
            key, value = part.split('=', 1)
            # Заменяем символы в значении
            value_replaced = value.translate(replacement_map)
            value_quoted = f"'{value_replaced}'"
            transformed_parts.append(f"{key}={value_quoted}")

    return ':'.join(transformed_parts)


def simple_transform(obj, is_optmize=False):
    output_json = {
        'ModeAndPID': obj.get('CMD', ''),
        'Name': obj.get('NM', ''),
        'ShortName': obj.get('SNM', ''),

        'Equation': '',
        'Min Value': obj.get('MIN', '0'),
        'Max Value': obj.get('MAX', '100'),
        'Units': get_unit(obj.get('UN')),
        'Header': obj.get('HDR', ''),
        'startDiagnostic': obj.get('BCM', '').replace(';', '\\'), #TODO optimize
        'stopDiagnostic': obj.get('ACM', '').replace(';', '\\'),
    }

    if is_optmize and (obj.get('SBI', 0) + obj.get('DL', 0)) <= 7:
        output_json['startDiagnostic'] = clean_diagnostic_string(obj.get('BCM', ''))
        output_json['stopDiagnostic'] = clean_diagnostic_string(obj.get('ACM', ''))

    if obj.get('TP') == 0:  # Формула
        output_json['Equation'] = obj.get('FR', '')

    elif obj.get('TP') == 1:  # Поряок байт
        # Максимальная длина данных (A-Z = 26 байт)
        MAX_BYTES: int = 26

        shift = obj.get('SBI', 0)
        if shift < 0 or shift > MAX_BYTES: return None

        dl = obj.get('DL', 0)

        # Генерируем буквы A-Z со сдвигом
        bytes_letters = [chr(ord('A') + shift + i) for i in range(MAX_BYTES - dl)]

        equation = ''

        if dl == 1:   equation = bytes_letters[0]

        elif dl == 2: equation = f"INT16{bytes_letters[0]}:{bytes_letters[1]})" #f"({bytes_letters[0]}*256+{bytes_letters[1]})"

        elif dl == 3: equation = f"INT24({bytes_letters[0]}:{bytes_letters[1]}:{bytes_letters[2]})" #f"({bytes_letters[0]}*65536+{bytes_letters[1]}*256+{bytes_letters[2]})"

        elif dl == 4: equation = f"INT32({bytes_letters[0]}:{bytes_letters[1]}:{bytes_letters[2]}:{bytes_letters[3]})" #f"({bytes_letters[0]}*16777216+{bytes_letters[1]}*65536+{bytes_letters[2]}*256+{bytes_letters[3]})"

        elif 5 <= dl <= (MAX_BYTES - shift):
            # Динамическое построение для любой длины
            terms = []
            for i in range(dl):
                if i == dl - 1:
                    # Последний байт (младший) - без множителя
                    terms.append(bytes_letters[i])
                else:
                    # Старшие байты с множителями
                    power = 256 ** (dl - 1 - i)
                    terms.append(f"{bytes_letters[i]}*{power}")
            equation = "(" + "+".join(terms) + ")"

            # Альтернативная запись в обратном порядке (от старшего к младшему)
            # terms_reversed = []
            # for i in range(dl):
            #     power = POWERS_OF_256[dl - 1 - i]
            #     if power == 1:
            #         terms_reversed.append(bytes_letters[i])
            #     else:
            #         terms_reversed.append(f"{bytes_letters[i]}*{power}")
            # equation = "(" + "+".join(terms_reversed) + ")"

        else:
            # Некорректная длина
            print(f"Предупреждение: некорректная длина данных DL={dl} для объекта {obj.get('NM', 'Unknown')}")
            return None

        if obj.get('SIG', False) == True and dl <= 4:
            if dl == 1:   equation = f"SIGNED8({equation})"
            elif dl == 2: equation = f"SIGNED16({equation})"
            elif dl == 3: equation = f"SIGNED24({equation})"
            elif dl == 4: equation = f"SIGNED32({equation})"

        if obj.get('MUL') is not None and obj.get('MUL') != 1: equation += f"*{str(obj.get('MUL'))}"
        if obj.get('DIV') is not None and obj.get('DIV') != 1: equation += f"/{str(obj.get('DIV'))}"
        if obj.get('OFS') is not None and obj.get('OFS') != 0: equation += f"+ ({str(obj.get('OFS'))})"

        if obj.get('TVV') is not None and obj.get('TVV') != 'null':
            equation = f"LOOKUP({equation}:\'{equation}\':{transform_tvv_string(str(obj.get('TVV')))})"

        # TODO 'SIG', 'RBS', 'SBI'
        output_json['Equation'] = equation

    elif obj.get('TP') == 2:  # Бит
        byte = chr(ord('A') + obj.get('SBI', 0))
        output_json['Equation'] = f"BIT({byte}:{str(obj.get('BIT', 0))})"

    else:                       # Действия и другие типы пропускаются
        return None

    return output_json


def process_files(input_file, input_csv_file=None, intermediate_json_file=None, output_csv_file=None, is_verbose=False, is_debug=False, is_optmize=False):
    """
    Основная функция обработки файлов

    Args:
        input_file (str): путь к входному JSON файлу
        input_csv_file (str): путь к CSV файлу с исходными данными
        intermediate_json_file (str): путь к промежуточному JSON файлу
        output_csv_file (str): путь к выходному CSV файлу с преобразованными данными
    """

    # Устанавливаем значения по умолчанию, если не указаны
    if input_csv_file is None:
        base_name = os.path.splitext(input_file)[0]
        input_csv_file = f"{base_name}_original.csv"

    if intermediate_json_file is None:
        base_name = os.path.splitext(input_file)[0]
        intermediate_json_file = f"{base_name}_transformed.json"

    if output_csv_file is None:
        base_name = os.path.splitext(input_file)[0]
        output_csv_file = f"{base_name}.csv"

    try:
        # Проверяем существование входного файла
        if not os.path.exists(input_file):
            print(f"Ошибка: Файл {input_file} не найден!")
            return False

        # Читаем и преобразуем исходный JSON
        if is_verbose: print(f"Чтение файла: {input_file}")
        with open(input_file, 'r', encoding='utf-8-sig') as f:
            content = re.sub(r',(\s*[}\]])', r'\1', f.read())
            original_data = json.loads(content)

        if is_verbose: print(f"Загружено {len(original_data)} объектов")

        # Конвертируем исходный JSON в CSV
        if is_debug:
            print(f"Создание CSV с исходными данными: {input_csv_file}")
            fieldnames = set()
            for item in original_data:
                fieldnames.update(item.keys())

            with open(input_csv_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=sorted(fieldnames), delimiter=';', extrasaction='ignore')
                writer.writeheader()
                writer.writerows(original_data)

        # Преобразуем данные
        if is_verbose: print("Трансформация данных...")
        transformed_data = [
            transformed for transformed in
            (simple_transform(obj, is_optmize) for obj in original_data)
            if transformed is not None
        ]

        # Сохраняем преобразованный JSON
        if is_debug:
            print(f"Сохранение преобразованного JSON: {intermediate_json_file}")
            with open(intermediate_json_file, 'w', encoding='utf-8') as f:
                json.dump(transformed_data, f, ensure_ascii=False, indent=2)

        # Конвертируем преобразованный JSON в CSV
        print(f"Создание CSV с преобразованными данными: {output_csv_file}")
        field_order = ['Name', 'ShortName', 'ModeAndPID', 'Equation', 'Min Value',
                       'Max Value', 'Units', 'Header', 'startDiagnostic', 'stopDiagnostic']

        with open(output_csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=',', quoting=csv.QUOTE_ALL)
            writer.writerow(field_order)

            for obj in transformed_data:
                row = [json.dumps(obj[field], ensure_ascii=False) if isinstance(obj[field], (list, dict))
                       else obj[field] for field in field_order]
                writer.writerow(row)

        if is_verbose:
            print(f"\n ✓ Готово! Созданы файлы:")
            print(f"  - {input_csv_file} (исходные данные в CSV)")
            print(f"  - {intermediate_json_file} (преобразованный JSON)")
            print(f"  - {output_csv_file} (CSV с преобразованными данными)")

        return True

    except json.JSONDecodeError as e:
        print(f"Ошибка парсинга JSON: {e}")
        print("Проверьте корректность JSON файла")
        return False
    except Exception as e:
        obj_name = obj.get('NM', 'Unknown')
        obj_cmd = obj.get('CMD', 'Unknown')
        print(f"Ошибка при обработке объекта NM='{obj_name}', CMD='{obj_cmd}': {str(e)}")
        return False


def main():
    """Основная функция с обработкой аргументов командной строки"""

    parser = argparse.ArgumentParser(
        description='Преобразование CSP файла с PID параметрами для CareScanner в CSV для TorquePro',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  # Базовое использование (все файлы создаются автоматически)
  python script.py custompids.csp

  # Указание всех файлов
  python script.py custompids.csp -ic original.csv -ij transformed.json -oc output.csv

  # Указание только входного и выходного CSV для преобразованных данных
  python script.py custompids.csp -oc result.csv

  # Краткая форма
  python script.py custompids.csp -i original.csv -j transformed.json -o output.csv

  # С подробным выводом
  python script.py custompids.csp -v
  
  # С сохранением промежуточных файлов преобразования
  python script.py custompids.csp -d

Имена файлов по умолчанию:
  - Исходный CSV: <имя_входного_файла>_original.csv
  - Преобразованный JSON: <имя_входного_файла>_transformed.json
  - Преобразованный CSV: <имя_входного_файла>.csv
        """
    )

    # Добавляем аргументы
    parser.add_argument(
        'input_file',
        type=str,
        help='Путь к входному CSP файлу с пидами для CarScanner'
    )

    parser.add_argument(
        '-i', '--input-csv',
        type=str,
        dest='input_csv',
        default=None,
        help='Путь к промежуточному CSV файлу с исходными данными (по умолчанию: <имя>_original.csv)'
    )

    parser.add_argument(
        '-j', '--json-output',
        type=str,
        dest='json_output',
        default=None,
        help='Путь к промежуточному JSON файлу с пидами для TorquePro (по умолчанию: <имя>_transformed.json)'
    )

    parser.add_argument(
        '-o', '--output-csv',
        type=str,
        dest='output_csv',
        default=None,
        help='Путь к выходному CSV файлу с преобразованными пидами для TorquePro (по умолчанию: <имя>.csv)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Подробный вывод информации'
    )

    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Сохранять файлы промежуточных преобразований'
    )

    parser.add_argument(
        '-op', '--optimize',
        action='store_true',
        help='Оптимизировать. (удаляет настройку FlowControl для сообщений в один фрейм)'
    )
    # Парсим аргументы
    args = parser.parse_args()

    # Выводим информацию если verbose
    if args.verbose:
        print("=" * 70)
        print("Преобразователь CSP PID в CSV")
        print("=" * 70)
        print(f"Входной CSP файл: {args.input_file}")
        print(f"Промежуточный CSV (исходные данные): {args.input_csv if args.input_csv else '<авто>'}")
        print(f"Промежуточный JSON файл (преобразованные): {args.json_output if args.json_output else '<авто>'}")
        print(f"Выходной CSV (преобразованные): {args.output_csv if args.output_csv else '<авто>'}")
        print("=" * 70)
        print()

    # Обрабатываем файлы
    success = process_files(
        args.input_file,
        args.input_csv,
        args.json_output,
        args.output_csv,
        args.verbose,
        args.debug,
        args.optimize
    )

    # Возвращаем код завершения
    sys.exit(0 if success else 1)


# Простая версия для drag-and-drop (Windows)
def main_drag_drop():
    """Версия для Windows с поддержкой перетаскивания файлов"""
    print("Преобразователь CSP PID в CSV")
    print("-" * 40)

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        print(f"Входной файл: {input_file}")
    else:
        input_file = input("Введите путь к CSP файлу: ").strip().strip('"')

    if not input_file:
        print("Ошибка: файл не указан!")
        input("Нажмите Enter для выхода...")
        sys.exit(1)

    # Запрашиваем дополнительные параметры
    print("\nДополнительные параметры (Enter для пропуска):")
    input_csv = input("Исходный CSV файл: ").strip().strip('"') or None
    json_output = input("Промежуточный JSON файл: ").strip().strip('"') or None
    output_csv = input("Выходной CSV файл: ").strip().strip('"') or None

    print("\nОбработка...")
    success = process_files(input_file, input_csv, json_output, output_csv)

    input("\nНажмите Enter для выхода...")


if __name__ == "__main__":
    # Для использования с drag-and-drop в Windows, раскомментируйте строку ниже:
    # main_drag_drop()

    # Стандартное использование с аргументами командной строки
    main()