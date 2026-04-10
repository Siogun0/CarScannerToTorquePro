# CarScannerToTorquePro
Converter PID from CarScanner CSP format to TorquePro CSV format

Преобразование CSP файла с PID параметрами для CareScanner в CSV для TorquePro
``` 
positional arguments:  
  input_file            Путь к входному CSP файлу с пидами для CarScanner

options:  
  -h, --help            show help message and exit
  -i, --input-csv INPUT_CSV
                        Путь к промежуточному CSV файлу с исходными данными (по умолчанию: <имя>_original.csv)
  -j, --json-output JSON_OUTPUT
                        Путь к промежуточному JSON файлу с пидами для TorquePro (по умолчанию: <имя>_transformed.json)
  -o, --output-csv OUTPUT_CSV
                        Путь к выходному CSV файлу с преобразованными пидами для TorquePro (по умолчанию: <имя>.csv)
  -v, --verbose         Подробный вывод информации
  -d, --debug           Сохранять файлы промежуточных преобразований
  -op, --optimize       Оптимизировать. (удаляет настройку FlowControl для сообщений в один фрейм)
```
Примеры использования:  
**Базовое использование (все файлы создаются автоматически)**  
  `python script.py custompids.csp`

 
**С оптимизацией команд пред и пост диагностики. (*Пока рекомендуемый. С полным набором Торк как-то тупит*)**  
  `python script.py custompids.csp -op`


