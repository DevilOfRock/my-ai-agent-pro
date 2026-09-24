import chromadb
from sentence_transformers import SentenceTransformer
import uuid

# โหลดโมเดลฝังคำ (Embedding) ที่รองรับภาษาไทยและอังกฤษ
# โมเดลตัวนี้จะโหลดมาทำงานในเครื่องเราครั้งแรกครั้งเดียว ไม่ต้องต่อเน็ต ไม่เสียเงิน!
embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# 🟢 แก้ชื่อโฟลเดอร์เป็น ai_memory เพื่อบังคับให้ Cloud สร้างตู้ใหม่ที่เขียนข้อมูลได้ 🟢
client = chromadb.PersistentClient(path="./ai_memory")

def get_collection():
    """ฟังก์ชันช่วยดึงหรือสร้าง Collection ใหม่ทุกครั้ง ป้องกันปัญหาขยะตกค้างบน Cloud"""
    return client.get_or_create_collection(name="ai_knowledge_base")

def add_to_knowledge_base(text_data, source_name="user_input"):
    """ฟังก์ชันสำหรับเอาความรู้ใหม่เก็บใส่ตู้ (แปลงเป็นพิกัดตัวเลขแล้วบันทึก)"""
    if not text_data.strip():
        return
    
    # 🟢 เรียกใช้ผ่านฟังก์ชัน เพื่อให้มันสร้างใหม่ทันทีถ้าหาตู้เดิมไม่เจอ
    collection = get_collection()
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
    # 🟢 เรียกใช้ผ่านฟังก์ชัน เพื่อให้มั่นใจว่าตู้ความจำมีอยู่จริง
    collection = get_collection()
    
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