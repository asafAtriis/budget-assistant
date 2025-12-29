"""
Budget Assistant - RAG Chatbot with AWS Bedrock
יועץ תקציב משפחתי - תומך במצב RAG ומצב Agent

Modes:
  - RAG: Uses Knowledge Base directly (retrieve_and_generate)
  - AGENT: Uses Bedrock Agent with Knowledge Base attached
"""
import os
import boto3
from flask import Flask, request, jsonify, render_template

# ============== Configuration ==============

# Mode: "RAG" or "AGENT"
MODE = os.environ.get("MODE", "RAG").upper()

# AWS Configuration
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# RAG Mode Configuration
KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID", "")
MODEL_ID = os.environ.get("MODEL_ID", "anthropic.claude-3-5-haiku-20241022-v1:0")

# Agent Mode Configuration
AGENT_ID = os.environ.get("AGENT_ID", "")
AGENT_ALIAS_ID = os.environ.get("AGENT_ALIAS_ID", "")

# System Prompt (for RAG mode)
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
6. היה אמפתי ותומך"""

GENERATION_CONFIG = {
    "maxTokens": 1024,
    "temperature": 0.7,
    "topP": 0.9,
}

# ============== Flask App ==============

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


# ============== RAG Mode Functions ==============

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


def query_knowledge_base_rag(question: str, num_results: int = 5) -> dict:
    """Query using RAG mode - Knowledge Base with retrieve_and_generate."""
    if not KNOWLEDGE_BASE_ID:
        raise ValueError("KNOWLEDGE_BASE_ID not configured")
    
    client = get_bedrock_agent_runtime()
    
    # First retrieve contexts for display
    contexts = retrieve_from_knowledge_base(question, num_results)
    
    # Generate answer
    response = client.retrieve_and_generate(
        input={"text": question},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": KNOWLEDGE_BASE_ID,
                "modelArn": f"arn:aws:bedrock:{AWS_REGION}::foundation-model/{MODEL_ID}",
                "retrievalConfiguration": {
                    "vectorSearchConfiguration": {
                        "numberOfResults": num_results
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
    
    answer = response.get("output", {}).get("text", "לא הצלחתי ליצור תשובה")
    
    # Format contexts for display
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
        "mode": "RAG"
    }


# ============== Agent Mode Functions ==============

def query_with_agent(question: str, session_id: str = "default") -> dict:
    """Query using Agent mode - Bedrock Agent."""
    if not AGENT_ID or not AGENT_ALIAS_ID:
        raise ValueError("AGENT_ID or AGENT_ALIAS_ID not configured")
    
    client = get_bedrock_agent_runtime()
    
    response = client.invoke_agent(
        agentId=AGENT_ID,
        agentAliasId=AGENT_ALIAS_ID,
        sessionId=session_id,
        inputText=question
    )
    
    # Process the streaming response
    answer = ""
    citations = []
    
    for event in response.get("completion", []):
        if "chunk" in event:
            chunk = event["chunk"]
            if "bytes" in chunk:
                answer += chunk["bytes"].decode("utf-8")
            
            # Extract citations if available
            if "attribution" in chunk:
                for citation in chunk["attribution"].get("citations", []):
                    for ref in citation.get("retrievedReferences", []):
                        content = ref.get("content", {}).get("text", "")
                        location = ref.get("location", {}).get("s3Location", {}).get("uri", "")
                        if content:
                            source = location.split("/")[-1] if location else "מסמך"
                            source = source.replace(".txt", "").replace("_", " ")
                            if len(content) > 250:
                                content = content[:250] + "..."
                            citations.append(f"📄 {source}: {content}")
    
    return {
        "answer": answer,
        "context": citations[:5],
        "mode": "AGENT"
    }


# ============== Main Query Function ==============

def process_question(question: str, num_results: int = 5, session_id: str = "default") -> dict:
    """Process question based on configured mode."""
    if MODE == "AGENT":
        return query_with_agent(question, session_id)
    else:  # Default to RAG
        return query_knowledge_base_rag(question, num_results)


# ============== Routes ==============

@app.route("/")
def home():
    """Render the chat interface."""
    return render_template("index.html")


@app.route("/health")
def health():
    """Health check endpoint."""
    config = {
        "status": "ok",
        "mode": MODE,
        "region": AWS_REGION
    }
    
    if MODE == "AGENT":
        config["agent_configured"] = bool(AGENT_ID and AGENT_ALIAS_ID)
        config["agent_id"] = AGENT_ID[:10] + "..." if AGENT_ID else None
    else:
        config["knowledge_base_configured"] = bool(KNOWLEDGE_BASE_ID)
        config["knowledge_base_id"] = KNOWLEDGE_BASE_ID[:10] + "..." if KNOWLEDGE_BASE_ID else None
        config["model"] = MODEL_ID
    
    return jsonify(config)


@app.route("/ask", methods=["POST"])
def ask():
    """Handle user questions."""
    data = request.get_json(force=True, silent=True) or {}
    question = (data.get("question") or "").strip()
    k = min(int(data.get("k", 5)), 10)
    session_id = data.get("session_id", "default-session")
    
    if not question:
        return jsonify({"error": "נא לספק שאלה"}), 400
    
    # Validate configuration based on mode
    if MODE == "AGENT" and (not AGENT_ID or not AGENT_ALIAS_ID):
        return jsonify({"error": "Agent לא מוגדר בשרת"}), 500
    elif MODE == "RAG" and not KNOWLEDGE_BASE_ID:
        return jsonify({"error": "Knowledge Base לא מוגדר בשרת"}), 500
    
    try:
        result = process_question(question, k, session_id)
        return jsonify({
            "question": question,
            "answer": result["answer"],
            "context": result["context"],
            "mode": result["mode"]
        })
    except Exception as e:
        print(f"Error processing question: {e}")
        return jsonify({"error": f"שגיאה: {str(e)}"}), 500

# ============== Main ==============

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Budget Assistant")
    print("=" * 60)
    print(f"Region: {AWS_REGION}")
    print(f" Mode: {MODE}")
    print("-" * 60)
    
    if MODE == "AGENT":
        print(f" Agent ID: {AGENT_ID or ' NOT SET!'}")
        print(f"  Alias ID: {AGENT_ALIAS_ID or ' NOT SET!'}")
        if not AGENT_ID or not AGENT_ALIAS_ID:
            print("\n  Set Agent variables:")
            print("   export AGENT_ID=your-agent-id")
            print("   export AGENT_ALIAS_ID=your-alias-id")
    else:
        print(f" Knowledge Base: {KNOWLEDGE_BASE_ID or ' NOT SET!'}")
        print(f" Model: {MODEL_ID}")
        if not KNOWLEDGE_BASE_ID:
            print("\n  Set Knowledge Base variable:")
            print("   export KNOWLEDGE_BASE_ID=your-kb-id")
    
    print("=" * 60)
    app.run(host="0.0.0.0", port=8000, debug=False)