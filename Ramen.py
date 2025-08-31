import os.path
import json
import pandas as pd
from datetime import datetime, timedelta

# --- Google API libraries ---
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Gemini API libraries ---
import google.generativeai as genai

# --- Settings (★ replace with your own values) ---
# 1) Google Gemini API key
#    For security, it’s recommended to read from an environment variable instead of hard-coding
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyD4XZ3ryFRwzkyADI6DjauCSi-5-04OQWU"  # ★★★ Replace with your API key ★★★

# 2) Your Google Spreadsheet ID
SPREADSHEET_ID = "1jIG40NngPvfO2dgNEJqTl-rMYu33L3w1b336w1YDcAw"  # ★★★ Replace with your Spreadsheet ID ★★★

# 3) Sheet name / range to read
#    e.g., "Sheet1", "DATA", or a range like "DATA!A:D"
RANGE_NAME = "DATA"
# --- End of settings ---

# Google API scope (no change needed)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Configure Gemini model
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')


def get_sheet_data():
    """Fetch data from the Google Spreadsheet and return it."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("sheets", "v4", credentials=creds)
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME
        ).execute()
        values = result.get("values", [])
        if not values:
            print("スプレッドシートからデータが見つかりませんでした。")
            return None
        return values
    except HttpError as err:
        print(f"Google Sheets APIでエラーが発生しました: {err}")
        return None
    except FileNotFoundError:
        print("エラー: 'credentials.json' が見つかりません。")
        return None


def _build_df(sheet_values):
    """Normalize header name variations (case/aliases) and build a DataFrame."""
    header = sheet_values[0]
    records = sheet_values[1:]
    df = pd.DataFrame(records, columns=header)

    column_aliases = {
        "timestamp": ("timestamp", "time", "date", "datetime"),
        "temperature": ("temperature", "temperture", "temp"),  # absorb the misspelling "temperture"
        "humidity": ("humidity", "humid"),
        "waterlevel": ("waterlevel", "water_level", "level"),
    }

    final_df = pd.DataFrame()
    found_columns = {}

    for target_name, aliases in column_aliases.items():
        found = False
        for actual_col in df.columns:
            normalized_actual = actual_col.strip().lower().replace("_", "")
            if normalized_actual in aliases:
                if actual_col not in found_columns:
                    final_df[target_name] = df[actual_col]
                    found_columns[actual_col] = target_name
                    found = True
                    break
        if not found:
            raise KeyError(f"必須列 '{target_name}' またはその別名が見つかりません。")
            
    return final_df


def analyze_data(sheet_values):
    """Compute the latest status and the rate of change vs. past data."""
    if not sheet_values or len(sheet_values) < 2:
        print("分析するにはデータが2件未満です。")
        return None

    try:
        df = _build_df(sheet_values)
    except KeyError as e:
        print(f"データ構築中にエラー: {e}")
        return None

    # --- Type conversions ---
    # timestamp: convert various string/number formats to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce', utc=True).dt.tz_convert(None)
    # Others: convert to numeric; invalid values become NaN
    for col in ["temperature", "humidity", "waterlevel"]:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop rows containing invalid values
    df.dropna(inplace=True)
    if len(df) < 2:
        print("有効なデータが2行未満です（欠損や形式不一致の可能性）。")
        return None

    # Sort by timestamp (newest first)
    df.sort_values(by="timestamp", ascending=False, inplace=True)
    df.reset_index(drop=True, inplace=True)

    latest = df.iloc[0]
    
    # ★★★ To change the comparison window for testing, modify 'minutes=2' below ★★★
    # Example: compare with 1 minute earlier -> timedelta(minutes=1)
    cutoff = latest["timestamp"] - timedelta(minutes=2)
    
    prev_candidates = df[df["timestamp"] <= cutoff]

    if prev_candidates.empty:
        print(f"比較対象となる{2}分以上前のデータがないため、変化を計算できません。")
        return None

    prev = prev_candidates.iloc[0]

    # Calculate rate of change (cm/min)
    dt_min = (latest["timestamp"] - prev["timestamp"]).total_seconds() / 60
    dlvl = latest["waterlevel"] - prev["waterlevel"]
    d_per_min = dlvl / dt_min if dt_min > 0 else 0.0

    print("\n--- データ分析結果 ---")
    print(f"最新時刻: {latest['timestamp']:%Y-%m-%d %H:%M:%S}")
    print(f"最新水位: {latest['waterlevel']:.2f} cm")
    print(f"水位変化率: {d_per_min:+.2f} cm/分")
    print("--------------------")

    # Skip Gemini call if the rise is minimal
    if d_per_min < 0.1:
        print("水位は安定しています。Geminiへの問い合わせをスキップします。")
        return None

    return {
        "current_level": float(latest["waterlevel"]),
        "change_per_minute": float(d_per_min),
        "temperature": float(latest["temperature"]),
        "humidity": float(latest["humidity"]),
    }


def get_gemini_prediction(analysis_data, danger_level_cm=500):
    """Query Gemini for flood prediction and recommended actions."""
    prompt = f"""
