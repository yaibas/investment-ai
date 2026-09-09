from __future__ import annotations

# Common Japanese listed companies and useful aliases for beginner-friendly selection.
# Users can still enter a Yahoo Finance ticker directly when a name is not in this table.
TICKER_NAMES: dict[str, str] = {
    "トヨタ": "7203.T",
    "トヨタ自動車": "7203.T",
    "ソニー": "6758.T",
    "ソニーグループ": "6758.T",
    "三菱UFJ": "8306.T",
    "三菱UFJフィナンシャル・グループ": "8306.T",
    "三井住友FG": "8316.T",
    "三井住友フィナンシャルグループ": "8316.T",
    "任天堂": "7974.T",
    "ソフトバンクグループ": "9984.T",
    "ソフトバンク": "9434.T",
    "キーエンス": "6861.T",
    "ファーストリテイリング": "9983.T",
    "リクルート": "6098.T",
    "リクルートホールディングス": "6098.T",
    "東京エレクトロン": "8035.T",
    "アドバンテスト": "6857.T",
    "日立": "6501.T",
    "日立製作所": "6501.T",
    "三菱商事": "8058.T",
    "伊藤忠": "8001.T",
    "伊藤忠商事": "8001.T",
    "丸紅": "8002.T",
    "日本郵政": "6178.T",
    "日本電信電話": "9432.T",
    "NTT": "9432.T",
    "KDDI": "9433.T",
    "武田薬品": "4502.T",
    "武田薬品工業": "4502.T",
    "キヤノン": "7751.T",
    "本田技研": "7267.T",
    "ホンダ": "7267.T",
    "日産": "7201.T",
    "日産自動車": "7201.T",
    "任天堂": "7974.T",
    "オリエンタルランド": "4661.T",
    "ZOZO": "3092.T",
    "ニトリ": "9843.T",
    "ファナック": "6954.T",
}

DISPLAY_NAMES = {ticker: name for name, ticker in TICKER_NAMES.items()}
# Prefer longer official-ish names when aliases map to the same ticker.
DISPLAY_NAMES.update(
    {
        "7203.T": "トヨタ自動車",
        "6758.T": "ソニーグループ",
        "8306.T": "三菱UFJフィナンシャル・グループ",
        "8316.T": "三井住友フィナンシャルグループ",
        "7974.T": "任天堂",
        "9984.T": "ソフトバンクグループ",
        "9434.T": "ソフトバンク",
        "6861.T": "キーエンス",
        "9983.T": "ファーストリテイリング",
        "6098.T": "リクルートホールディングス",
        "8035.T": "東京エレクトロン",
        "6857.T": "アドバンテスト",
        "6501.T": "日立製作所",
        "8058.T": "三菱商事",
        "8001.T": "伊藤忠商事",
        "8002.T": "丸紅",
        "6178.T": "日本郵政",
        "9432.T": "日本電信電話",
        "9433.T": "KDDI",
        "4502.T": "武田薬品工業",
        "7751.T": "キヤノン",
        "7267.T": "本田技研工業",
        "7201.T": "日産自動車",
        "4661.T": "オリエンタルランド",
        "3092.T": "ZOZO",
        "9843.T": "ニトリホールディングス",
        "6954.T": "ファナック",
    }
)


def resolve_ticker(value: str) -> str:
    """Resolve a company name, alias, or ticker into a Yahoo Finance ticker."""
    cleaned = " ".join(value.strip().split())
    if not cleaned:
        raise ValueError("銘柄名を入力してください")
    upper = cleaned.upper()
    if upper in DISPLAY_NAMES:
        return upper
    if cleaned in TICKER_NAMES:
        return TICKER_NAMES[cleaned]
    # Also support case-insensitive aliases.
    for name, ticker in TICKER_NAMES.items():
        if name.upper() == upper:
            return ticker
    return upper


def display_name(ticker: str) -> str:
    ticker = ticker.strip().upper()
    return DISPLAY_NAMES.get(ticker, ticker)


def search_names(query: str = "") -> list[tuple[str, str]]:
    q = query.strip().lower()
    pairs = sorted({(name, ticker) for name, ticker in TICKER_NAMES.items()})
    if not q:
        return pairs
    return [(name, ticker) for name, ticker in pairs if q in name.lower()]
