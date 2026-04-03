import os
import docx
import fitz # PyMuPDF

class DocumentReader:
    def __init__(self):
        self.supported_extensions = ['.docx', '.doc', '.pdf']


    def read(self, file_path):
        if not os.path.exists(file_path):
                raise FileNotFoundError(f'File not found: {file_path}')
            
        file = os.path.splitext(file_path)[1]

        if file == '.pdf':
            return self.read_pdf(file_path)
        elif file == '.docx' or file == '.doc':
            return self.read_docx(file_path)
        elif file == '.txt':
            return self.read_txt(file_path)
        else:
            raise ValueError(f"{file} is not supported")

          

    def read_pdf(self, file_path):

        text = ""

        try:
            with fitz.open(file_path) as doc:
                for page in doc:
                    text= text + page.get_text()+ '\n'
            return text.strip()
        except Exception as e:
            print(f'Error reading PDF file: {e}')
    
    def read_docx(self, file_path):

        try:
            doc = docx.Document(file_path)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            return '\n'.join(full_text)
        except Exception as e:
            print(f"Error reading DOCX file: {e}")

    
    def read_txt(self, file_path):

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except Exception as e:
            print(f"Error reading TXT file: {e}")