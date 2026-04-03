import re 

class DocumentChunker:
    def __init__(self, size=500, overlap=50):
        self.size = size
        self.overlap = overlap

    def chunk(self, text):
        if not text:
            return []

        if '\n\n' in text or re.search(r'\n\s*\n', text):
            return self.dynamic_chunking(text)
        else:
            return self.static_chunking(text)

        

    def dynamic_chunking(self, text):

        chunks = []
        chunk=''
        paragraphs = re.split(r'\n\s*\n', text)

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue


            if len(chunk) + len(paragraph) <= self.size:
                chunk = chunk + paragraph + "\n\n"
            else:
                if chunk:
                    chunks.append(chunk.strip())
                chunk = paragraph + "\n\n"

        if chunk:
            chunks.append(chunk.strip())
        
        final_chunks = []

        for i in chunks:
            if len(i) > self.size:
                final_chunks.extend(self.static_chunking(i))
            else:
                final_chunks.append(i)
        return final_chunks
            
    
    def static_chunking(self, text):

        chunks = []
        words = text.split()

        i=0

        while i < len(words):
            chunk = " ".join(words[i:i+self.size])
            chunks.append(chunk)
            i += self.size - self.overlap
        return chunks