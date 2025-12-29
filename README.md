# 💰 Budget Assistant - יועץ תקציב משפחתי

צ'אטבוט RAG לניהול תקציב משפחתי בישראל, מבוסס על AWS Bedrock Knowledge Base.

## 📋 תוכן עניינים

1. [סקירה כללית](#סקירה-כללית)
2. [ארכיטקטורה](#ארכיטקטורה)
3. [הקמת AWS](#הקמת-aws)
4. [הרצה מקומית](#הרצה-מקומית)
5. [פריסה ב-EC2](#פריסה-ב-ec2)
6. [שימוש](#שימוש)
7. [פתרון בעיות](#פתרון-בעיות)

---

## 📖 סקירה כללית

המערכת היא צ'אטבוט חכם שעונה על שאלות בנושא ניהול תקציב משפחתי בישראל:
- הוצאות טיפוסיות של משפחה
- חיסכון וקרן חירום
- ניהול חובות והלוואות
- מיסים והטבות
- טיפים מעשיים לחיסכון

### טכנולוגיות
- **Backend**: Flask (Python)
- **RAG Engine**: AWS Bedrock Knowledge Base
- **LLM**: Claude (via Bedrock)
- **Vector Store**: OpenSearch Serverless (מנוהל אוטומטית)
- **Storage**: Amazon S3

---

## 🏗️ ארכיטקטורה

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────────┐
│   Browser   │────▶│   Flask     │────▶│  Bedrock Knowledge   │
│   (User)    │◀────│   Backend   │◀────│       Base           │
└─────────────┘     └─────────────┘     └──────────────────────┘
                                                  │
                                        ┌─────────┴─────────┐
                                        │                   │
                                   ┌────▼────┐       ┌──────▼──────┐
                                   │   S3    │       │  OpenSearch │
                                   │ (Docs)  │       │ (Vectors)   │
                                   └─────────┘       └─────────────┘
```

---

## ☁️ הקמת AWS

### שלב 1: יצירת S3 Bucket

1. פתח את [AWS S3 Console](https://s3.console.aws.amazon.com/)
2. לחץ **Create bucket**
3. הגדר:
   - **Bucket name**: `budget-assistant-docs-[your-unique-id]`
   - **Region**: `us-east-1` (או region אחר שתומך ב-Bedrock)
   - **Block all public access**: ✅ (מומלץ)
4. לחץ **Create bucket**

### שלב 2: העלאת מסמכים ל-S3

העלה את קבצי ה-TXT מתיקיית `data/`:
```bash
aws s3 cp data/ s3://budget-assistant-docs-[your-id]/ --recursive
```

או דרך הקונסול:
1. פתח את ה-bucket
2. לחץ **Upload**
3. העלה את כל קבצי ה-`.txt` מתיקיית `data/`

### שלב 3: יצירת IAM Role ל-Bedrock

1. פתח [IAM Console](https://console.aws.amazon.com/iam/)
2. לחץ **Roles** → **Create role**
3. בחר **AWS service** → **Bedrock**
4. הוסף policies:
   - `AmazonBedrockFullAccess`
   - Policy מותאם לגישה ל-S3:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:GetObject",
           "s3:ListBucket"
         ],
         "Resource": [
           "arn:aws:s3:::budget-assistant-docs-*",
           "arn:aws:s3:::budget-assistant-docs-*/*"
         ]
       }
     ]
   }
   ```
5. שם: `BedrockKnowledgeBaseRole`
6. לחץ **Create role**

### שלב 4: הפעלת מודלים ב-Bedrock

1. פתח [Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. לך ל-**Model access** בתפריט השמאלי
3. לחץ **Manage model access**
4. סמן ✅:
   - `Titan Embeddings G1 - Text`
   - `Claude 3 Haiku` (או Sonnet)
5. לחץ **Save changes**
6. המתן לאישור (יכול לקחת כמה דקות)

### שלב 5: יצירת Knowledge Base

1. פתח [Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. לך ל-**Knowledge bases** → **Create knowledge base**
3. **Step 1 - Provide KB details**:
   - **Name**: `budget-assistant-kb`
   - **Description**: `Knowledge base for Israeli family budget management`
   - **IAM role**: בחר `Create and use a new service role` או את ה-role שיצרת
4. **Step 2 - Set up data source**:
   - **Data source name**: `budget-docs`
   - **S3 URI**: `s3://budget-assistant-docs-[your-id]/`
5. **Step 3 - Select embeddings model**:
   - בחר `Titan Embeddings G1 - Text`
6. **Step 4 - Configure vector store**:
   - בחר `Quick create a new vector store`
   - OpenSearch Serverless יווצר אוטומטית
7. **Review and create**

### שלב 6: סנכרון ה-Knowledge Base

1. אחרי היצירה, לחץ על ה-Knowledge Base
2. לחץ **Sync** לסנכרון המסמכים
3. המתן עד שהסטטוס יהיה `Available`

### שלב 7: העתקת ה-Knowledge Base ID

1. ב-Knowledge Base, העתק את ה-**Knowledge base ID**
   - נראה כמו: `ABCD1234XY`
2. שמור אותו - תצטרך אותו לקונפיגורציה

---

## 💻 הרצה מקומית

### דרישות מקדימות
- Python 3.9+
- AWS CLI מוגדר עם credentials

### התקנה

```bash
# Clone או צור את הפרויקט
cd budget-assistant

# יצירת virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# או: venv\Scripts\activate  # Windows

# התקנת dependencies
pip install -r requirements.txt
```

### קונפיגורציה

צור קובץ `.env`:
```bash
cp .env.example .env
```

ערוך את `.env`:
```env
AWS_REGION=us-east-1
KNOWLEDGE_BASE_ID=your-kb-id-here
MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
PORT=8000
```

### הגדרת AWS Credentials

```bash
# Option 1: AWS CLI
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_DEFAULT_REGION=us-east-1
```

### הרצה

```bash
python app.py
```

פתח: http://localhost:8000

---

## 🚀 פריסה ב-EC2

### שלב 1: יצירת EC2 Instance

1. פתח [EC2 Console](https://console.aws.amazon.com/ec2/)
2. לחץ **Launch instance**
3. הגדר:
   - **Name**: `budget-assistant`
   - **AMI**: Amazon Linux 2023 או Ubuntu 22.04
   - **Instance type**: `t2.micro` (מספיק להתחלה)
   - **Key pair**: צור או בחר קיים
   - **Security group**:
     - SSH (port 22) - מה-IP שלך
     - HTTP (port 80) - מכל מקום (או 8000 אם לא משתמשים ב-nginx)
4. לחץ **Launch instance**

### שלב 2: הוספת IAM Role ל-EC2

1. בחר את ה-instance
2. **Actions** → **Security** → **Modify IAM role**
3. צור role חדש או בחר קיים עם:
   - `AmazonBedrockFullAccess`
   - גישה ל-S3

### שלב 3: התחברות והתקנה

```bash
# התחבר ל-EC2
ssh -i your-key.pem ec2-user@your-ec2-ip

# עדכון מערכת
sudo yum update -y  # Amazon Linux
# או: sudo apt update && sudo apt upgrade -y  # Ubuntu

# התקנת Python
sudo yum install python3 python3-pip git -y  # Amazon Linux
# או: sudo apt install python3 python3-pip python3-venv git -y  # Ubuntu

# Clone הפרויקט
git clone https://github.com/your-repo/budget-assistant.git
cd budget-assistant

# Virtual environment
python3 -m venv venv
source venv/bin/activate

# התקנת dependencies
pip install -r requirements.txt
```

### שלב 4: קונפיגורציה

```bash
# צור קובץ .env
cat > .env << EOF
AWS_REGION=us-east-1
KNOWLEDGE_BASE_ID=your-kb-id
MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
PORT=8000
EOF
```

### שלב 5: הרצה עם systemd (מומלץ)

צור service file:
```bash
sudo tee /etc/systemd/system/budget-assistant.service << EOF
[Unit]
Description=Budget Assistant Flask App
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/budget-assistant
Environment="PATH=/home/ec2-user/budget-assistant/venv/bin"
EnvironmentFile=/home/ec2-user/budget-assistant/.env
ExecStart=/home/ec2-user/budget-assistant/venv/bin/python app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# הפעל את השירות
sudo systemctl daemon-reload
sudo systemctl enable budget-assistant
sudo systemctl start budget-assistant

# בדיקת סטטוס
sudo systemctl status budget-assistant
```

### שלב 6: הגדרת Nginx (אופציונלי - לפורט 80)

```bash
sudo yum install nginx -y  # Amazon Linux
# או: sudo apt install nginx -y  # Ubuntu

sudo tee /etc/nginx/conf.d/budget-assistant.conf << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

sudo systemctl enable nginx
sudo systemctl start nginx
```

---

## 📱 שימוש

### ממשק הצ'אט
1. פתח את כתובת השרת בדפדפן
2. הקלד שאלה בעברית
3. קבל תשובה מבוססת על מסמכי הידע

### שאלות לדוגמה
- "כמה כסף צריך בקרן חירום?"
- "מהן ההוצאות הטיפוסיות של משפחה בישראל?"
- "איך לנהל חובות?"
- "מה זה כלל 50/30/20?"
- "כמה קצבת ילדים מקבלים?"

### API Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "knowledge_base_configured": true,
  "knowledge_base_id": "ABCD1234...",
  "model": "anthropic.claude-3-haiku-20240307-v1:0",
  "region": "us-east-1"
}
```

#### Ask Question
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "כמה כסף צריך בקרן חירום?", "k": 5}'
```

Response:
```json
{
  "question": "כמה כסף צריך בקרן חירום?",
  "answer": "ההמלצה המקובלת היא לשמור 3-6 חודשי הוצאות בקרן חירום...",
  "context": ["קטע 1...", "קטע 2..."],
  "top_k": 5
}
```

#### Retrieve Only (ללא יצירת תשובה)
```bash
curl -X POST http://localhost:8000/retrieve \
  -H "Content-Type: application/json" \
  -d '{"question": "חיסכון", "k": 3}'
```

---

## 🔧 פתרון בעיות

### בעיה: "Knowledge Base לא מוגדר"
**פתרון**: ודא שהגדרת את `KNOWLEDGE_BASE_ID` בקובץ `.env`

### בעיה: "AccessDeniedException"
**פתרון**: 
1. ודא שה-IAM Role/User שלך כולל `AmazonBedrockFullAccess`
2. ודא שהמודל הופעל ב-Model Access
3. ודא שיש גישה ל-S3 bucket

### בעיה: "ResourceNotFoundException" עבור Knowledge Base
**פתרון**:
1. ודא שה-Knowledge Base ID נכון
2. ודא שאתה באותו region
3. ודא שה-Knowledge Base במצב `Available`

### בעיה: "Model not found"
**פתרון**:
1. פתח Bedrock Console → Model access
2. ודא שהמודל הרצוי מופעל
3. המתן לאישור

### בעיה: תשובות לא רלוונטיות
**פתרון**:
1. ודא שסנכרנת את ה-Knowledge Base אחרי העלאת מסמכים
2. הגדל את `k` (מספר התוצאות)
3. בדוק את איכות המסמכים שהעלית

### בעיה: השרת לא מגיב ב-EC2
**פתרון**:
1. בדוק שה-Security Group מאפשר תעבורה בפורט הנכון
2. בדוק logs: `sudo journalctl -u budget-assistant -f`
3. ודא שהאפליקציה רצה: `sudo systemctl status budget-assistant`

---

## 📁 מבנה הפרויקט

```
budget-assistant/
├── app.py                 # Flask application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .env                  # Environment variables (לא ב-git)
├── README.md             # Documentation
├── data/                 # Knowledge base documents
│   ├── budget_basics.txt
│   ├── expenses_guide.txt
│   ├── savings_emergency_fund.txt
│   ├── debt_management.txt
│   ├── taxes_benefits.txt
│   └── budgeting_tips.txt
├── templates/            # HTML templates
│   ├── base.html
│   └── index.html
└── static/
    └── css/
        └── main.css      # Styles
```

---

## 🎯 הרחבות אפשריות

- [ ] העלאת מסמכים דרך הממשק
- [ ] היסטוריית שיחות
- [ ] תמיכה ב-Amazon Translate לשפות נוספות
- [ ] תמיכה ב-Amazon Polly להקראת תשובות
- [ ] Dashboard עם סטטיסטיקות שימוש
- [ ] אימות משתמשים
- [ ] Cache לתשובות נפוצות

---

## 📄 רישיון

MIT License
