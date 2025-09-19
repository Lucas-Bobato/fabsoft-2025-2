import unicodedata
import re

def generate_slug(text: str) -> str:
    """
    Gera um slug amigável para URL a partir de uma string de texto.
    Ex: "Stephen Curry" -> "stephen-curry"
        "Dallas Mavericks vs Boston Celtics 2024-03-15" -> "dallas-mavericks-vs-boston-celtics-2024-03-15"
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
        
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    text = re.sub(r'[-\s]+', '-', text)
    return text

def normalize_text(text: str) -> str:
    """
    Normaliza o texto removendo acentos e convertendo para minúsculas.
    Ex: "Luka Dončić" -> "luka doncic"
    """
    if not isinstance(text, str):
        return ""
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn').lower()