import json
from collections import defaultdict
import re

# ========= 1. Load terms from JSON file =========
def load_json_terms(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['terms']

# ========= 2. DFS traversal =========
def dfs(term_id):
    if term_id in visited:
        return
    visited.add(term_id)

    term = id_to_term.get(term_id)
    if not term:
        return

    children = parent_to_children.get(term_id, [])
    is_leaf = len(children) == 0

    results.append((
        term_id,
        normalize_text(term.get('name', '')),
        normalize_text(term.get('comment', '')),
        is_leaf
    ))

    for child_id in children:
        dfs(child_id)

# ========= 3. Normalization functions =========
def normalize_id(sbo_id: str) -> str:
    return sbo_id.replace('_', ':').strip()

def normalize_text(text: str) -> str:
    text = text.replace("''", "'").replace('\n', ' ').replace('\\n', ' ')
    text = re.sub(r'\s+', ' ', text)  # collapse multiple spaces
    return text.strip()

# ========= 4. Main entry point =========

# Replace with your JSON file path
json_file = '../ols_fetch_from_github/SBO_OBO_Files/localfiles/SBO_OBO_20230516_110919.json'
terms = load_json_terms(json_file)

# Build graph structure
id_to_term = {term['id']: term for term in terms}
parent_to_children = defaultdict(list)
for term in terms:
    for parent in term.get('is_a', []):
        parent_id = parent['id']
        parent_to_children[parent_id].append(term['id'])

# Perform DFS
visited = set()
results = []
dfs('SBO:0000176')

# Remove duplicates
unique_results = {item[0]: item for item in results}
sorted_results = list(unique_results.values())

# Generate SQL insert
insert_lines = [
    f"('{id}', '{name}', '{comment}', {'true' if is_leaf else 'false'})"
    for id, name, comment, is_leaf in sorted_results
]
sql = "INSERT INTO sbo_terms (id, name, comment, is_leaf) VALUES\n" + ",\n".join(insert_lines) + ";"

with open('insert_sbo.json.sql', 'w') as f:
    f.write(sql)

print(f"\n🧮 Total nodes found: {len(results)}. SQL written to insert_sbo.json.sql")

# ========= 5. Ground truth verification =========
ground_truth = [
    # your ground truth tuples (unchanged)
]

# Normalize ground truth
ground_truth = [
    (
        normalize_id(t[0]),
        normalize_text(t[1]),
        normalize_text(t[2]),
        t[3]
    )
    for t in ground_truth
]

# Normalize generated results
generated_dict = {
    normalize_id(item[0]): (
        normalize_id(item[0]),
        normalize_text(item[1]),
        normalize_text(item[2]),
        item[3]
    )
    for item in results
}

# Compare
print("\n======= Ground Truth Verification =======\n")
matched = mismatched = missing = 0

for gt in ground_truth:
    gt_id = gt[0]
    if gt_id not in generated_dict:
        print(f"❌ Missing: {gt_id}")
        missing += 1
    elif generated_dict[gt_id] != gt:
        print(f"⚠️ Mismatch: {gt_id}")
        print(f"  Expected: {gt}")
        print(f"  Actual:   {generated_dict[gt_id]}")
        mismatched += 1
    else:
        print(f"✅ Matched: {gt_id}")
        matched += 1

print("\n======= Summary =======")
print(f"✅ Matched: {matched}")
print(f"⚠️ Mismatched: {mismatched}")
print(f"❌ Missing: {missing}")
print(f"📦 Total in ground truth: {len(ground_truth)}")
