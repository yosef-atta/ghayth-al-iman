import os
import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

CHAPTER_FILES = [
    'الفصل-الأول.md',
    'الفصل-الثاني.md',
    'الفصل-الثالث.md',
    'الفصل-الرابع.md',
    'الفصل-الخامس.md'
]

BOOK_HEADER = "# غيث الإيمان: رحلة العقل والمنطق من العدم إلى اليقين\n\n---\n\n"


def generate_master_markdown(output_filename="غيث-الإيمان.md"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(base_dir, output_filename)
    
    combined_content = [BOOK_HEADER]
    missing_files = []
    
    for idx, filename in enumerate(CHAPTER_FILES):
        file_path = os.path.join(base_dir, filename)
        if not os.path.exists(file_path):
            missing_files.append(filename)
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        combined_content.append(content)
        combined_content.append("\n\n")
        
        if idx < len(CHAPTER_FILES) - 1:
            combined_content.append("---\n\n")
            
    if missing_files:
        print(f"تحذير: بعض ملفات الفصول مفقودة: {missing_files}")
        
    final_text = "".join(combined_content).strip() + "\n"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_text)
        
    print(f"تم إنشاء وتجميع ملف الماركداون الشامل بنجاح: {output_path} ({len(final_text)} حرف)")
    return output_path


if __name__ == '__main__':
    generate_master_markdown()
