import os.path
import json
import pandas as pd
from datetime import datetime, timedelta

# --- Google API関連のライブラリ ---
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Gemini API関連のライブラリ ---
import google.generativeai as genai

# --- 設定項目 (★ここを自分の情報に書き換えてください) ---
# 1. 取得したGoogle Gemini APIキー
GEMINI_API_KEY = "AIzaSyD4XZ3ryFRwzkyADI6DjauCSi-5-04OQWU"  # ★★★ 自分のAPIキーに書き換えてください ★★★

# 2. あなたのスプレッドシートID
# (例: https://docs.google.com/spreadsheets/d/1jIG40N.../edit#gid=0 の "1jIG40N..." の部分)
SPREADSHEET_ID = "1jIG40NngPvfO2dgNEJqTl-rMYu33L3w1b336w1YDcAw" # ★★★ 自分のスプレッドシートIDに書き換えてください ★★★

# 3. データを読み込むシート名と範囲
# (シート名が "floodsheet" で、A列からD列まで読み込む場合)
RANGE_NAME = "floodsheet"
# --- 設定はここまで ---

# Google APIのスコープ (変更不要)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Gemini APIのモデルを設定
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')


# ===== ステップ1: スプレッドシートからデータを取得する関数 (あなたのコードを基に作成) =====
def get_sheet_data():
    """
    あなたのコードを基にした関数。
    Googleスプレッドシートにアクセスし、指定された範囲のデータを取得して返す。
    """
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
        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME)
            .execute()
        )
        values = result.get("values", [])
        
        if not values:
            print("スプレッドシートからデータが見つかりませんでした。")
            return None
        
        # データを返すように変更
        return values

    except HttpError as err:
        print(f"Google Sheets APIでエラーが発生しました: {err}")
        return None
    except FileNotFoundError:
        print("エラー: 'credentials.json' が見つかりません。")
        print("Google CloudからダウンロードしたOAuth 2.0クライアントIDのJSONファイルが必要です。")
        return None


# ===== ステップ2: 取得したデータを分析する関数 =====
def analyze_data(sheet_values):
    """
    スプレッドシートのデータを分析し、最新の状況と変化率を計算する。
    """
    if not sheet_values or len(sheet_values) < 2:
        print("分析するにはデータが2件未満です。")
        return None

    # Pandas DataFrameに変換
    header = sheet_values[0]
    records = sheet_values[1:]
    df = pd.DataFrame(records, columns=header)

    # データ型を変換 (列名はスプレッドシートに合わせてください)
    try:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['temperture'] = pd.to_numeric(df['temperture'])
        df['humidity'] = pd.to_numeric(df['humidity'])
        df['waterlevel'] = pd.to_numeric(df['waterlevel'])
    except (KeyError, TypeError) as e:
        print(f"データ変換中にエラー: {e}")
        print("スプレッドシートの列名が 'timestamp', 'temperture', 'humidity', 'waterlevel' になっているか確認してください。")
        return None

    # タイムスタンプで並び替え
    df = df.sort_values(by='timestamp', ascending=False).reset_index(drop=True)

    # 最新データと15分前のデータを比較
    latest_data = df.iloc[0]
    fifteen_minutes_ago = latest_data['timestamp'] - timedelta(minutes=15)
    
    previous_data_options = df[df['timestamp'] <= fifteen_minutes_ago]
    if previous_data_options.empty:
        print("15分以上前のデータがないため、変化を計算できません。")
        return None
    previous_data = previous_data_options.iloc[0]

    # 水位の変化率を計算 (cm/分)
    time_diff_minutes = (latest_data['timestamp'] - previous_data['timestamp']).total_seconds() / 60
    level_change = latest_data['waterlevel'] - previous_data['waterlevel']
    change_per_minute = level_change / time_diff_minutes if time_diff_minutes > 0 else 0

    print("\n--- データ分析結果 ---")
    print(f"最新時刻: {latest_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"最新水位: {latest_data['waterlevel']:.2f} cm")
    print(f"水位変化率: {change_per_minute:+.2f} cm/分")
    print("--------------------")

    # 水位がほとんど上昇していない場合は、API呼び出しをスキップ
    if change_per_minute < 0.1:
        print("水位は安定しています。Geminiへの問い合わせをスキップします。")
        return None

    return {
        "current_level": latest_data['waterlevel'],
        "change_per_minute": change_per_minute,
        "temperature": latest_data['temperture'],
        "humidity": latest_data['humidity']
    }


# ===== ステップ3: Gemini APIに予測を問い合わせる関数 =====
def get_gemini_prediction(analysis_data, danger_level_cm=500):
    """
    分析データを基に、Geminiに洪水予測と対処行動を問い合わせる。
    """
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
        
        # レスポンスからJSON部分を抽出
        cleaned_response = response.text.replace("```json", "").replace("```", "").strip()
        prediction = json.loads(cleaned_response)
        return prediction
    except Exception as e:
        print(f"Gemini APIとの通信中にエラーが発生しました: {e}")
        return None


# ===== ステップ4: 全体を制御するメインの処理 =====
def main():
    """メイン処理"""
    print("洪水予測システムを起動します。")
    
    # 1. スプレッドシートからデータを取得
    sheet_values = get_sheet_data()
    
    # 2. データを分析
    if sheet_values:
        analysis_results = analyze_data(sheet_values)
        
        # 3. 分析結果に基づき、Geminiに問い合わせ
        if analysis_results:
            prediction = get_gemini_prediction(analysis_results)
            
            # 4. 結果を表示
            if prediction:
                print("\n\n---【緊急防災情報】---")
                print(f"発表時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("---------------------------------")
                print(f"■ 洪水発生の危険度")
                print(f"  今後3時間以内の発生確率: {prediction.get('flood_probability_3hr', 'N/A')}")
                print(f"  氾濫危険水位への到達予測: {prediction.get('time_to_danger_level', 'N/A')}")
                print("\n■ 住民が取るべき行動")
                actions = prediction.get('resident_actions', [])
                if actions:
                    for i, action in enumerate(actions, 1):
                        print(f"  {i}. {action}")
                else:
                    print("  具体的な行動指示はありません。")
                print("---------------------------------\n")

if __name__ == "__main__":
    main()