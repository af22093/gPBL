🌊 FloodGuard 3000 🚨

「洪水？知らんけど、スプレッドシートに聞いてみよ！」

🧐 これは何？

このリポジトリにあるPythonスクリプトは、河川の水位をGoogleスプレッドシートから取得 → AI（Gemini）に投げて → 洪水の危険度と住民の取るべき行動を教えてくれるという、まるで「河川版ドクターX」みたいなシステムです。
そう、つまり「洪水占いマシーン」💧🔮

⚙️ どう動くの？

Google Sheetsとお友達になる

credentials.json を用意してOAuth認証。

「floodsheet」という名前のシートからデータをゴソッと持ってきます。

最新データを分析

timestamp, temperture（←なぜかスペルミス）、humidity, waterlevel の列をPandasで解析。

「今の水位」と「15分前の水位」を比較して、どれくらい増えてるかを計算。

Geminiに質問する

「このペースで水位が上がったらヤバい？」と聞く。

するとGeminiはJSON形式で「洪水確率」「氾濫までの時間」「住民が今すぐやるべき3つのこと」を返してくれる。

結果を発表

「洪水確率60%！ 2時間後に氾濫の可能性！ 住民はすぐに避難準備！」みたいに表示してくれる。

ちょっと防災無線っぽい。

📦 必要なもの

Python 3.x

Pandas

Google API関連ライブラリ

credentials.json（Google CloudからDL）

そして最も重要な…

Gemini APIキー（←ここで未来を占う🔑）

スプレッドシートID（←ここで過去を振り返る📊）

🚀 使い方

このリポジトリをクローン（またはコピー＆ペースト）

GEMINI_API_KEY と SPREADSHEET_ID を自分の値に書き換える

ターミナルで実行

python flood_guard.py


祈る🙏（水位が上がってませんように…）

🤖 出力サンプル
---【緊急防災情報】---
発表時刻: 2025-08-29 17:00:00
---------------------------------
■ 洪水発生の危険度
  今後3時間以内の発生確率: 65%
  氾濫危険水位への到達予測: 約2時間30分後

■ 住民が取るべき行動
  1. 貴重品と非常食を持って避難準備
  2. ご近所に声をかけて情報共有
  3. ラジオや公式アプリで最新情報をチェック
---------------------------------

😂 作者の思い

「洪水予測システム」とか言ってるけど、実際はGoogleスプレッドシートとGemini頼り。

もしGeminiが寝不足だったら、たぶん「たぶん大丈夫じゃね？」って返してくる。

でも、やらないより100倍マシ。

⚠️ 免責事項

このスクリプトを使って家を守れなかった場合、作者は責任を負いません。
本当に命を守るのは、自治体からの公式情報です！
このスクリプトはあくまで「お遊び × 実験 × 教材」です。

✨さあ、君も「未来を読む洪水占い師」になろう！✨

🌊 FloodGuard 3000 🚨

"Floods? No worries, just ask Google Sheets!"

🧐 What’s this?

This Python script is basically a river fortune teller.
It grabs river data from Google Sheets, throws it at Gemini AI, and then Gemini comes back with:

Flood probability

Time left until your neighborhood becomes Venice

And what residents should do ASAP

Yes, this is literally the “Doctor X of Flood Forecasting.” 💧🔮

⚙️ How does it work?

Befriends Google Sheets

Uses credentials.json for OAuth.

Pulls data from the sheet called "floodsheet".

Analyzes the data

Looks at timestamp, temperture (yes, misspelled on purpose 🤷), humidity, waterlevel.

Compares the latest water level with the one from 15 minutes ago.

Asks Gemini

Like: “Hey, if this continues, are we screwed?”

Gemini replies in JSON with flood probability, time until danger, and top 3 resident actions.

Broadcasts the results

Prints a mini “disaster radio announcement” in your terminal.

📦 Requirements

Python 3.x

Pandas

Google API libraries

credentials.json (from Google Cloud)

And most importantly…

Gemini API key (the crystal ball 🔑)

Spreadsheet ID (the magic scroll 📜)

🚀 Usage

Clone (or copy-paste like a pro)

Edit GEMINI_API_KEY and SPREADSHEET_ID with your own values

Run it:

python flood_guard.py


Cross your fingers 🤞 (and maybe your toes too).

🤖 Sample Output
---【Emergency Flood Alert】---
Issued at: 2025-08-29 17:00:00
---------------------------------
■ Flood Risk
  Probability within 3 hours: 65%
  Time until danger level: ~2 hours 30 minutes

■ Resident Actions
  1. Grab valuables + food and prepare to evacuate
  2. Warn your neighbors
  3. Keep checking radio/official apps for updates
---------------------------------

😂 Author’s Thoughts

This system looks fancy, but honestly it’s just Google Sheets + Gemini cosplay.

If Gemini is in a bad mood, it might just say: “Meh, probably fine.”

Still, better than nothing!

⚠️ Disclaimer

This tool will NOT save your life.
Always rely on official government alerts for real emergencies.
This project is for fun, learning, and playing “AI fortune teller” only.

✨ Become the “Flood Oracle” your neighborhood never asked for ✨