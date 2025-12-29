"""
Budget Assistant - RAG Chatbot using AWS Bedrock Knowledge Base
יועץ תקציב משפחתי - צ'אטבוט מבוסס RAG
"""
import os
import boto3
from flask import Flask, request, jsonify, render_template

# Configuration
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID", "")
MODEL_ID = os.environ.get("MODEL_ID", "anthropic.claude-3-5-haiku-20241022-v1:0")

# System Prompt for the assistant
SYSTEM_PROMPT = """אתה יועץ פיננסי מומחה לניהול תקציב משפחתי בישראל.

## התפקיד שלך:
- לענות על שאלות בנושא ניהול תקציב משפחתי
- להסביר מושגים פיננסיים בשפה פשוטה וברורה
- לתת טיפים מעשיים לחיסכון והתנהלות כלכלית נכונה
- להתייחס לנתונים ספציפיים לישראל (שכר ממוצע, קצבאות, מיסים וכו')

## הנחיות:
1. ענה תמיד בעברית
2. השתמש אך ורק במידע שמופיע בהקשר (context) שניתן לך
3. אם המידע לא מספיק - ציין זאת בכנות
4. תן תשובות מעשיות וישימות
5. השתמש בדוגמאות מספריות כשרלוונטי
6. היה אמפתי ותומך - ניהול כספים יכול להיות מלחיץ

## פורמט תשובה:
- תשובות ברורות ומאורגנות
- פסקאות קצרות
- נקודות עיקריות כשצריך
- סיכום או המלצה בסוף כשרלוונטי"""

# Generation configuration for Claude
GENERATION_CONFIG = {
    "maxTokens": 1024,
    "temperature": 0.7,
    "topP": 0.9,
}

app = Flask(__name__)
_bedrock_agent_runtime = None


def get_bedrock_agent_runtime():
    """Get or create Bedrock Agent Runtime client."""
    global _bedrock_agent_runtime
    if _bedrock_agent_runtime is None:
        _bedrock_agent_runtime = boto3.client(
            "bedrock-agent-runtime", 
            region_name=AWS_REGION
        )
    return _bedrock_agent_runtime


def retrieve_from_knowledge_base(question: str, num_results: int = 5) -> list:
    """Retrieve relevant chunks from Knowledge Base."""
    client = get_bedrock_agent_runtime()
    
    response = client.retrieve(
        knowledgeBaseId=KNOWLEDGE_BASE_ID,
        retrievalQuery={"text": question},
        retrievalConfiguration={
            "vectorSearchConfiguration": {
                "numberOfResults": num_results
            }
        }
    )
    
    contexts = []
    for result in response.get("retrievalResults", []):
        content = result.get("content", {}).get("text", "")
        score = result.get("score", 0)
        location = result.get("location", {}).get("s3Location", {}).get("uri", "")
        
        if content:
            contexts.append({
                "text": content,
                "score": score,
                "source": location.split("/")[-1] if location else "unknown"
            })
    
    return contexts


def generate_answer_with_context(question: str, contexts: list) -> str:
    """Generate answer using Claude with retrieved context."""
    client = get_bedrock_agent_runtime()
    
    # Build context string
    context_parts = []
    for i, ctx in enumerate(contexts, 1):
        context_parts.append(f"[מקור {i}: {ctx['source']}]\n{ctx['text']}")
    
    context_string = "\n\n---\n\n".join(context_parts) if context_parts else "לא נמצא מידע רלוונטי"
    
    # Use retrieve_and_generate with prompt template
    response = client.retrieve_and_generate(
        input={"text": question},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": KNOWLEDGE_BASE_ID,
                "modelArn": f"arn:aws:bedrock:{AWS_REGION}::foundation-model/{MODEL_ID}",
                "retrievalConfiguration": {
                    "vectorSearchConfiguration": {
                        "numberOfResults": len(contexts) if contexts else 5
                    }
                },
                "generationConfiguration": {
                    "promptTemplate": {
                        "textPromptTemplate": f"""{SYSTEM_PROMPT}

## הקשר (מידע רלוונטי מבסיס הידע):
$search_results$

## שאלת המשתמש:
$query$

## התשובה שלך:"""
                    },
                    "inferenceConfig": {
                        "textInferenceConfig": GENERATION_CONFIG
                    }
                }
            }
        }
    )
    
    return response.get("output", {}).get("text", "לא הצלחתי ליצור תשובה")


