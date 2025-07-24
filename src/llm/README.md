
# 📘 EC Comment Vectorization - README

## 🧩 Overview

This project provides a script `ec_vector.py` that vectorizes enzyme comment data using a pre-trained sentence embedding model from the [Sentence-Transformers](https://www.sbert.net/) library.

The input is a CSV file containing EC numbers and their functional comments. The script filters and processes records that have non-empty comments, converts them into dense vector representations, and saves the results in multiple formats for further analysis, visualization, or machine learning tasks.

---

## 📂 Input

The input CSV file must contain at least the following columns:

- `ec_num`: Enzyme Commission number (e.g., `"1.1.1.1"`)
- `comments`: Descriptive comment text associated with the EC number

📌 The dataset used in this script is **`entry_with_comments`**, which has already been filtered to include **only rows where `comments` is not null or empty**.

---

## ⚙️ What the script does (`ec_vector.py`)

1. Loads the input CSV using `pandas`.
2. Uses `SentenceTransformer('all-MiniLM-L6-v2')` to vectorize the `comments` column.
3. Constructs a result dictionary and a browsable DataFrame with embedding vectors.
4. Saves the outputs to multiple files:
   - `.pkl`: Full Python dictionary with vectors and metadata
   - `.npy`: Raw NumPy matrix for fast loading
   - `.csv`: Full table with all metadata and embedding values per dimension

---

## 📄 Output Files

### ✅ `ec_comments_vectors.pkl`

- A Python `dict` serialized via `pickle`, containing:
  - `'ec_numbers'`: List of EC numbers
  - `'comments'`: List of corresponding comments
  - `'embeddings'`: A NumPy array of shape `(N, 384)` representing each comment vector

### ✅ `ec_embeddings.npy`

- A NumPy `.npy` file containing only the embeddings: shape `(N, 384)`
- Useful for fast loading in numerical computing environments

### ✅ `ec_vectorization_results.csv`

This is a tabular file combining metadata and embedding values for easy inspection.

#### 🔠 Columns:

| Column Name      | Description                                                                 |
|------------------|-----------------------------------------------------------------------------|
| `ec_num`         | EC number (Enzyme Commission number)                                        |
| `comments`       | Functional description or comment for that EC                               |
| `embedding_dim`  | Embedding dimensionality (typically 384)                                    |
| `vector_norm`    | L2 norm (magnitude) of the embedding vector (computed via `np.linalg.norm`) |
| `dim_0`...`dim_383` | The actual embedding vector, one dimension per column                    |

This CSV is ideal for manual inspection (e.g. in Excel), visualization, or conversion to other formats.

---

## 🧠 Model Details

- Model used: [`all-MiniLM-L6-v2`](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- Embedding dimension: `384`
- Encoding type: Mean pooling over BERT token embeddings

---

## 🛠️ How to Use

### Run the script:

```bash
python ec_vector.py
```

### Make sure the input CSV is correctly set inside the script:

```python
csv_file = "entry_with_comments_202507250622.csv"
```

You will find the output files in the same directory unless otherwise specified.

---

## 📌 Notes

- Only EC entries **with non-empty comments** are processed.
- The script currently vectorizes only the `comments` field, but can be extended to combine or include `accepted_name`, `reaction`, etc.
- The `vector_norm` column can be used to analyze how “informative” each comment is in embedding space.
