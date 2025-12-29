"""
Budget Assistant - RAG Chatbot using AWS Bedrock Knowledge Base
מערכת צ'אטבוט לניהול תקציב משפחתי בישראל
"""
import os
import boto3
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------------------------
# Configuration
# ---------------------------
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID", "")  # Your KB ID from Bedrock
MODEL_ID = os.environ.get("MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")  # Or claude-3-sonnet

# ---------------------------
# Flask App
# ---------------------------
app = Flask(__name__)

# ---------------------------
# AWS Clients (lazy initialization)
# ---------------------------
_bedrock_agent_runtime = None
_bedrock_runtime = None


def get_bedrock_agent_runtime():
    """Get Bedrock Agent Runtime client for Knowledge Base queries."""
    global _bedrock_agent_runtime
    if _bedrock_agent_runtime is None:
        _bedrock_agent_runtime = boto3.client(
            "bedrock-agent-runtime",
            region_name=AWS_REGION
        )
    return _bedrock_agent_runtime


def get_bedrock_runtime():
    """Get Bedrock Runtime client for direct model invocation."""
    global _bedrock_runtime
    if _bedrock_runtime is None:
        _bedrock_runtime = boto3.client(
            "bedrock-runtime",
            region_name=AWS_REGION
        )
    return _bedrock_runtime


# ---------------------------
# RAG Functions
# ---------------------------
def query_knowledge_base(question: str, num_results: int = 5) -> dict:
    """
    Query the Bedrock Knowledge Base and get a grounded response.
    Uses RetrieveAndGenerate API for RAG in a single call.
    """
    if not KNOWLEDGE_BASE_ID:
        raise ValueError("KNOWLEDGE_BASE_ID environment variable is not set")
    
    client = get_bedrock_agent_runtime()
    
    try:
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
                            "textPromptTemplate": """אתה יועץ פיננסי מומחה לניהול תקציב משפחתי בישראל.
ענה על השאלה בהתבסס על המידע המסופק בלבד.
אם המידע לא מספיק, אמור זאת בכנות.
ענה בעברית בצורה ברורה ומסודרת.

מידע רלוונטי:
$search_results$

שאלה: $query$

תשובה:"""
                        }
                    }
                }
            }
        )
        
        # Extract answer and citations
        answer = response.get("output", {}).get("text", "לא נמצאה תשובה")
        
        # Extract retrieved contexts for transparency
        citations = []
        for citation in response.get("citations", []):
            for ref in citation.get("retrievedReferences", []):
                content = ref.get("content", {}).get("text", "")
                if content:
                    citations.append(content[:200] + "..." if len(content) > 200 else content)
        
        return {
            "answer": answer,
            "context": citations[:5]  # Top 5 contexts
        }
        
    except Exception as e:
        raise RuntimeError(f"Error querying Knowledge Base: {str(e)}")


def retrieve_only(question: str, num_results: int = 5) -> list:
    """
    Retrieve relevant chunks from Knowledge Base without generation.
    Useful for debugging or showing raw context.
    """
    if not KNOWLEDGE_BASE_ID:
        raise ValueError("KNOWLEDGE_BASE_ID environment variable is not set")
    
    client = get_bedrock_agent_runtime()
    
    try:
        response = client.retrieve(
            knowledgeBaseId=KNOWLEDGE_BASE_ID,
            retrievalQuery={"text": question},
            retrievalConfiguration={
                "vectorSearchConfiguration": {
                    "numberOfResults": num_results
                }
            }
        )
        
        results = []
        for result in response.get("retrievalResults", []):
            content = result.get("content", {}).get("text", "")
            score = result.get("score", 0)
            results.append({
                "text": content,
                "score": round(score, 4)
            })
        
        return results
        
    except Exception as e:
        raise RuntimeError(f"Error retrieving from Knowledge Base: {str(e)}")


# ---------------------------
# Routes - Pages
# ---------------------------
@app.route("/")
def home():
    """Render the main chat interface."""
    return render_template("index.html")


# ---------------------------
# Routes - API
# ---------------------------
@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    kb_configured = bool(KNOWLEDGE_BASE_ID)
    return jsonify({
        "status": "ok",
        "knowledge_base_configured": kb_configured,
        "knowledge_base_id": KNOWLEDGE_BASE_ID[:8] + "..." if KNOWLEDGE_BASE_ID else None,
        "model": MODEL_ID,
        "region": AWS_REGION
    })


@app.route("/ask", methods=["POST"])
def ask():
    """
    Main endpoint for asking questions.
    Expects JSON: {"question": "...", "k": 5}
    Returns JSON: {"question": "...", "answer": "...", "context": [...]}
    """
    data = request.get_json(force=True, silent=True) or {}
    question = (data.get("question") or "").strip()
    k = int(data.get("k", 5))
    
    if not question:
        return jsonify({"error": "נא לספק שאלה בשדה 'question'"}), 400
    
    if not KNOWLEDGE_BASE_ID:
        return jsonify({
            "error": "Knowledge Base לא מוגדר. הגדר KNOWLEDGE_BASE_ID ב-environment variables"
        }), 500
    
    try:
        result = query_knowledge_base(question, num_results=k)
        return jsonify({
            "question": question,
            "answer": result["answer"],
            "context": result["context"],
            "top_k": k
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/retrieve", methods=["POST"])
def retrieve():
    """
    Retrieve-only endpoint (without generation).
    Useful for debugging and showing raw chunks.
    """
    data = request.get_json(force=True, silent=True) or {}
    question = (data.get("question") or "").strip()
    k = int(data.get("k", 5))
    
    if not question:
        return jsonify({"error": "נא לספק שאלה בשדה 'question'"}), 400
    
    try:
        results = retrieve_only(question, num_results=k)
        return jsonify({
            "question": question,
            "results": results,
            "count": len(results)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║           💰 Budget Assistant - RAG Chatbot                  ║
║              ניהול תקציב משפחתי בישראל                        ║
╠══════════════════════════════════════════════════════════════╣
║  Region: {AWS_REGION:<50} ║
║  Model: {MODEL_ID:<51} ║
║  KB ID: {(KNOWLEDGE_BASE_ID[:20] + '...') if KNOWLEDGE_BASE_ID else 'NOT SET':<51} ║
║  Port: {port:<52} ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    if not KNOWLEDGE_BASE_ID:
        print("⚠️  WARNING: KNOWLEDGE_BASE_ID is not set!")
        print("   Set it with: export KNOWLEDGE_BASE_ID=your-kb-id")
    
    app.run(host="0.0.0.0", port=port, debug=debug)
