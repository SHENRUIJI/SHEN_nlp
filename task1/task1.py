from typing import Optional, List
from dataclasses import dataclass
from yargy import Parser, rule, and_, or_, not_
from yargy.pipelines import morph_pipeline
from yargy.predicates import dictionary, is_capitalized, type as yargy_type, gram, normalized
from yargy.interpretation import fact

# Предопределенный список категорий
categories = ['science', 'style', 'culture', 'life', 'economics', 'business', 'travel', 'forces', 'media', 'sport']

# Класс для хранения извлеченной информации
@dataclass
class Entry:
    names: List[str] = None  # Имена
    birth_dates: List[str] = None  # Даты рождения
    birth_places: List[str] = None  # Места рождения

    def __post_init__(self):
        self.names = [] if self.names is None else self.names
        self.birth_dates = [] if self.birth_dates is None else self.birth_dates
        self.birth_places = [] if self.birth_places is None else self.birth_places

# Определение структуры имен, дат и мест
Name = fact('Name', ['first', 'last'])
Date = fact('Date', ['day', 'month', 'year'])
Place = fact('Place', ['location'])

# Правило для распознавания имени
NAME = rule(
    and_(
        is_capitalized(),
        or_(gram('Name'), gram('Surn'))  # Убедиться, что это имя или фамилия
    ).interpretation(Name.first),
    and_(
        is_capitalized(),
        or_(gram('Name'), gram('Surn'))  # Убедиться, что это имя или фамилия
    ).interpretation(Name.last)
).interpretation(Name)

# Правило для распознавания даты
MONTHS = morph_pipeline([
    'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
    'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
])
DATE = rule(
    yargy_type('INT').interpretation(Date.day),
    MONTHS.interpretation(Date.month),
    yargy_type('INT').interpretation(Date.year)
).interpretation(Date)

# Правило для распознавания места рождения
PLACE = rule(
    dictionary({'город', 'село', 'поселок', 'деревня'}),
    is_capitalized().interpretation(Place.location)
).interpretation(Place)

# Контекст для определения информации о рождении
BIRTH_CONTEXT = or_(
    normalized('родился'),
    normalized('рожден'),
    normalized('родилась'),
    normalized('рождена')
)

BIRTH_CONTEXT_RULE = rule(BIRTH_CONTEXT)

# Парсеры для различных типов данных
parser_name = Parser(NAME)
parser_date = Parser(DATE)
parser_place = Parser(PLACE)
parser_birth_context = Parser(BIRTH_CONTEXT_RULE)

# Функция для извлечения информации из параграфа
def extract_data(content):
    entry = Entry()

    name_matches = list(parser_name.findall(content))
    entry.names = [' '.join(_.fact.as_json.values()) for _ in name_matches]

    date_matches = list(parser_date.findall(content))
    entry.birth_dates = [' '.join(_.fact.as_json.values()) for _ in date_matches]

    place_matches = list(parser_place.findall(content))
    entry.birth_places = [_.fact.location for _ in place_matches]

    if not entry.names or not entry.birth_dates or not entry.birth_places:
        context_content = content.lower()
        birth_context_matches = list(parser_birth_context.findall(context_content))

        if birth_context_matches:
            name_matches = list(parser_name.findall(context_content))
            date_matches = list(parser_date.findall(context_content))
            place_matches = list(parser_place.findall(context_content))

            entry.names = [' '.join(_.fact.as_json.values()) for _ in name_matches]
            entry.birth_dates = [' '.join(_.fact.as_json.values()) for _ in date_matches]
            entry.birth_places = [_.fact.location for _ in place_matches]

    return entry

# Функция для чтения файла построчно и обработки его содержимого
def process_file_paragraphs(file_path):
    entries_with_categories = []
    paragraph_number = 0

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            paragraph_number += 1
            parts = line.strip().split('\t')
            if len(parts) == 3:
                category, title, content = parts
                if category in categories:
                    print(f"Обработка параграфа {paragraph_number} из категории: {category}")
                    entry = extract_data(content)
                    entries_with_categories.append((category, entry))

    return entries_with_categories

# Путь к файлу
file_path = r"D:\Projects\Pycharm_projects\NLP\nlp-2024-main\data\news.txt\news.txt"
entries_with_categories = process_file_paragraphs(file_path)

# Сохранение результатов в файл
output_file_all = 'Results.txt'
with open(output_file_all, 'w', encoding='utf-8') as all_entries_file:
    for i, (category, entry) in enumerate(entries_with_categories, 1):
        all_entries_file.write(f"Параграф {i} извлеченные данные (Категория: {category}):\n")
        if entry.names:
            all_entries_file.write(f"Имена: {', '.join(entry.names)}\n")
        else:
            all_entries_file.write("Имена: нет\n")

        if entry.birth_dates:
            all_entries_file.write(f"Дата рождения: {', '.join(entry.birth_dates)}\n")
        else:
            all_entries_file.write("Дата рождения: нет\n")

        if entry.birth_places:
            all_entries_file.write(f"Место рождения: {', '.join(entry.birth_places)}\n")
        else:
            all_entries_file.write("Место рождения: нет\n")

        all_entries_file.write("\n") 

print(f"Все записи сохранены в файл {output_file_all}")