def query_knowledge_base(question: str, num_results: int = 5) -> dict:
    """Main function to query KB and generate answer."""
    if not KNOWLEDGE_BASE_ID:
        raise ValueError("KNOWLEDGE_BASE_ID not configured")
    
    # Step 1: Retrieve relevant contexts
    contexts = retrieve_from_knowledge_base(question, num_results)
    
    # Step 2: Generate answer with context
    answer = generate_answer_with_context(question, contexts)
    
    # Step 3: Format context for response
    formatted_contexts = []
    for ctx in contexts:
        text = ctx["text"]
        if len(text) > 250:
            text = text[:250] + "..."
        source = ctx["source"].replace(".txt", "").replace("_", " ")
        formatted_contexts.append(f"📄 {source}: {text}")
    
    return {
        "answer": answer,
        "context": formatted_contexts,
        "sources_count": len(contexts)
    }


# ============== Routes ==============

@app.route("/")
def home():
    """Render the chat interface."""
    return render_template("index.html")


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "knowledge_base_configured": bool(KNOWLEDGE_BASE_ID),
        "knowledge_base_id": KNOWLEDGE_BASE_ID[:10] + "..." if KNOWLEDGE_BASE_ID else None,
        "model": MODEL_ID,
        "region": AWS_REGION
    })


@app.route("/ask", methods=["POST"])
def ask():
    """Handle user questions."""
    data = request.get_json(force=True, silent=True) or {}
    question = (data.get("question") or "").strip()
    k = min(int(data.get("k", 5)), 10)  # Max 10 results
    
    if not question:
        return jsonify({"error": "נא לספק שאלה"}), 400
    
    if not KNOWLEDGE_BASE_ID:
        return jsonify({"error": "Knowledge Base לא מוגדר בשרת"}), 500
    
    try:
        result = query_knowledge_base(question, num_results=k)
        return jsonify({
            "question": question,
            "answer": result["answer"],
            "context": result["context"],
            "sources_count": result["sources_count"],
            "top_k": k
        })
    except Exception as e:
        print(f"Error processing question: {e}")
        return jsonify({"error": f"שגיאה בעיבוד השאלה: {str(e)}"}), 500


@app.route("/retrieve", methods=["POST"])
def retrieve_only():
    """Debug endpoint - retrieve without generating."""
    data = request.get_json(force=True, silent=True) or {}
    question = (data.get("question") or "").strip()
    k = min(int(data.get("k", 5)), 10)
    
    if not question:
        return jsonify({"error": "נא לספק שאלה"}), 400
    
    if not KNOWLEDGE_BASE_ID:
        return jsonify({"error": "Knowledge Base לא מוגדר"}), 500
    
    try:
        contexts = retrieve_from_knowledge_base(question, k)
        return jsonify({
            "question": question,
            "results": contexts,
            "count": len(contexts)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============== Main ==============

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Starting Budget Assistant")
    print("=" * 50)
    print(f"📍 Region: {AWS_REGION}")
    print(f"🧠 Model: {MODEL_ID}")
    print(f"📚 Knowledge Base: {KNOWLEDGE_BASE_ID or 'NOT SET!'}")
    print("=" * 50)
    
    if not KNOWLEDGE_BASE_ID:
        print("⚠️  WARNING: KNOWLEDGE_BASE_ID is not set!")
        print("   Set it with: export KNOWLEDGE_BASE_ID=your-kb-id")
    
    app.run(host="0.0.0.0", port=8000, debug=False)