import re

def check_tags(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Simple regex to find ALL {{ ... }} tags
    tags = re.findall(r'\{\{.*?\}\}', content, re.DOTALL)
    multiline = [t for t in tags if '\n' in t]
    
    if multiline:
        print(f"Found {len(multiline)} multiline tags:")
        for t in multiline:
            print(f"---TAG---\n{t}\n---------")
    else:
        print("No multiline tags found.")

if __name__ == "__main__":
    check_tags('simulator/templates/simulator/bilanz.html')
