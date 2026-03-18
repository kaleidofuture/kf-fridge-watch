---
title: kf-fridge-watch
emoji: 🚀
colorFrom: green
colorTo: blue
sdk: streamlit
sdk_version: 1.44.1
app_file: app.py
pinned: false
---

# KF-FridgeWatch

> 冷蔵庫の食材期限を見える化して食品ロスを減らす。

## The Problem

冷蔵庫の食材をうっかり腐らせてしまう。期限が近いものに気づけない。

## How It Works

1. 食材名・購入日・期限日を入力して追加
2. 期限が近い順にソート表示（「あと2日」のような表示）
3. CSV/JSONでエクスポート/インポートしてデータを持ち運び

## Libraries Used

- **Pendulum** — 日付計算と残り日数の算出
- **Humanize** — 人間に分かりやすい時間表現

## Development

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deployment

Hosted on [Hugging Face Spaces](https://huggingface.co/spaces/mitoi/kf-fridge-watch).

---

Part of the [KaleidoFuture AI-Driven Development Research](https://kaleidofuture.com) — proving that everyday problems can be solved with existing libraries, no AI model required.