あなたは経験豊富な河川防災のエキスパートです。提供されたリアルタイムの河川データに基づき、洪水の危険性を分析し、地域住民が取るべき具体的な行動を冷静かつ的確に指示してください。

# リアルタイム河川データ
- 現在の水位: {analysis_data['current_level']:.2f} cm
- 水位の変動率: {analysis_data['change_per_minute']:.2f} cm/分 (プラスは上昇)
- 周辺の気温: {analysis_data['temperature']:.1f} °C
- 周辺の湿度: {analysis_data['humidity']:.1f} %
- 氾濫危険水位 (想定): {danger_level_cm} cm

# 指示
上記のデータを専門家の視点で分析し、以下の項目を含むJSONオブジェクトを生成してください。

1.  **flood_probability_3hr**: 今後3時間以内に氾濫危険水位に到達する確率を、具体的なパーセンテージで示してください。(例: "60%")
2.  **time_to_danger_level**: 現在の水位上昇ペースが続いた場合、氾濫危険水位に到達するまでの予測時間を算出してください。(例: "約1時間45分後")
3.  **resident_actions**: 住民が今すぐ取るべき最も重要な行動を、危険レベルに応じて3つ、優先順位の高い順にリスト形式で記述してください。簡潔かつ具体的な指示にしてください。

# 出力形式 (JSONのみを厳守)
{{
  "flood_probability_3hr": "（計算した確率）",
  "time_to_danger_level": "（計算した予測時間）",
  "resident_actions": [
    "（最優先の行動）",
    "（次に取るべき行動）",
    "（準備すべきこと）"
  ]
}}
"""
    try:
        print("\nGemini APIに洪水予測を問い合わせています...")
        response = model.generate_content(prompt)
        cleaned = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
    except Exception as e:
        print(f"Gemini APIとの通信中にエラーが発生しました: {e}")
        return None


def main():
    """Main routine."""
    print("洪水予測システムを起動します。")
    sheet_values = get_sheet_data()
    if sheet_values:
        analysis = analyze_data(sheet_values)
        if analysis:
            prediction = get_gemini_prediction(analysis)
            if prediction:
                print("\n\n---【緊急防災情報】---")
                print(f"発表時刻: {datetime.now():%Y-%m-%d %H:%M:%S}")
                print("---------------------------------")
                print("■ 洪水発生の危険度")
                print(f"  今後3時間以内の発生確率: {prediction.get('flood_probability_3hr', 'N/A')}")
                print(f"  氾濫危険水位への到達予測: {prediction.get('time_to_danger_level', 'N/A')}")
                print("\n■ 住民が取るべき行動")
                actions = prediction.get('resident_actions', [])
                if actions:
                    for i, a in enumerate(actions, 1):
                        print(f"  {i}. {a}")
                else:
                    print("  具体的な行動指示はありません。")
                print("---------------------------------\n")


if __name__ == "__main__":
    main()
