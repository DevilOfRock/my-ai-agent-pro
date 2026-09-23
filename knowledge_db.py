import chromadb
from sentence_transformers import SentenceTransformer
import uuid

# โหลดโมเดลฝังคำ (Embedding) ที่รองรับภาษาไทยและอังกฤษ
# โมเดลตัวนี้จะโหลดมาทำงานในเครื่องเราครั้งแรกครั้งเดียว ไม่ต้องต่อเน็ต ไม่เสียเงิน!
embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# สร้าง/เชื่อมต่อฐานข้อมูล ChromaDB (ระบบจะสร้างโฟลเดอร์ chroma_data ขึ้นมาเก็บไฟล์อัตโนมัติ)
client = chromadb.PersistentClient(path="./chroma_data")

# สร้างตู้เก็บความรู้ (Collection)
collection = client.get_or_create_collection(name="ai_knowledge_base")

def add_to_knowledge_base(text_data, source_name="user_input"):
    """ฟังก์ชันสำหรับเอาความรู้ใหม่เก็บใส่ตู้ (แปลงเป็นพิกัดตัวเลขแล้วบันทึก)"""
    if not text_data.strip():
        return
    
    doc_id = str(uuid.uuid4())
    vector = embedder.encode(text_data).tolist()
    
    collection.add(
        ids=[doc_id],
        embeddings=[vector],
        documents=[text_data],
        metadatas=[{"source": source_name}]
    )
    print(f"✅ บันทึกความรู้จาก {source_name} ลงสมองระยะยาวเรียบร้อย!")

def search_knowledge_base(query_text, n_results=2):
    """ฟังก์ชันค้นหาความรู้ที่มี 'ความหมาย' ใกล้เคียงกับคำถามมากที่สุด"""
    if collection.count() == 0:
        return ""
    
    query_vector = embedder.encode(query_text).tolist()
    
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=n_results
    )
    
    if results and results['documents'] and results['documents'][0]:
        retrieved_docs = results['documents'][0]
        return "\n\n---\n\n".join(retrieved_docs)
    
    return ""