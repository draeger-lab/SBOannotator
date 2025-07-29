
# 📘 EC & SBO Comment Vectorization - README

## 🧩 Overview

This project provides scripts for vectorizing enzyme and sbo comment data using a pre-trained sentence embedding model from the [Sentence-Transformers](https://www.sbert.net/) library.

- **`ec_vector.py`**: Vectorizes EC (Enzyme Commission) comment data
- **`sbo_vector.py`**: Vectorizes SBO (Systems Biology Ontology) comment data

Both scripts filter and process records that have non-empty comments, convert them into dense vector representations, and save the results in multiple formats for further analysis, visualization, or machine learning tasks.

---

## 📊 Data Sources

### EC Data
- **Source**: Downloaded from [ExploreEnz](https://www.enzyme-database.org/) database
- **Processing**: Filtered in MySQL to include only EC entries with non-empty comments
- **Input File**: `entry_with_comments_202507250622.csv`

### SBO Data  
- **Source**: Fetched from local sbo json file：SBO_OBO_20230516_110919.json
- **Processing Scripts**: 
  - `sbo_insert.py`: extracts SBO ontology terms from a JSON file, performs a depth-first search traversal starting from a root node, and generates SQL insert statements for database storage while verifying the results against ground truth data.
  - `insert_sbo.json.sql`: SQL file containing INSERT statements for SBO terms with comments
- **Input File**: `sbo_terms_202507292305.csv`

---

## 📂 Input Format

### EC Data Input
The EC input CSV file must contain the following columns:
- `ec_num`: Enzyme Commission number (e.g., `"1.1.1.1"`)
- `comments`: Descriptive comment text associated with the EC number

### SBO Data Input
The SBO input CSV file contain the following columns:
- `id`: SBO identifier (e.g., `"SBO:0000176"`)
- `name`: SBO term name
- `comment`: Descriptive comment text associated with the SBO term
- `is_leaf`: Boolean indicating if the term is a leaf node

---

## ⚙️ What the scripts do

### `ec_vector.py`
1. Loads the EC CSV using `pandas`.
2. Uses `SentenceTransformer('all-MiniLM-L6-v2')` to vectorize the `comments` column.
3. Constructs a result dictionary and a browsable DataFrame with embedding vectors.
4. Saves the outputs to multiple files:
   - `.pkl`: Full Python dictionary with vectors and metadata
   - `.npy`: Raw NumPy matrix for fast loading
   - `.csv`: Full table with all metadata and embedding values per dimension

### `sbo_vector.py`
1. Loads the SBO CSV using `pandas`.
2. Uses `SentenceTransformer('all-MiniLM-L6-v2')` to vectorize the `comment` column.
3. Constructs a result dictionary and a browsable DataFrame with embedding vectors.
4. Saves the outputs in the same format as EC vectorization.

---

## 📄 Output Files

### EC Output Files

#### ✅ `ec_comments_vectors.pkl`
- A Python `dict` serialized via `pickle`, containing:
  - `'ec_numbers'`: List of EC numbers
  - `'comments'`: List of corresponding comments
  - `'embeddings'`: A NumPy array of shape `(N, 384)` representing each comment vector

#### ✅ `ec_embeddings.npy`
- A NumPy `.npy` file containing only the embeddings: shape `(N, 384)`

#### ✅ `ec_vectorization_results.csv`
Tabular file with columns:
- `ec_num`: EC number
- `comments`: Functional description
- `embedding_dim`: Embedding dimensionality (384)
- `vector_norm`: L2 norm of the embedding vector
- `dim_0`...`dim_383`: The actual embedding vector dimensions

### SBO Output Files

#### ✅ `sbo_comments_vectors.pkl`
- A Python `dict` serialized via `pickle`, containing:
  - `'sbo_ids'`: List of SBO identifiers
  - `'names'`: List of SBO term names
  - `'comments'`: List of corresponding comments
  - `'is_leaf'`: List of boolean values indicating leaf nodes
  - `'embeddings'`: A NumPy array of shape `(N, 384)` representing each comment vector

#### ✅ `sbo_embeddings.npy`
- A NumPy `.npy` file containing only the embeddings: shape `(N, 384)`

#### ✅ `sbo_vectorization_results.csv`
Tabular file with columns:
- `id`: SBO identifier
- `comments`: Descriptive comment
- `embedding_dim`: Embedding dimensionality (384)
- `vector_norm`: L2 norm of the embedding vector
- `dim_0`...`dim_383`: The actual embedding vector dimensions

---

## 🧠 Model Details

- Model used: [`all-MiniLM-L6-v2`](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- Embedding dimension: `384`
- Encoding type: Mean pooling over BERT token embeddings

---

## 🛠️ How to Use

### For EC Vectorization:
```bash
python ec_vector.py
```

Make sure the input CSV is correctly set inside the script:
```python
csv_file = "entry_with_comments_202507250622.csv"
```

### For SBO Vectorization:
```bash
python sbo_vector.py
```

Make sure the input CSV is correctly set inside the script:
```python
csv_file = "sbo_terms_202507292305.csv"
```

Output files will be saved in the same directory as the scripts.

---

## 📌 Notes

- Only entries **with non-empty comments** are processed for both EC and SBO data.
- Both scripts use the same embedding model for consistency.
- The `vector_norm` column can be used to analyze how "informative" each comment is in embedding space.
- SBO data includes additional metadata like `name` and `is_leaf` status compared to EC data.
