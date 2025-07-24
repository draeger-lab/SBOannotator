# import pandas as pd
# import numpy as np
# from sentence_transformers import SentenceTransformer
# import pickle
# import os
#
#
# def vectorize_ec_comments(csv_path, output_dir='vectors'):
#     """
#     Vectorize EC records that have comments.
#     """
#     # Create output directory
#     os.makedirs(output_dir, exist_ok=True)
#
#     # Read the CSV file
#     print(f"Reading CSV file: {csv_path}")
#     df = pd.read_csv(csv_path)
#
#     # Check data structure
#     print(f"Data shape: {df.shape}")
#     print(f"Columns: {df.columns.tolist()}")
#
#     # Filter records with non-empty comments
#     df_with_comments = df[df['comments'].notna() & (df['comments'].str.strip() != '')]
#     print(f"Number of records with comments: {len(df_with_comments)}")
#
#     if len(df_with_comments) == 0:
#         print("No records with comments found.")
#         return
#
#     # Load pretrained SentenceTransformer model
#     print("Loading SentenceTransformer model...")
#     model = SentenceTransformer('all-MiniLM-L6-v2')
#
#     # Vectorize the comments
#     print("Vectorizing comments...")
#     comments = df_with_comments['comments'].tolist()
#     embeddings = model.encode(comments, show_progress_bar=True)
#
#     # Save results
#     results = {
#         'ec_numbers': df_with_comments['ec_num'].tolist(),
#         'accepted_names': df_with_comments['accepted_name'].tolist(),
#         'reactions': df_with_comments['reaction'].tolist(),
#         'comments': comments,
#         'embeddings': embeddings
#     }
#
#     # Save the full result as pickle
#     with open(os.path.join(output_dir, 'ec_comments_vectors.pkl'), 'wb') as f:
#         pickle.dump(results, f)
#
#     # Save only the embeddings as .npy
#     np.save(os.path.join(output_dir, 'embeddings.npy'), embeddings)
#
#     # Save index information as CSV
#     index_df = df_with_comments[['ec_num', 'accepted_name']].copy()
#     index_df.to_csv(os.path.join(output_dir, 'ec_index.csv'), index=False)
#
#     # Done
#     print("Vectorization complete!")
#     print(f"- Embedding shape: {embeddings.shape}")
#     print(f"- Saved in: {output_dir}/")
#     print(f"- Files: ec_comments_vectors.pkl, embeddings.npy, ec_index.csv")
#
#
# if __name__ == "__main__":
#     # Set your CSV file path here
#     csv_file = "enzyme_data.csv"  # Replace with your actual file path
#
#     if os.path.exists(csv_file):
#         vectorize_ec_comments(csv_file)
#     else:
#         print(f"CSV file does not exist: {csv_file}")
#         print("Please generate a CSV file containing EC data first.")

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle

# Load the CSV file (assumed to contain 'ec_num' and 'comments' columns)
df = pd.read_csv('entry_with_comments_202507250622.csv')  # Replace with your actual filename

# Load the pre-trained SentenceTransformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Vectorize the comments
print(f"Vectorizing comments for {len(df)} EC records...")
embeddings = model.encode(df['comments'].tolist(), show_progress_bar=True)

# Save the results
results = {
    'ec_numbers': df['ec_num'].tolist(),
    'comments': df['comments'].tolist(),
    'embeddings': embeddings
}

with open('ec_comments_vectors.pkl', 'wb') as f:
    pickle.dump(results, f)

np.save('ec_embeddings.npy', embeddings)

# Create a DataFrame with vector information for inspection
# results_df = pd.DataFrame({
#     'ec_num': df['ec_num'],
#     'comments': df['comments'],
#     'embedding_dim': [embeddings.shape[1]] * len(df),
#     'vector_norm': np.linalg.norm(embeddings, axis=1)
# })

vector_cols = {f'dim_{i}': embeddings[:, i] for i in range(embeddings.shape[1])}
results_df = pd.DataFrame({
    'ec_num': df['ec_num'],
    'comments': df['comments'],
    'embedding_dim': [embeddings.shape[1]] * len(df),
    'vector_norm': np.linalg.norm(embeddings, axis=1),
    **vector_cols
})

# Save to CSV
results_df.to_csv('ec_vectorization_results.csv', index=False)
print("CSV file saved: ec_vectorization_results.csv")


print(f"Vectorization complete! Embedding shape: {embeddings.shape}")
print("Saved files: ec_comments_vectors.pkl, ec_embeddings.npy")
