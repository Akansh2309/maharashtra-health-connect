import re

with open("serve.py", "r") as f:
    serve_content = f.read()

if "/api/locations" not in serve_content:
    serve_content = serve_content.replace(
        'if path == "/api/facilities":',
        'if path == "/api/locations":\n            return api_routes.handle_locations(self)\n\n        if path == "/api/facilities":'
    )
    with open("serve.py", "w") as f:
        f.write(serve_content)


with open("api_routes.py", "r") as f:
    api_content = f.read()

if "def handle_locations" not in api_content:
    new_func = """
def handle_locations(server):
    import csv
    import os
    locations = {"districts": set(), "villages": set()}
    try:
        with open(os.path.join(os.path.dirname(__file__), "city_town_village.csv"), "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                d = row.get("District", "").strip()
                v = row.get("Location_Name", "").strip()
                if d: locations["districts"].add(d)
                if v: locations["villages"].add(v)
    except Exception as e:
        pass
    return server._send_json({
        "districts": sorted(list(locations["districts"])),
        "villages": sorted(list(locations["villages"]))
    })
"""
    # Append it before # --- data endpoints --- or at the end
    if "#  data endpoints " in api_content:
        api_content = api_content.replace("#  data endpoints ", new_func + "\n#  data endpoints ")
    else:
        api_content += "\n" + new_func
    
    with open("api_routes.py", "w") as f:
        f.write(api_content)
