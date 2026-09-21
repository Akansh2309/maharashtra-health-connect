import auth_utils
with open("auth_utils.py", "r") as f:
    content = f.read()
demo_account = '''    "9999999999": {
        "password_hash": hashlib.sha256("demo123".encode()).hexdigest(),
        "name": "Demo Patient",
        "email": "demopatient@mhconnect.org",
        "role": "patient",
    },'''
content = content.replace('"demo": {', demo_account + '\n    "demo": {')
with open("auth_utils.py", "w") as f:
    f.write(content)
