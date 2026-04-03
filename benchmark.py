import time
import os
from retriever import Retriever

def run_benchmark():
    print("="*50)
    print("Starting RAG Evaluation Benchmark...")
    print("="*50)

    
    COHERE_KEY = os.getenv("COHERE_KEY", "")
    PINECONE_KEY = os.getenv("PINECONE_KEY", "")

    if COHERE_KEY == "YOUR_COHERE_KEY":
        print("WARNING: Using placeholder keys. Benchmark will fail if real keys are not provided.")

    try:
        retriever = Retriever(pinecone_key=PINECONE_KEY, cohere_key=COHERE_KEY)
    except Exception as e:
        print(f"Failed to initialize Retriever: {e}")
        return

    test_cases = [
        {
            "question": "ما هو الغرض من استخدام ملفات تعريف الارتباط (Cookies)؟",
            "expected_keyword": "لتسهيل تجربتك"
        },
        {
            "question": "أين يتم تخزين البيانات الشخصية للمستخدمين؟",
            "expected_keyword": "في السعودية" 
        },
        {
            "question": "كيف يمكن التواصل مع مسؤول حماية البيانات الشخصية؟",
            "expected_keyword": "aalolaiwi@misa.gov.sa"
        },
        {
            "question": "ما هي البيانات الحساسة؟",
            "expected_keyword": "أصل الفرد العرقي"
        }
    ]
    
    passed = 0
    total_time = 0
    
    for i, test in enumerate(test_cases, 1):
        start_time = time.time()
        try:
            results = retriever.search(query=test['question'], k=3)
        except Exception as e:
            print(f"Error during search: {e}")
            results = []
            
        latency = time.time() - start_time
        total_time += latency
        
    
        combined_results = " ".join([res.get('text', '') for res in results]) if results else ""
        
        if test['expected_keyword'] in combined_results:
            passed += 1
            print(f"Test [{i}/{len(test_cases)}] PASSED | Latency: {latency:.2f}s")
        else:
            print(f"Test [{i}/{len(test_cases)}] FAILED")

    hit_rate = (passed / len(test_cases)) * 100
    avg_latency = total_time / len(test_cases) if test_cases else 0

    print("="*50)
    print("Benchmark Results:")
    print(f"Hit Rate @ 3: {hit_rate:.1f}%")
    print(f"Average Latency: {avg_latency:.2f} seconds")
    print("="*50)

if __name__ == "__main__":
    run_benchmark()