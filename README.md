<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:166534,50:22c55e,100:0ea5e9&height=190&section=header&text=%F0%9D%95%BF%F0%9D%96%83%F0%9D%95%B2%20Quiz%20Bot&fontSize=48&fontColor=ffffff&fontAlignY=36&desc=Advanced%20Telegram%20Exam%20Engine%20%E2%80%A2%20Rich%20Format%20%E2%80%A2%20HTML%20Exams&descAlignY=58&descSize=16" alt="TXQ Quiz Bot" />

<a href="#-features">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=700&size=22&duration=2600&pause=700&color=22C55E&center=true&vCenter=true&width=760&lines=Rich+markdown+results+%E2%9C%A8;Premium+HTML+exams+%F0%9F%93%9D;Set+Builder+%E2%80%94+split+any+draft+into+sets+%E2%9A%A1;Manual+GitHub+backup+%2B+restore+%F0%9F%92%BE" alt="typing" />
</a>

<p>
<img src="https://img.shields.io/badge/Python-3.11+-166534?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/python--telegram--bot-v21-22c55e?style=for-the-badge&logo=telegram&logoColor=white" />
<img src="https://img.shields.io/badge/Telethon-rich%20format-0ea5e9?style=for-the-badge&logo=telegram&logoColor=white" />
<img src="https://img.shields.io/badge/Deploy-Render-000000?style=for-the-badge&logo=render&logoColor=white" />
</p>

<img src="https://raw.githubusercontent.com/platane/snk/output/github-contribution-grid-snake-dark.svg" width="88%" alt="animated divider" />

</div>

---

## 🚀 Features

<table>
<tr>
<td width="50%" valign="top">

### 🎨 Rich formatting
Native Telegram rich markdown everywhere — headings, **tables**, quotes,
task lists and LaTeX. Results, scoreboards and set reports are all
rendered as rich tables. Needs `API_ID` + `API_HASH`; falls back to HTML
automatically when they are missing.

</td>
<td width="50%" valign="top">

### 🧾 Premium HTML exams
A full offline exam page: fixed timer bar, section drawer, question
palette, deep light/dark themes, MathJax equations, Bengali-safe
rendering and a professional result report with two-column stats and
filterable answer review.

</td>
</tr>
<tr>
<td width="50%" valign="top">

### ❐ Set Builder
Split any draft (e.g. 213 CSV questions) into equal sets of
`20 / 25 / 30 / 35 / 40 / 45 / 50 / 55 / 60 / 70` or a custom number.
The remainder becomes the final set, and every set becomes its own exam
with a serial-numbered practice link.

</td>
<td width="50%" valign="top">

### 💾 Manual GitHub backup
Backups run **only** on `/backupnow` — never automatically. Every
persistent table is included, backups merge with older snapshots, and
`/backups` lists snapshots with one-tap restore.

</td>
</tr>
</table>

<div align="center">

```text
   CSV / TXT / JSON / Forwarded polls
                 │
                 ▼
        ┌──────────────────┐
        │   Draft engine   │──▶ ❐ Set Builder ──▶ Set 1 … Set N
        └──────────────────┘
                 │
     ┌───────────┼─────────────┬────────────────┐
     ▼           ▼             ▼                ▼
  Group exam  Inbox practice  HTML exam    Rich result tables
```

</div>

---

## 🧱 Kept from the base bot

`draft system` · `forwarded quiz poll import` · `CSV import` ·
`group exam start / stop / schedule` · `private practice links` ·
`leaderboard image` · `PDF report delivery` · `admin / owner controls` ·
`file rename + thumbnail utilities`

## 🆕 Added in this package

- **Rich message formatting** in every surface — results, scoreboards, set reports.
- **Result as a table** — personal result, section analysis and question breakdown.
- **Manual-only GitHub backup** with cumulative merge + auto-restore on boot.
- **Set Builder** in the draft edit panel (admin / owner only).
- **Premium HTML exam UI** — deep accents, no A/B/C/D letters, phone + desktop tuned.
- `/richstatus` — owner-only rich/backup diagnostics.

<details>
<summary><b>📜 Previously added</b> (click to expand)</summary>

