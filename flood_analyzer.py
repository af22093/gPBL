import gspread
import pandas as pd
import google.generativeai as genai
import time
import json
from datetime import datetime, timedelta

# --- 設定項目 (★ここを自分の情報に書き換えてください) ---
# 1. 取得したGoogle Gemini APIキー
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY" 

# 2. ESPがデータを保存しているGoogleスプレッドシートの名前
GOOGLE_SHEET_NAME = "センサーデータ" 
# --- 設定はここまで ---

# 認証情報ファイルの名前
CREDENTIALS_FILE = 'credentials.json'

# Gemini APIのモデルを設定
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5')

def analyze_sheet_data():
    """スプレッドシートにアクセスし、データを分析してLLMへの入力を作成する"""
    try:
        # 認証とスプレッドシートへのアクセス
        gc = gspread.service_account(filename=CREDENTIALS_FILE)
        spreadsheet = gc.open(GOOGLE_SHEET_NAME)
        worksheet = spreadsheet.sheet1
        
        records = worksheet.get_all_records()
        if len(records) < 2:
            print("データが2件未満のため、変化を計算できません。")
            return None

        # Pandas DataFrameに変換して時系列データを扱いやすくする
        df = pd.DataFrame(records)
        
        # スプレッドシートの列名に合わせて、以下のキーを修正してください
        # 例: 'Timestamp', 'Temperature', 'Humidity', 'Water_Level'
        # もし列名が日本語なら df.rename() などで英語に変換すると扱いやすいです
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df = df.sort_values(by='Timestamp', ascending=False).reset_index(drop=True)

        # 最新データと15分前のデータを取得して変化を計算
        latest_data = df.iloc[0]
        fifteen_minutes_ago_time = latest_data['Timestamp'] - timedelta(minutes=15)
        
        previous_data_options = df[df['Timestamp'] <= fifteen_minutes_ago_time]
        if previous_data_options.empty:
            print("15分以上前のデータが見つからないため、比較できません。")
            return None
        
        previous_data = previous_data_options.iloc[0]

        # 単位時間あたりの水位変化を計算
        time_diff_minutes = (latest_data['Timestamp'] - previous_data['Timestamp']).total_seconds() / 60
        level_change = latest_data['Water_Level'] - previous_data['Water_Level']
        
        # 1分あたりの変化量に換算
        change_per_minute = level_change / time_diff_minutes if time_diff_minutes > 0 else 0

        print("\n--- データ分析結果 ---")
        print(f"最新時刻: {latest_data['Timestamp']}")
        print(f"最新水位: {latest_data['Water_Level']:.2f} cm")
        print(f"最新温度: {latest_data['Temperature']:.1f} °C")
        print(f"最新湿度: {latest_data['Humidity']:.1f} %")
        print(f"水位変化率: {change_per_minute:+.2f} cm/分")
        print("--------------------")
        
        # 水位が上昇している場合のみLLMに問い合わせる
        if change_per_minute <= 0.1: # わずかな上昇は無視
            print("水位はほぼ上昇していません。LLMへの問い合わせをスキップします。")
            return None

        return {
            "current_level": latest_data['Water_Level'],
            "change_per_minute": change_per_minute,
            "temperature": latest_data['Temperature'],
            "humidity": latest_data['Humidity']
        }

    except gspread.exceptions.SpreadsheetNotFound:
        print(f"エラー: スプレッドシート '{GOOGLE_SHEET_NAME}' が見つかりません。")
        return None
    except KeyError as e:
        print(f"エラー: スプレッドシートに '{e}' という名前の列が見つかりません。")
        print("列名が 'Timestamp', 'Water_Level', 'Temperature', 'Humidity' になっているか確認してください。")
        return None
    except Exception as e:
        print(f"データ分析中に予期せぬエラーが発生しました: {e}")
        return None

def get_llm_prediction(analysis_data, danger_level_cm=500):
    """分析データを基に、LLMに洪水予測と対処行動を問い合わせる"""
    
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
        
        cleaned_response = response.text.replace("```json", "").replace("```", "").strip()
        prediction = json.loads(cleaned_response)
        return prediction
    except Exception as e:
        print(f"Gemini APIとの通信中にエラーが発生しました: {e}")
        return None

def main():
    """メイン処理ループ"""
    print("洪水予測システムを起動します。15分ごとにスプレッドシートをチェックします。")
    while True:
        analysis_data = analyze_sheet_data()
        
        if analysis_data:
            prediction = get_llm_prediction(analysis_data)
            if prediction:
                print("\n\n---【緊急防災情報】---")
                print(f"発表時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("---------------------------------")
                print(f"■ 洪水発生の危険度")
                print(f"  今後3時間以内の発生確率: {prediction['flood_probability_3hr']}")
                print(f"  氾濫危険水位への到達予測: {prediction['time_to_danger_level']}")
                print("\n■ 住民が取るべき行動")
                for i, action in enumerate(prediction['resident_actions'], 1):
                    print(f"  {i}. {action}")
                print("---------------------------------\n")
        
        print(f"次のチェックまで15分間待機します...(次回チェック時刻: {(datetime.now() + timedelta(minutes=15)).strftime('%H:%M')})")
        time.sleep(900) # 15分 (900秒) 待機

if __name__ == "__main__":
    main()