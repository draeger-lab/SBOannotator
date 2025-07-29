import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import os


def extract_sbo_comments_from_csv(csv_path):
    """
    Extract SBO data from CSV file.
    """
    # Read CSV file
    df = pd.read_csv(csv_path)

    # Filter out records with empty comments only
    df_filtered = df[
        (df['comment'].notna()) &
        (df['comment'].str.strip() != '')
        ].copy()

    # Convert is_leaf to boolean
    df_filtered['is_leaf'] = df_filtered['is_leaf'].astype(bool)

    return df_filtered


def vectorize_sbo_comments(csv_path):
    """
    Vectorize SBO records that have comments, similar to EC vectorization.
    Output files will be saved in the same directory as the script.
    """
    # Extract SBO data from CSV file
    print(f"Extracting SBO data from: {csv_path}")
    df = extract_sbo_comments_from_csv(csv_path)

    print(f"Number of SBO records with comments: {len(df)}")

    if len(df) == 0:
        print("No SBO records with comments found.")
        return

    # Load pre-trained SentenceTransformer model
    print("Loading SentenceTransformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Vectorize the comments
    print(f"Vectorizing comments for {len(df)} SBO records...")
    embeddings = model.encode(df['comment'].tolist(), show_progress_bar=True)

    # Save the full result as pickle (in current directory)
    results = {
        'sbo_ids': df['id'].tolist(),
        'names': df['name'].tolist(),
        'comments': df['comment'].tolist(),
        'is_leaf': df['is_leaf'].tolist(),
        'embeddings': embeddings
    }

    with open('sbo_comments_vectors.pkl', 'wb') as f:
        pickle.dump(results, f)

    # Save only the embeddings as .npy (in current directory)
    np.save('sbo_embeddings.npy', embeddings)

    # Create a DataFrame with vector information for CSV output (similar to EC format)
    vector_cols = {f'dim_{i}': embeddings[:, i] for i in range(embeddings.shape[1])}
    results_df = pd.DataFrame({
        'id': df['id'],
        'comments': df['comment'],
        'embedding_dim': [embeddings.shape[1]] * len(df),
        'vector_norm': np.linalg.norm(embeddings, axis=1),
        **vector_cols
    })

    # Save to CSV (in current directory)
    csv_path = 'sbo_vectorization_results.csv'
    results_df.to_csv(csv_path, index=False)

    print(f"Vectorization complete! Embedding shape: {embeddings.shape}")
    print(f"Saved files in current directory:")
    print(f"  - sbo_comments_vectors.pkl")
    print(f"  - sbo_embeddings.npy")
    print(f"  - {csv_path}")

    return results_df


if __name__ == "__main__":
    csv_file = "sbo_terms_202507292305.csv"  # 修改为CSV文件名

    if os.path.exists(csv_file):
        vectorize_sbo_comments(csv_file)
    else:
        print(f"CSV file does not exist: {csv_file}")
        print("Please ensure the CSV file is in the correct location.")