- `@QuizBot` guided clone workflow
- text / TXT / JSON MCQ import with `✅` answer marking
- smart cleanup of forwarded poll text
- duplicate-question skipping while importing
- draft editing commands: title, timer, negative marking, shuffle, delete question
- sectional draft timing
- group exam controls: pause, resume, skip, slow / fast
- inline query sharing by quiz ID
- creator-info lookup by quiz ID
- improved personal result DM: accuracy, percentage, percentile
- HTML report file sent with the PDF report

</details>

---

## ⚠️ Important limit

Directly fetching another bot's full inline quiz payload from only a pasted
`@QuizBot quiz:XXXX` token is not supported by the Telegram Bot API. So the
clone flow in this build is:

1. `/clonequiz`
2. send the `@QuizBot quiz:XXXX` text
3. the bot creates a new draft
4. forward the actual quiz polls from `@QuizBot` into the bot inbox
5. the bot auto-cleans and auto-adds them to the draft
6. `/cloneend`

This is the most reliable Bot-API-safe approach.

---

## 💬 Commands

<details open>
<summary><b>Private commands</b></summary>

| Command | What it does |
| :--- | :--- |
| `/newexam` | start a new draft |
| `/drafts` | list and open drafts |
| `/importtext` · `/txtquiz` | import MCQs from text / TXT / JSON |
| `/clonequiz` · `/cloneend` | guided @QuizBot clone flow |
| `/draftinfo CODE` | full draft details |
| `/settitle CODE \| New Title` | rename a draft |
| `/settime CODE 30` | seconds per question |
| `/setneg CODE 0.25` | negative marking |
| `/shuffle CODE` | shuffle questions |
| `/delq CODE 3,5-7` | delete questions |
| `/section CODE 1-10 \| Biology \| 30` | define a section |
| `/sections CODE` · `/clearsections CODE` | manage sections |
| `/creator CODE` | creator info |

</details>

<details open>
<summary><b>Group commands</b></summary>

| Command | What it does |
| :--- | :--- |
| `/binddraft CODE` | bind a draft to the group |
| `/starttqex [CODE]` | start the exam |
| `/pauseq` · `/resumeq` · `/skipq` | live controls |
| `/speed slow\|normal\|fast` | question pacing |
| `/stoptqex` | stop and publish results |
| `/examstatus` | current session state |
| `/schedule YYYY-MM-DD HH:MM` | schedule an exam |
| `/listschedules` · `/cancelschedule ID` | manage schedules |

</details>

<details>
<summary><b>Owner commands — backup &amp; stats</b></summary>

| Command | What it does |
| :--- | :--- |
| `/stats` | users, groups, drafts, questions, sessions, DB size, backup status |
| `/backupnow` | force an immediate upload to GitHub |
| `/backups` | list snapshots and restore one |
| `/restorebackup` | pull the latest backup into the live DB |
| `/richstatus` | rich-format diagnostics |

</details>

---

## ☁️ Deploy on Render

```text
1  Create a new Web Service
2  Connect this repo
3  Start file:  advanced_quiz_bot.py
4  Add the env vars from .env.example
5  Deploy 🚀
```

### 💾 Free permanent storage (survives restarts and redeploys)

Render's free tier wipes the disk on every restart, so the SQLite file is lost.
The built-in **GitHub backup engine** serialises the whole database to JSON in a
private repo and restores it on boot — 100% free.

<details>
<summary><b>One-time setup (5 minutes)</b></summary>

1. **Create a private GitHub repo** (e.g. `my-quizbot-backup`) — it can be empty.
2. **Create a fine-grained Personal Access Token**
   - GitHub → Settings → Developer settings → Personal access tokens → Fine-grained
   - Repository access: *Only select repositories* → the backup repo
   - Repository permissions: **Contents → Read and write**
3. **Add these env vars** in Render → your service → Environment:

   | Variable | Value |
   | :--- | :--- |
   | `GITHUB_TOKEN` | `github_pat_…` |
   | `GITHUB_REPO` | `your-username/my-quizbot-backup` |
   | `GITHUB_BRANCH` | `main` *(optional)* |
   | `GITHUB_STATE_PATH` | `data/state.json` *(optional)* |

4. Redeploy, then run `/backupnow` whenever you want a snapshot.

</details>

---

## 🖥️ Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python advanced_quiz_bot.py
```

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0ea5e9,50:22c55e,100:166534&height=120&section=footer" alt="footer" />

<b>𝕿𝖃𝕼</b> — built for serious exams.

</div>
