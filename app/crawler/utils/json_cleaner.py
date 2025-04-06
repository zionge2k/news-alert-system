import re


def sanitize_js_style_json(raw: str) -> str:
    """
    JavaScript 형식의 JSON-like 문자열을 Python의 json.loads()로 파싱 가능하도록 정리합니다.
    
    주요 기능:
    - BOM(Byte Order Mark) 제거
    - 문자열 양 끝 공백 제거
    - 마지막 항목 뒤에 붙은 잘못된 쉼표(,) 제거
    
    Args:
        raw (str): 서버에서 받은 JavaScript 형식의 JSON-like 문자열
    
    Returns:
        str: 정제된 JSON 문자열
    """
    text = raw.lstrip('\ufeff').strip()
    text = re.sub(r',(\s*[\]}])', r'\1', text)
    return text
