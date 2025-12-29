# 💰 Budget Assistant - יועץ תקציב משפחתי

צ'אטבוט RAG לניהול תקציב משפחתי בישראל, מבוסס על AWS Bedrock.

**תומך בשני מצבים:**
- 🔍 **RAG Mode** - Knowledge Base עם retrieve_and_generate
- 🤖 **Agent Mode** - Bedrock Agent חכם עם זיכרון שיחה

---

## 📖 סקירה כללית

המערכת היא צ'אטבוט חכם שעונה על שאלות בנושא ניהול תקציב משפחתי בישראל:
- 📊 יסודות ניהול תקציב וכלל 50/30/20
- 🏠 הוצאות טיפוסיות של משפחה בישראל
- 💵 חיסכון וקרן חירום
- 💳 ניהול חובות והלוואות
- 🧾 מיסים, קצבאות והטבות
- 💡 טיפים מעשיים לחיסכון

---

## 🏗️ ארכיטקטורה

### מצב RAG:
```
┌─────────────┐     ┌─────────────┐     ┌──────────────────────┐
│   Browser   │────▶│   NGINX     │────▶│      Flask App       │
│   (User)    │◀────│   (port 80) │◀────│     (port 8000)      │
└─────────────┘     └─────────────┘     └──────────────────────┘
                                                  │
                                                  ▼
                                        ┌──────────────────────┐
                                        │  Bedrock Knowledge   │
                                        │  Base (RAG)          │
                                        └──────────────────────┘
                                                  │
                                        ┌─────────┴─────────┐
                                        ▼                   ▼
                                   ┌─────────┐       ┌─────────────┐
                                   │   S3    │       │  OpenSearch │
                                   │ (Docs)  │       │  (Vectors)  │
                                   └─────────┘       └─────────────┘
```

### מצב Agent:
```
┌─────────────┐     ┌─────────────┐     ┌──────────────────────┐
│   Browser   │────▶│   NGINX     │────▶│      Flask App       │
│   (User)    │◀────│   (port 80) │◀────│     (port 8000)      │
└─────────────┘     └─────────────┘     └──────────────────────┘
                                                  │
                                                  ▼
                                        ┌──────────────────────┐
                                        │   Bedrock Agent      │
                                        │   (AI Agent)         │
                                        └──────────────────────┘
                                                  │
                                                  ▼
                                        ┌──────────────────────┐
                                        │  Knowledge Base      │
                                        └──────────────────────┘
```

---

## 🎛️ השוואת מצבים

| תכונה | RAG Mode | Agent Mode |
|-------|----------|------------|
| **מהירות** | ⚡ מהיר | 🐢 איטי יותר |
| **עלות** | 💵 זול | 💵💵 יקר יותר |
| **זיכרון שיחה** | ❌ אין | ✅ יש (session) |
| **חשיבה מתקדמת** | ❌ | ✅ |
| **כלים (Tools)** | ❌ | ✅ אפשר להוסיף |
| **הגדרה** | פשוט | מורכב יותר |
| **מתאים ל-** | שאלות פשוטות | שיחות מורכבות |

---

## 🛠️ טכנולוגיות

| רכיב | טכנולוגיה |
|------|-----------|
| **Backend** | Flask (Python) + boto3 |
| **Web Server** | NGINX (reverse proxy) |
| **RAG Engine** | AWS Bedrock Knowledge Base |
| **AI Agent** | AWS Bedrock Agent |
| **LLM** | Claude 3.5 Haiku |
| **Embeddings** | Titan Text Embeddings V2 |
| **Vector Store** | OpenSearch Serverless |
| **Storage** | Amazon S3 |
| **Compute** | EC2 (Ubuntu 24.04) |

---

## 📁 מבנה הפרויקט

```
budget-assistant/
├── app.py                 # Flask application (dual mode)
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── README.md             # Documentation
├── data/                 # Knowledge base documents
│   ├── budget_basics.txt
│   ├── expenses_guide.txt
│   ├── savings_emergency_fund.txt
│   ├── debt_management.txt
│   ├── taxes_benefits.txt
│   └── budgeting_tips.txt
├── templates/
│   ├── base.html
│   └── index.html
└── static/
    └── css/
        └── main.css
```

---

## ☁️ הקמת AWS

### משאבים נדרשים

