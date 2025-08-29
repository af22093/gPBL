# 🌊 FloodGuard 3000 🚨

「洪水？知らんけど、スプレッドシートに聞いてみよ！」

---

## 🧐 これは何？

並木さんに捧げる愛の歌  
このリポジトリにある Python スクリプトは、**河川の水位を Google スプレッドシートから取得 → AI（Gemini）に投げて → 洪水の危険度と住民の取るべき行動を出力**する、まるで「河川版ドクターX」みたいなシステムです。  
そう、つまり **「洪水占いマシーン」** 💧🔮

---

## ⚙️ どう動くの？

### 1) Google Sheets とお友達になる
- `credentials.json` を用意して OAuth 認証。  
- シート名 **`floodsheet`** からデータを取得。

### 2) 最新データを分析
- 列: `timestamp`, `temperture`（←なぜかスペルミス）, `humidity`, `waterlevel` を **Pandas** で解析。  
- 「今の水位」と「15分前の水位」を比較して、上昇ペースを計算。

### 3) Gemini に質問する
- 例: 「**このペースで水位が上がったらヤバい？**」  
- **JSON** で「洪水確率」「氾濫までの時間」「住民が今すぐやるべき3つのこと」が返ってくる。

### 4) 結果を発表
- 端末に **防災無線っぽいアナウンス** を表示。

---

## 📦 必要なもの

- Python **3.x**
- **Pandas**
- **Google API** 関連ライブラリ
- `credentials.json`（Google Cloud から DL）
- **Gemini API キー**（←ここで未来を占う🔑）
- **スプレッドシート ID**（←ここで過去を振り返る📊）

---

## 🚀 使い方

1. このリポジトリをクローン（またはコピペ）  
2. `GEMINI_API_KEY` と `SPREADSHEET_ID` を自分の値に設定  
3. ターミナルで実行

```bash
python flood_guard.py
```

4. 祈る🙏（水位が上がっていませんように…）

---

## 🤖 出力サンプル

```text
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
```

---

## 😂 作者の思い

「洪水予測システム」とか言ってるけど、実際は **Google スプレッドシートと Gemini 頼り**。  
もし Gemini が寝不足だったら、たぶん「**たぶん大丈夫じゃね？**」って返してくる。  
でも、**やらないより100倍マシ**。

---

## ⚠️ 免責事項

このスクリプトを使って家を守れなかった場合、作者は責任を負いません。  
本当に命を守るのは、**自治体からの公式情報** です！  
このスクリプトはあくまで **「お遊び × 実験 × 教材」** です。

---

## ✨ ラストメッセージ

**さあ、君も「未来を読む洪水占い師」になろう！** ✨


---

# 🌊 FloodGuard 3000 🚨 (English)

"Floods? No worries, just ask Google Sheets!"

---

## 🧐 What’s this?

This Python script is basically a **river fortune teller**.  
It grabs river data from Google Sheets, throws it at **Gemini AI**, and Gemini comes back with:

- **Flood probability**  
- **Time left** until your neighborhood becomes Venice  
- **Top 3 actions** residents should do ASAP

Yes, this is literally the **“Doctor X of Flood Forecasting.”** 💧🔮

---

## ⚙️ How does it work?

### 1) Befriends Google Sheets
- Use `credentials.json` for OAuth.
- Pull from the sheet named **`floodsheet`**.

### 2) Analyzes the data
- Columns: `timestamp`, `temperture` (misspelled on purpose 🤷), `humidity`, `waterlevel`.  
- Compare the **latest water level** with the one from **15 minutes ago**.

### 3) Asks Gemini
- Prompt like: “**If this continues, are we in trouble?**”  
- Gemini replies in **JSON** with flood probability, time until danger, and top 3 resident actions.

### 4) Broadcasts the results
- Prints a mini **disaster radio announcement** in your terminal.

---

## 📦 Requirements

- Python **3.x**  
- **Pandas**  
- **Google API libraries**  
- `credentials.json` (from Google Cloud)  
- **Gemini API key** (the crystal ball 🔑)  
- **Spreadsheet ID** (the magic scroll 📜)

---

## 🚀 Usage

1. Clone (or shamelessly copy-paste)  
2. Set `GEMINI_API_KEY` and `SPREADSHEET_ID` with your own values  
3. Run:

```bash
python flood_guard.py
```

4. Cross your fingers 🤞 (and maybe your toes too).

---

## 🤖 Sample Output

```text
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
```

---

## 😂 Author’s Thoughts

Looks fancy, but honestly it’s just **Google Sheets + Gemini cosplay**.  
If Gemini is in a bad mood, it might say: “**Meh, probably fine.**”  
Still, **better than nothing!**

---

## ⚠️ Disclaimer

This tool will **NOT** save your life.  
Always rely on **official government alerts** for real emergencies.  
This project is for **fun, learning, and AI fortune telling** only.

---

## ✨ Final Call

**Become the “Flood Oracle” your neighborhood never asked for.** ✨
