with open("public/interface.html", "r") as f:
    content = f.read()

# 1. Remove broken loader
content = content.replace('    <div class="loader-text">Loading...</div></div>\n', '')

# 2. Add list attributes
content = content.replace(
    '<input type="text" id="su-village" name="village" required placeholder="Your village or locality">',
    '<input type="text" id="su-village" name="village" required placeholder="Your village or locality" list="village-list">\n                        <datalist id="village-list"></datalist>'
)
content = content.replace(
    '<input type="text" id="su-district" name="district" required placeholder="Your district">',
    '<input type="text" id="su-district" name="district" required placeholder="Your district" list="district-list">\n                        <datalist id="district-list"></datalist>'
)

# 3. Add JS to fetch and validate
js_code = """
    <script>
        // Location datalist logic
        let validVillages = new Set();
        let validDistricts = new Set();

        fetch('/api/locations').then(r => r.json()).then(data => {
            const vList = document.getElementById('village-list');
            data.villages.forEach(v => {
                validVillages.add(v);
                let opt = document.createElement('option');
                opt.value = v;
                vList.appendChild(opt);
            });
            const dList = document.getElementById('district-list');
            data.districts.forEach(d => {
                validDistricts.add(d);
                let opt = document.createElement('option');
                opt.value = d;
                dList.appendChild(opt);
            });
        }).catch(err => console.error('Failed to load locations', err));

        // Form validation hook
        document.getElementById('signup-form').addEventListener('submit', function(e) {
            const isPatient = document.getElementById('su-role-patient').checked;
            if (isPatient) {
                const village = document.getElementById('su-village').value.trim();
                const district = document.getElementById('su-district').value.trim();
                
                if (validVillages.size > 0 && !validVillages.has(village)) {
                    e.preventDefault();
                    document.getElementById('signup-error').textContent = "Invalid Village. Please select from the dropdown.";
                    document.getElementById('signup-error').style.display = 'block';
                    return;
                }
                if (validDistricts.size > 0 && !validDistricts.has(district)) {
                    e.preventDefault();
                    document.getElementById('signup-error').textContent = "Invalid District. Please select from the dropdown.";
                    document.getElementById('signup-error').style.display = 'block';
                    return;
                }
            }
        });
    </script>
"""
content = content.replace('</body>', js_code + '\n</body>')

with open("public/interface.html", "w") as f:
    f.write(content)