#### למצב RAG:
| משאב | שם | הערות |
|------|----|-------|
| S3 Bucket | `budget-assistant-docs-XXX` | לאחסון מסמכי הידע |
| Knowledge Base | `budget-assistant-kb` | RAG engine |
| EC2 Instance | `t2.micro` (Ubuntu 24.04) | Free Tier |
| IAM Role | `EC2-Bedrock-Role` | הרשאות Bedrock |

#### למצב Agent (בנוסף):
| משאב | שם | הערות |
|------|----|-------|
| Bedrock Agent | `budget-assistant-agent` | AI Agent |
| Agent Alias | `prod` | גרסת production |

### הערכת עלויות

| שירות | עלות משוערת |
|--------|-------------|
| EC2 t2.micro | $0 (Free Tier) |
| S3 | ~$0.01 |
| Bedrock Claude Haiku | ~$0.50-2/חודש |
| OpenSearch Serverless | ⚠️ ~$8-10/חודש |
| **סה"כ** | **~$10-15/חודש** |

> ⚠️ **חשוב**: למחוק את ה-Knowledge Base כשלא בשימוש כדי לעצור חיובי OpenSearch!

---

## 🚀 התקנה מלאה

### שלב 1: Clone הפרויקט

```bash
cd ~
git clone https://github.com/asafAtriis/budget-assistant.git
cd budget-assistant
```

### שלב 2: התקנת Dependencies

```bash
sudo apt update
sudo apt install python3-venv python3-pip nginx -y

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### שלב 3: הגדרת NGINX

```bash
sudo nano /etc/nginx/sites-available/budget-assistant
```

תוכן הקובץ:
```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

הפעלה:
```bash
sudo ln -s /etc/nginx/sites-available/budget-assistant /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### שלב 4: הגדרת Systemd Service

```bash
sudo nano /etc/systemd/system/budget-assistant.service
```

#### למצב RAG:
```ini
[Unit]
Description=Budget Assistant Flask App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/budget-assistant
Environment="PATH=/home/ubuntu/budget-assistant/venv/bin"
Environment="MODE=RAG"
Environment="KNOWLEDGE_BASE_ID=YOUR-KB-ID"
Environment="AWS_REGION=us-east-1"
Environment="MODEL_ID=anthropic.claude-3-5-haiku-20241022-v1:0"
ExecStart=/home/ubuntu/budget-assistant/venv/bin/python app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

#### למצב Agent:
```ini
[Unit]
Description=Budget Assistant Flask App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/budget-assistant
Environment="PATH=/home/ubuntu/budget-assistant/venv/bin"
Environment="MODE=AGENT"
Environment="AGENT_ID=YOUR-AGENT-ID"
Environment="AGENT_ALIAS_ID=YOUR-ALIAS-ID"
Environment="AWS_REGION=us-east-1"
ExecStart=/home/ubuntu/budget-assistant/venv/bin/python app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

הפעלה:
```bash
sudo systemctl daemon-reload
sudo systemctl enable budget-assistant
sudo systemctl start budget-assistant
```

### שלב 5: בדיקת סטטוס

```bash
sudo systemctl status budget-assistant
sudo journalctl -u budget-assistant -f  # לצפייה בלוגים
```

---

## 🎛️ קונפיגורציה

### משתני סביבה

| משתנה | ברירת מחדל | תיאור |
|-------|------------|-------|
| `MODE` | `RAG` | מצב עבודה: `RAG` או `AGENT` |
| `AWS_REGION` | `us-east-1` | AWS Region |
| `KNOWLEDGE_BASE_ID` | - | ID של Knowledge Base (למצב RAG) |
| `MODEL_ID` | `claude-3-5-haiku` | מודל LLM (למצב RAG) |
| `AGENT_ID` | - | ID של Agent (למצב AGENT) |
| `AGENT_ALIAS_ID` | - | Alias ID של Agent (למצב AGENT) |

### דוגמה - הרצה ידנית

#### מצב RAG:
```bash
export MODE=RAG
export KNOWLEDGE_BASE_ID="ABCD1234XY"
export AWS_REGION="us-east-1"
python app.py
```

#### מצב Agent:
```bash
export MODE=AGENT
export AGENT_ID="AGENT123XY"
export AGENT_ALIAS_ID="ALIAS456"
export AWS_REGION="us-east-1"
python app.py
```

---

## 📱 שימוש

### גישה לאפליקציה
```
http://YOUR-EC2-IP
```

### שאלות לדוגמה
- "כמה כסף צריך בקרן חירום?"
- "מה זה כלל 50/30/20?"
- "מהן ההוצאות הטיפוסיות של משפחה בישראל?"
- "איך לנהל חובות והלוואות?"
- "כמה קצבת ילדים מקבלים?"
- "איך לחסוך בהוצאות החודשיות?"

### API Endpoints

| Endpoint | Method | תיאור |
|----------|--------|-------|
| `/` | GET | ממשק הצ'אט |
| `/health` | GET | בדיקת תקינות וקונפיגורציה |
| `/ask` | POST | שליחת שאלה |
| `/retrieve` | POST | שליפת מקורות בלבד (RAG mode) |

### דוגמת API Request

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "מה זה קרן חירום?", "k": 5}'
```

