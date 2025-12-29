# 💰 Budget Assistant - יועץ תקציב משפחתי

צ'אטבוט RAG לניהול תקציב משפחתי בישראל, מבוסס על AWS Bedrock Knowledge Base.

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

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────────┐
│   Browser   │────▶│   NGINX     │────▶│      Flask App       │
│   (User)    │◀────│   (port 80) │◀────│     (port 8000)      │
└─────────────┘     └─────────────┘     └──────────────────────┘
                                                  │
                                                  ▼
                                        ┌──────────────────────┐
                                        │  Bedrock Knowledge   │
                                        │       Base           │
                                        └──────────────────────┘
                                                  │
                                        ┌─────────┴─────────┐
                                        │                   │
                                   ┌────▼────┐       ┌──────▼──────┐
                                   │   S3    │       │  OpenSearch │
                                   │ (Docs)  │       │ (Vectors)   │
                                   └─────────┘       └─────────────┘
```

---

## 🛠️ טכנולוגיות

| רכיב | טכנולוגיה |
|------|-----------|
| **Backend** | Flask (Python) |
| **Web Server** | NGINX (reverse proxy) |
| **RAG Engine** | AWS Bedrock Knowledge Base |
| **LLM** | Claude 3.5 Haiku |
| **Embeddings** | Titan Text Embeddings V2 |
| **Vector Store** | OpenSearch Serverless |
| **Storage** | Amazon S3 |
| **Compute** | EC2 (Ubuntu 24.04) |

---

## 📁 מבנה הפרויקט

```
budget-assistant/
├── app.py                 # Flask application
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

| משאב | שם | הערות |
|------|----|-------|
| S3 Bucket | `budget-assistant-docs-12345` | לאחסון מסמכי הידע |
| Knowledge Base | `budget-assistant-kb` | RAG engine |
| EC2 Instance | `t2.micro` (Ubuntu 24.04) | Free Tier |
| IAM Role | `EC2-Bedrock-Role` | הרשאות Bedrock |
| Security Group | פורטים 22, 80 | SSH + HTTP |

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

## 🚀 התקנה בשרת EC2

### 1. Clone הפרויקט

```bash
cd ~
git clone https://github.com/asafAtriis/budget-assistant.git
cd budget-assistant
```

### 2. התקנת Dependencies

```bash
sudo apt update
sudo apt install python3-venv python3-pip nginx -y

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. הגדרת NGINX

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
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### 4. הגדרת Systemd Service

```bash
sudo nano /etc/systemd/system/budget-assistant.service
```

תוכן:
```ini
[Unit]
Description=Budget Assistant Flask App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/budget-assistant
Environment="PATH=/home/ubuntu/budget-assistant/venv/bin"
Environment="KNOWLEDGE_BASE_ID=YOUR-KB-ID"
Environment="AWS_REGION=us-east-1"
Environment="MODEL_ID=anthropic.claude-3-5-haiku-20241022-v1:0"
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

### 5. בדיקת סטטוס

```bash
sudo systemctl status budget-assistant
sudo journalctl -u budget-assistant -f  # לצפייה בלוגים
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

### API Endpoints

| Endpoint | Method | תיאור |
|----------|--------|-------|
| `/` | GET | ממשק הצ'אט |
| `/health` | GET | בדיקת תקינות |
| `/ask` | POST | שליחת שאלה |

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
```

---

## 🧹 ניקוי משאבים (לחיסכון בעלויות)

```bash
# מחיקת Knowledge Base (עוצר חיוב OpenSearch)
# דרך Bedrock Console → Knowledge Bases → Delete

# עצירת EC2
aws ec2 stop-instances --instance-ids YOUR-INSTANCE-ID

# מחיקת S3 (אופציונלי)
aws s3 rb s3://budget-assistant-docs-12345 --force
```

---

## 📄 רישיון

MIT License

---

## 👤 מחבר

Asaf Atriis

פרויקט במסגרת קורס AWS & AI