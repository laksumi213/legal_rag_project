from docx import Document
import os

def create_empty_docx(path: str):
    document = Document()
    document.save(path)

if __name__ == "__main__":
    demo_dir = "data/demo_wills"
    os.makedirs(demo_dir, exist_ok=True)
    
    files_to_create = [
        "will_sample_1.docx",
        "will_sample_2.docx",
        "will_sample_3.docx"
    ]

    print("Creating empty sample Word documents...")
    for file_name in files_to_create:
        file_path = os.path.join(demo_dir, file_name)
        create_empty_docx(file_path)
        print(f"Created: {file_path}")
    print("Finished creating sample Word documents.")