Response:
```json
{
  "question": "מה זה קרן חירום?",
  "answer": "קרן חירום היא סכום כסף נזיל...",
  "context": ["📄 savings: ...", "📄 budget basics: ..."],
  "mode": "RAG"
}
```

---

## 🔧 פקודות שימושיות

```bash
# הפעלה מחדש
sudo systemctl restart budget-assistant

# צפייה בלוגים
sudo journalctl -u budget-assistant -f

# עדכון קוד מ-Git
cd ~/budget-assistant
git pull
sudo systemctl restart budget-assistant

# עצירת השירות
sudo systemctl stop budget-assistant

# בדיקת Health
curl http://localhost:8000/health
```

---

## 🤖 הגדרת Bedrock Agent (למצב Agent)

### שלב 1: יצירת Agent
1. כנס ל-[Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. **Agents** → **Create Agent**
3. הגדר:
   - Name: `budget-assistant-agent`
   - Model: Claude 3.5 Haiku
   - Instructions: (ראה למטה)

### שלב 2: הוספת Instructions
```
אתה יועץ פיננסי מומחה לניהול תקציב משפחתי בישראל.

התפקיד שלך:
- לענות על שאלות בנושא ניהול תקציב משפחתי
- להסביר מושגים פיננסיים בשפה פשוטה
- לתת טיפים מעשיים לחיסכון
- להתייחס לנתונים ספציפיים לישראל

הנחיות:
1. ענה תמיד בעברית
2. השתמש במידע מבסיס הידע
3. תן תשובות מעשיות וישימות
4. היה אמפתי ותומך
```

### שלב 3: חיבור Knowledge Base
1. ב-Agent → **Knowledge bases** → **Add**
2. בחר את `budget-assistant-kb`
3. שמור

### שלב 4: יצירת Alias
1. **Create Alias** → Name: `prod`
2. שמור את ה-Agent ID ו-Alias ID

---

## 🧹 ניקוי משאבים (לחיסכון בעלויות)

```bash
# מחיקת Knowledge Base (עוצר חיוב OpenSearch!)
# Bedrock Console → Knowledge Bases → Delete

# מחיקת Agent
# Bedrock Console → Agents → Delete

# עצירת EC2
aws ec2 stop-instances --instance-ids YOUR-INSTANCE-ID

# מחיקת S3 (אופציונלי)
aws s3 rb s3://budget-assistant-docs-XXX --force
```

---

## 🐛 פתרון בעיות

### "Unable to locate credentials"
```bash
# ודא שיש IAM Role ל-EC2 עם AmazonBedrockFullAccess
# EC2 Console → Instance → Security → Modify IAM role
```

### "Knowledge Base not found"
```bash
# ודא שה-KB ID נכון וב-Region הנכון
curl http://localhost:8000/health
```

### "Agent not responding"
```bash
# בדוק לוגים
sudo journalctl -u budget-assistant -f

# ודא שה-Agent ב-status "Prepared"
```

### מקורות לא מופיעים
```bash
# בדוק retrieve ישירות
curl -X POST http://localhost:8000/retrieve \
  -H "Content-Type: application/json" \
  -d '{"question": "קרן חירום", "k": 5}'
```

---

## 📄 רישיון

MIT License

---

## 👤 מחבר

**Asaf Atriis**

פרויקט במסגרת קורס AWS & AI

---

## 🔗 קישורים

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Bedrock Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)
- [Bedrock Agents](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)