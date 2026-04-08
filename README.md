# CarScannerToTorquePro
Converter PID from CarScanner CSP format to TorquePro CSV format


Преобразование CSP файла с PID параметрами для CareScanner в CSV для TorquePro

positional arguments:
  input_file            Путь к входному CSP файлу с пидами для CarScanner

options:
  -h, --help            show this help message and exit
  -i, --input-csv INPUT_CSV
                        Путь к промежуточному CSV файлу с исходными данными (по умолчанию: <имя>_original.csv)
  -j, --json-output JSON_OUTPUT
                        Путь к промежуточному JSON файлу с пидами для TorquePro (по умолчанию: <имя>_transformed.json)
  -o, --output-csv OUTPUT_CSV
                        Путь к выходному CSV файлу с преобразованными пидами для TorquePro (по умолчанию: <имя>.csv)
  -v, --verbose         Подробный вывод информации
  -d, --debug           Сохранять файлы промежуточных преобразований

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
