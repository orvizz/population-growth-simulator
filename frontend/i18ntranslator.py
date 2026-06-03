import i18n
from pathlib import Path

SUPPORTED_LANGUAGES = ["en", "es", "ast"]
DEFAULT_LANGUAGE = "en"

i18n.set("file_format", "json")
i18n.set("filename_format", "{locale}.{format}")
i18n.set("skip_locale_root_data", True)
i18n.set("enable_memoization", True)
i18n.set("fallback", DEFAULT_LANGUAGE)
i18n.load_path.append(str(Path(__file__).parent / "locales"))


def get_translator(lang: str):
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE

    def tr(key: str, **kwargs) -> str:
        return i18n.t(key, locale=lang, **kwargs)

    return tr
