from typing import Optional, List
from dataclasses import dataclass
from yargy import Parser, rule, and_, or_, not_
from yargy.pipelines import morph_pipeline
from yargy.predicates import dictionary, is_capitalized, type as yargy_type, gram, normalized
from yargy.interpretation import fact

# 预定义的类别列表
categories = ['science', 'style', 'culture', 'life', 'economics', 'business', 'travel', 'forces', 'media', 'sport']


# 定义数据结构保存提取的实体信息
@dataclass
class Entry:
    names: List[str] = None
    birth_dates: List[str] = None
    birth_places: List[str] = None

    def __post_init__(self):
        self.names = [] if self.names is None else self.names
        self.birth_dates = [] if self.birth_dates is None else self.birth_dates
        self.birth_places = [] if self.birth_places is None else self.birth_places


# 定义命名实体的模式
Name = fact('Name', ['first', 'last'])
Date = fact('Date', ['day', 'month', 'year'])
Place = fact('Place', ['location'])

# 姓名规则
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

# 日期规则
MONTHS = morph_pipeline([
    'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
    'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
])
DATE = rule(
    yargy_type('INT').interpretation(Date.day),
    MONTHS.interpretation(Date.month),
    yargy_type('INT').interpretation(Date.year)
).interpretation(Date)

# 出生地规则
PLACE = rule(
    dictionary({'город', 'село', 'поселок', 'деревня'}),
    is_capitalized().interpretation(Place.location)
).interpretation(Place)

# 增加上下文信息
BIRTH_CONTEXT = or_(
    normalized('родился'),
    normalized('рожден'),
    normalized('родилась'),
    normalized('рождена')
)

# 将 BIRTH_CONTEXT 包装成规则对象
BIRTH_CONTEXT_RULE = rule(BIRTH_CONTEXT)

# 解析器
parser_name = Parser(NAME)
parser_date = Parser(DATE)
parser_place = Parser(PLACE)
parser_birth_context = Parser(BIRTH_CONTEXT_RULE)


# 从段落中提取信息的函数
def extract_data(content):
    entry = Entry()

    # 提取姓名
    name_matches = list(parser_name.findall(content))
    entry.names = [' '.join(_.fact.as_json.values()) for _ in name_matches]

    # 提取出生日期
    date_matches = list(parser_date.findall(content))
    entry.birth_dates = [' '.join(_.fact.as_json.values()) for _ in date_matches]

    # 提取出生地
    place_matches = list(parser_place.findall(content))
    entry.birth_places = [_.fact.location for _ in place_matches]

    # 如果没有提取到信息，尝试结合上下文信息
    if not entry.names or not entry.birth_dates or not entry.birth_places:
        context_content = content.lower()
        birth_context_matches = list(parser_birth_context.findall(context_content))

        if birth_context_matches:
            # 尝试重新提取
            name_matches = list(parser_name.findall(context_content))
            date_matches = list(parser_date.findall(context_content))
            place_matches = list(parser_place.findall(context_content))

            entry.names = [' '.join(_.fact.as_json.values()) for _ in name_matches]
            entry.birth_dates = [' '.join(_.fact.as_json.values()) for _ in date_matches]
            entry.birth_places = [_.fact.location for _ in place_matches]

    return entry


# 逐段读取文件并解析内容
def process_file_paragraphs(file_path):
    entries_with_categories = []
    paragraph_number = 0

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            paragraph_number += 1
            parts = line.strip().split('\t')
            if len(parts) == 3:
                category, title, content = parts
                # 只处理预定义类别的段落
                if category in categories:
                    print(f"Processing paragraph {paragraph_number} from category: {category}")  # 调试信息
                    entry = extract_data(content)
                    entries_with_categories.append((category, entry))

    return entries_with_categories


# 使用您的 txt 文件路径
file_path = r"D:\Projects\Pycharm_projects\NLP\nlp-2024-main\data\news.txt\news.txt"
entries_with_categories = process_file_paragraphs(file_path)

# 保存所有段落的提取结果到一个文件
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

        all_entries_file.write("\n")  # 空行分隔

print(f"All entries have been saved to {output_file_all}")