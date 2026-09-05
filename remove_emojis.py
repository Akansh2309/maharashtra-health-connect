import os
import emoji

def remove_emojis_from_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # emoji.replace_emoji replaces all emojis with the replace string (default '')
        cleaned_content = emoji.replace_emoji(content, replace='')
        
        if cleaned_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            print(f"Removed emojis from: {filepath}")
    except Exception as e:
        print(f"Skipping {filepath}: {e}")

if __name__ == "__main__":
    target_dirs = ['.']
    
    for root, dirs, files in os.walk('.'):
        if '.git' in root or 'venv' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith(('.html', '.js', '.css', '.py', '.json', '.md', '.txt')):
                filepath = os.path.join(root, file)
                remove_emojis_from_file(filepath)
    print("Emoji removal complete.")
