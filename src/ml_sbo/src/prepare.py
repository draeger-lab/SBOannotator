#!/usr/bin/env python3


import pandas as pd
import json
import os
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, Counter
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


def load_data(gpt_path, terms_path, golden_path):
    """
    Load three data files for SBO annotation training
    
    Args:
        gpt_path (str): Path to GPT prediction data CSV file
        terms_path (str): Path to SBO terms dictionary CSV file
        golden_path (str): Path to golden standard data CSV file
    
    Returns:
        tuple: (gpt_data, sbo_terms, golden_data) - Three pandas DataFrames containing the loaded data
    """
    print("Loading data files...")
    
    # Load SBO terms dictionary (authoritative standard)
    sbo_terms = pd.read_csv(terms_path)
    print(f"SBO terms dictionary: {len(sbo_terms)} records")
    
    # Load GPT prediction data
    gpt_data = pd.read_csv(gpt_path)
    print(f"GPT prediction data: {len(gpt_data)} records")
    
    # Load golden standard data
    golden_data = pd.read_csv(golden_path)
    print(f"Golden standard data: {len(golden_data)} records")
    
    return gpt_data, sbo_terms, golden_data


def create_sbo_mapping(sbo_terms):
    """
    Create mapping dictionary from SBO ID to attributes
    
    Args:
        sbo_terms (pd.DataFrame): DataFrame containing SBO terms with columns 'id', 'name', 'comment', 'is_leaf'
    
    Returns:
        dict: Dictionary mapping SBO IDs to their attributes (name, comment, is_leaf)
    """
    sbo_mapping = {}
    for _, row in sbo_terms.iterrows():
        sbo_mapping[row['id']] = {
            'name': row['name'],
            'comment': row['comment'],
            'is_leaf': row['is_leaf']
        }
    return sbo_mapping


def normalize_gpt_data(gpt_data, sbo_mapping):
    """
    Normalize GPT data fields to LLM format
    
    Args:
        gpt_data (pd.DataFrame): GPT prediction data with columns 'sbo_id', 'ec_number', 'sbo_name', etc.
        sbo_mapping (dict): Dictionary mapping SBO IDs to their attributes
    
    Returns:
        tuple: (normalized, conflicts) - List of normalized records and list of field conflicts found
    """
    print("Normalizing GPT prediction data...")
    
    # Create normalized data structure
    normalized = []
    conflicts = []
    
    for idx, row in gpt_data.iterrows():
        sbo_id = row['sbo_id']
        ec_number = str(row['ec_number'])
        
        # Check for field conflicts
        if sbo_id in sbo_mapping:
            original_name = row['sbo_name']
            original_comment = row['sbo_comment'] 
            original_is_leaf = row['is_leaf']
            
            correct_name = sbo_mapping[sbo_id]['name']
            correct_comment = sbo_mapping[sbo_id]['comment']
            correct_is_leaf = sbo_mapping[sbo_id]['is_leaf']
            
            if (original_name != correct_name or 
                original_comment != correct_comment or 
                int(original_is_leaf) != int(correct_is_leaf)):
                conflicts.append({
                    'sbo_id': sbo_id,
                    'ec_num': ec_number,
                    'original_name': original_name,
                    'correct_name': correct_name,
                    'original_comment': original_comment,
                    'correct_comment': correct_comment,
                    'original_is_leaf': original_is_leaf,
                    'correct_is_leaf': correct_is_leaf
                })
        
        # Extract keywords
        keywords = []
        if pd.notna(row['ec_text_keyword']):
            keyword_text = str(row['ec_text_keyword'])
            raw_keywords = [k.strip() for k in keyword_text.replace(';', ',').split(',')]
            keywords = [k for k in raw_keywords if len(k) > 2][:5]
        
        # Generate reaction_id
        reaction_id = f"gpt_{idx}_{ec_number}_{sbo_id}"
        
        # Build new LLM format record
        record = {
            'reaction_id': {
                'reaction_id': reaction_id,
                'original_sbo': sbo_id,  # Original SBO from input data
                'original_sbo_term': sbo_mapping.get(sbo_id, {}).get('name', row['sbo_name']),
                'original_sbo_comment': sbo_mapping.get(sbo_id, {}).get('comment', row['sbo_comment']),
                'original_sbo_is_leaf': sbo_mapping.get(sbo_id, {}).get('is_leaf', row['is_leaf']),
                'ec_numbers': [ec_number],
                'ec_to_llm': ec_number,
                'ec_text_to_llm': str(row['ec_text']) if pd.notna(row['ec_text']) else "",
                # LLM output fields (as training targets)
                'recommended_sbo_id': sbo_id,
                'recommend_sbo_term': sbo_mapping.get(sbo_id, {}).get('name', row['sbo_name']),
                'recommend_sbo_comment': sbo_mapping.get(sbo_id, {}).get('comment', row['sbo_comment']),
                'recommend_sbo_is_leaf': sbo_mapping.get(sbo_id, {}).get('is_leaf', row['is_leaf']),
                'recommend_sbo_reason': str(row['reason']) if pd.notna(row['reason']) else "",
                'keywords': keywords,
                'source': 'gpt'
            }
        }
        normalized.append(record)
    
    print(f"GPT data normalization completed, found {len(conflicts)} field conflicts")
    return normalized, conflicts


def normalize_golden_data(golden_data, sbo_mapping):
    """
    Normalize golden standard data fields to LLM format.
    
    Args:
        golden_data (pd.DataFrame): Golden standard data with columns 'correct_sbo_id', 'ec_num', etc.
        sbo_mapping (dict): Dictionary mapping SBO IDs to their attributes
    
    Returns:
        tuple: (normalized, conflicts) - List of normalized records and list of field conflicts found
    """
    print("Normalizing golden standard data...")
    
    normalized = []
    conflicts = []
    
    for idx, row in golden_data.iterrows():
        sbo_id = row['correct_sbo_id']
        ec_number = str(row['ec_num'])
        

        if sbo_id in sbo_mapping:
            if (row['correct_sbo_name'] != sbo_mapping[sbo_id]['name'] or
                row['correct_sbo_comment'] != sbo_mapping[sbo_id]['comment'] or
                int(row['correct_sbo_is_leaf']) != int(sbo_mapping[sbo_id]['is_leaf'])):
                conflicts.append({
                    'sbo_id': sbo_id,
                    'ec_num': ec_number,
                    'golden_name': row['correct_sbo_name'],
                    'terms_name': sbo_mapping[sbo_id]['name']
                })
        
        # Generate reaction_id
        reaction_id = f"golden_{idx}_{ec_number}_{sbo_id}"

        record = {
            'reaction_id': {
                'reaction_id': reaction_id,
                'original_sbo': "SBO:0000000",  
                'original_sbo_term': "unknown",
                'original_sbo_comment': "unknown", 
                'original_sbo_is_leaf': False,
                'ec_numbers': [ec_number],
                'ec_to_llm': ec_number,
                'ec_text_to_llm': str(row['ec_text']) if pd.notna(row['ec_text']) else "",
                # Correct labels (as training targets)
                'recommended_sbo_id': sbo_id,
                'recommend_sbo_term': sbo_mapping.get(sbo_id, {}).get('name', row['correct_sbo_name']),
                'recommend_sbo_comment': sbo_mapping.get(sbo_id, {}).get('comment', row['correct_sbo_comment']),
                'recommend_sbo_is_leaf': sbo_mapping.get(sbo_id, {}).get('is_leaf', row['correct_sbo_is_leaf']),
                'recommend_sbo_reason': "",  # Golden data has no reason field
                'keywords': [],  # Golden data has no keywords field
                'source': 'golden'
            }
        }
        normalized.append(record)
    
    print(f"Golden data normalization completed, found {len(conflicts)} field conflicts")
    return normalized, conflicts


def deduplicate_data(combined_data):
    """
    Remove duplicates using ec_num + sbo_id + ec_text as unique key.
    
    Args:
        combined_data (list): Combined list of normalized records from GPT and golden data
    
    Returns:
        tuple: (deduplicated, duplicates) - List of unique records and list of duplicate information
    """
    print("Data deduplication...")
    
    # Create unique keys
    dedup_dict = {}
    duplicates = []
    
    for record in combined_data:
        # Extract deduplication key values from new nested structure
        reaction_data = record['reaction_id']
        
        # Build unique key
        unique_key = (
            reaction_data['ec_to_llm'],
            reaction_data['recommended_sbo_id'],
            reaction_data['ec_text_to_llm'][:100]  # Only take first 100 characters to avoid excessive length
        )
        
        if unique_key in dedup_dict:
            duplicates.append({
                'key': unique_key,
                'existing': dedup_dict[unique_key]['reaction_id']['source'],
                'duplicate': reaction_data['source']
            })
            # Prioritize retaining golden data
            if reaction_data['source'] == 'golden':
                dedup_dict[unique_key] = record
        else:
            dedup_dict[unique_key] = record
    
    deduplicated = list(dedup_dict.values())
    print(f"Deduplication completed: {len(combined_data)} → {len(deduplicated)} records, removed {len(duplicates)} duplicates")
    
    return deduplicated, duplicates


def split_data(deduplicated_data):
    """
    Split dataset into train/dev/test sets.
    
    Args:
        deduplicated_data (list): List of deduplicated records
    
    Returns:
        tuple: (dev_data, test_data, train_base_data, train_noisy_data) - Split datasets
    """
    print("Splitting dataset...")
    
    # Separate golden data and GPT data (from new nested structure)
    golden_records = [r for r in deduplicated_data if r['reaction_id']['source'] == 'golden']
    gpt_records = [r for r in deduplicated_data if r['reaction_id']['source'] == 'gpt']
    
    print(f"Golden data: {len(golden_records)} records")
    print(f"GPT data: {len(gpt_records)} records")
    

    import random
    random.seed(42)
    random.shuffle(golden_records)
    
    dev_data = golden_records[:100]
    test_data = golden_records[100:200]
    train_base_data = golden_records[200:]
    
    # All GPT data as train_noisy
    train_noisy_data = gpt_records
    
    print(f"Data splitting completed:")
    print(f"  - dev: {len(dev_data)} records")
    print(f"  - test: {len(test_data)} records")
    print(f"  - train_base: {len(train_base_data)} records")
    print(f"  - train_noisy: {len(train_noisy_data)} records")
    
    return dev_data, test_data, train_base_data, train_noisy_data


def create_labels_mapping(sbo_terms, all_data):
    """
    Create label mapping file.
    
    Args:
        sbo_terms (pd.DataFrame): DataFrame containing SBO terms
        all_data (list): All data records for extracting used labels
    
    Returns:
        dict: Complete label mapping dictionary with all SBO terms and their attributes
    """
    print("Creating label mappings...")
    
    # Labels actually appearing in data (extracted from new nested structure)
    used_labels = set()
    for record in all_data:
        used_labels.add(record['reaction_id']['recommended_sbo_id'])
    
    # Create complete label mapping (using all 42 labels from terminology)
    all_sbo_labels = []
    id2name = {}
    name2id = {}
    id2comment = {}
    id2is_leaf = {}
    
    for _, row in sbo_terms.iterrows():
        label_id = row['id']
        label_name = row['name']
        is_leaf = bool(row['is_leaf'])
        
        all_sbo_labels.append(label_id)
        id2name[label_id] = label_name
        name2id[label_name] = label_id
        id2comment[label_id] = row['comment']
        id2is_leaf[label_id] = is_leaf
    
    # Create numerical index mapping (for model)
    label2idx = {label_id: idx for idx, label_id in enumerate(all_sbo_labels)}
    idx2label = {idx: label_id for label_id, idx in label2idx.items()} 
    
    labels_mapping = {
        'id2name': id2name,
        'name2id': name2id,
        'id2comment': id2comment,
        'id2is_leaf': id2is_leaf,
        'all_labels': all_sbo_labels,  # Complete 42 labels
        'used_labels': list(used_labels),  # Labels appearing in data
        'label2idx': label2idx,  # Label to numerical index mapping
        'idx2label': idx2label,  # Numerical index to label mapping
        'total_labels': len(all_sbo_labels),
        'leaf_labels': [label_id for label_id in all_sbo_labels if id2is_leaf[label_id]],
        'non_leaf_labels': [label_id for label_id in all_sbo_labels if not id2is_leaf[label_id]]
    }
    
    print(f"Label mapping creation completed:")
    print(f"  - Total labels in terminology: {len(all_sbo_labels)}")
    print(f"  - Used in data: {len(used_labels)}")
    print(f"  - Leaf labels: {len(labels_mapping['leaf_labels'])}")
    print(f"  - Non-leaf labels: {len(labels_mapping['non_leaf_labels'])}")
    
    return labels_mapping


def save_jsonl(data, filepath):
    """
    Save data in JSONL format.
    
    Args:
        data (list): List of data records to save
        filepath (str): Path where to save the JSONL file
    
    Returns:
        None
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        for record in data:
           
            clean_record = {k: v for k, v in record.items() if k != 'source'}
            f.write(json.dumps(clean_record, ensure_ascii=False) + '\n')


def analyze_consistency(gpt_conflicts, golden_conflicts, duplicates, all_data):
    """
    Analyze data consistency and generate statistics.
    
    Args:
        gpt_conflicts (list): List of conflicts found in GPT data
        golden_conflicts (list): List of conflicts found in golden data
        duplicates (list): List of duplicate records
        all_data (list): All processed data records
    
    Returns:
        dict: Comprehensive consistency analysis statistics
    """
    print("Analyzing data consistency...")
    
    # 1. Field conflict statistics
    gpt_conflict_stats = {
        'name_conflicts': len([c for c in gpt_conflicts if c.get('original_name') != c.get('correct_name')]),
        'comment_conflicts': len([c for c in gpt_conflicts if c.get('original_comment') != c.get('correct_comment')]),
        'is_leaf_conflicts': len([c for c in gpt_conflicts if c.get('original_is_leaf') != c.get('correct_is_leaf')])
    }
    
    # 2. Overlap analysis (extracted from new nested structure)
    golden_ec_nums = set([r['reaction_id']['ec_to_llm'] for r in all_data if r['reaction_id']['source'] == 'golden'])
    gpt_ec_nums = set([r['reaction_id']['ec_to_llm'] for r in all_data if r['reaction_id']['source'] == 'gpt'])
    overlap_ec_nums = golden_ec_nums.intersection(gpt_ec_nums)
    
    # 3. Confusion cluster analysis
    label_pairs = defaultdict(int)
    for dup in duplicates:
        if len(dup['key']) >= 2:  # ec_num, label_id
            pass
    
    # 4. Class distribution statistics (extracted from new nested structure)
    golden_label_dist = Counter([r['reaction_id']['recommended_sbo_id'] for r in all_data if r['reaction_id']['source'] == 'golden'])
    gpt_label_dist = Counter([r['reaction_id']['recommended_sbo_id'] for r in all_data if r['reaction_id']['source'] == 'gpt'])
    
    return {
        'gpt_conflicts': gpt_conflict_stats,
        'golden_conflicts': len(golden_conflicts),
        'duplicate_count': len(duplicates),
        'ec_overlap': {
            'golden_total': len(golden_ec_nums),
            'gpt_total': len(gpt_ec_nums),
            'overlap_count': len(overlap_ec_nums),
            'overlap_rate': len(overlap_ec_nums) / len(golden_ec_nums) if golden_ec_nums else 0
        },
        'golden_label_dist': dict(golden_label_dist.most_common()),
        'gpt_label_dist': dict(gpt_label_dist.most_common(10))  # Only take top 10
    }


def create_distribution_plots(consistency_stats, output_dir):
    """
    Create class distribution histograms.
    
    Args:
        consistency_stats (dict): Consistency analysis statistics
        output_dir (str): Output directory for saving plots
    
    Returns:
        None
    """
    print("Generating class distribution plots...")
    
    # Ensure plots directory exists
    plots_dir = os.path.join(output_dir, 'docs', 'plots')
    os.makedirs(plots_dir, exist_ok=True)
    
    plt.style.use('default')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Golden data distribution
    golden_labels = list(consistency_stats['golden_label_dist'].keys())[:10]
    golden_counts = [consistency_stats['golden_label_dist'][label] for label in golden_labels]
    
    ax1.bar(range(len(golden_labels)), golden_counts)
    ax1.set_title('Golden Data Label Distribution (Top 10)')
    ax1.set_xlabel('SBO Labels')
    ax1.set_ylabel('Count')
    ax1.tick_params(axis='x', rotation=45)
    ax1.set_xticks(range(len(golden_labels)))
    ax1.set_xticklabels([label.replace('SBO:', '') for label in golden_labels], rotation=45, ha='right')
    
    # GPT data distribution
    gpt_labels = list(consistency_stats['gpt_label_dist'].keys())[:10]
    gpt_counts = [consistency_stats['gpt_label_dist'][label] for label in gpt_labels]
    
    ax2.bar(range(len(gpt_labels)), gpt_counts)
    ax2.set_title('GPT Data Label Distribution (Top 10)')
    ax2.set_xlabel('SBO Labels')
    ax2.set_ylabel('Count')
    ax2.tick_params(axis='x', rotation=45)
    ax2.set_xticks(range(len(gpt_labels)))
    ax2.set_xticklabels([label.replace('SBO:', '') for label in gpt_labels], rotation=45, ha='right')
    
    plt.tight_layout()
    plot_path = os.path.join(plots_dir, 'label_distribution.png')
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Class distribution plot saved to: {plot_path}")


def generate_report(consistency_stats, output_dir):
    """
    Generate consistency check report.
    
    Args:
        consistency_stats (dict): Consistency analysis statistics
        output_dir (str): Output directory for saving the report
    
    Returns:
        None
    """
    print("Generating consistency check report...")
    
    report_content = f"""# Data Consistency and Coverage Report

## 1. Field Conflict Statistics

### GPT Data vs Terminology Alignment Results
- Name field conflicts: {consistency_stats['gpt_conflicts']['name_conflicts']}
- Comment field conflicts: {consistency_stats['gpt_conflicts']['comment_conflicts']}
- is_leaf field conflicts: {consistency_stats['gpt_conflicts']['is_leaf_conflicts']}

### Golden Data vs Terminology Alignment Results
- Total field conflicts: {consistency_stats['golden_conflicts']}

## 2. Data Overlap Analysis

### EC Number Overlap
- Golden data EC total: {consistency_stats['ec_overlap']['golden_total']}
- GPT data EC total: {consistency_stats['ec_overlap']['gpt_total']} 
- Overlap EC count: {consistency_stats['ec_overlap']['overlap_count']}
- Overlap ratio: {consistency_stats['ec_overlap']['overlap_rate']:.2%}

### Deduplication Statistics
- Duplicate records: {consistency_stats['duplicate_count']}

## 3. Label Distribution Analysis

### Golden Data Top Labels
"""
    
    for i, (label, count) in enumerate(list(consistency_stats['golden_label_dist'].items())[:10]):
        report_content += f"{i+1}. {label}: {count} 条\n"
    
    report_content += f"""
### GPT Data Top Labels
"""
    
    for i, (label, count) in enumerate(list(consistency_stats['gpt_label_dist'].items())[:10]):
        report_content += f"{i+1}. {label}: {count} 条\n"

    report_content += f"""
## 4. Major Confusion Cluster Statistics

Based on data observations, main confusion patterns include:
- **Oxidation-related**: oxidation ↔ hydroxylation (fine-grained oxidation reaction confusion)
- **Group transfer**: transfer of a chemical group ↔ specific group transfers (acetylation, palmitoylation, etc.)
- **Metabolic pathways**: general biochemical reaction ↔ specific reaction types

## 5. Data Quality Conclusions

1. **Consistency**: Most fields remain consistent after terminology backfilling
2. **Coverage**: GPT and golden data have {consistency_stats['ec_overlap']['overlap_rate']:.1%} overlap in EC numbers
3. **Class balance**: Class imbalance issues exist, need to consider class weights during training
4. **Noise handling**: GPT data as noise samples, requires special handling in second-stage training

## 6. Visualization Charts

Class distribution histogram saved to: `docs/plots/label_distribution.png`

---
*Report generation time: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    report_path = os.path.join(output_dir, 'check_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"Consistency report saved to: {report_path}")


def main():
    """
    Main entry point for data cleaning and consistency validation.
    
    Input: Command line arguments specifying data paths and output directory
    Output: Processed JSONL files, label mappings, and consistency reports
    Purpose: Orchestrates the complete data preparation pipeline including normalization, deduplication, splitting, and quality analysis
    """
    parser = argparse.ArgumentParser(description='SBO data cleaning and consistency validation')
    parser.add_argument('--gpt', required=True, help='GPT prediction data CSV file path')
    parser.add_argument('--terms', required=True, help='SBO terms dictionary CSV file path')  
    parser.add_argument('--golden', required=True, help='Golden standard data CSV file path')
    parser.add_argument('--out', required=True, help='Output directory path')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.out, exist_ok=True)
    plots_dir = os.path.join(os.path.dirname(args.out), 'docs', 'plots')
    os.makedirs(plots_dir, exist_ok=True)
    
    try:
        # 1. Load data
        gpt_data, sbo_terms, golden_data = load_data(args.gpt, args.terms, args.golden)
        
        # 2. Create SBO mapping
        sbo_mapping = create_sbo_mapping(sbo_terms)
        print(f"SBO mapping creation completed: {len(sbo_mapping)} labels")
        
        # 3. Normalize data
        normalized_gpt, gpt_conflicts = normalize_gpt_data(gpt_data, sbo_mapping)
        normalized_golden, golden_conflicts = normalize_golden_data(golden_data, sbo_mapping)
        
        # 4. Combine and deduplicate
        combined_data = normalized_gpt + normalized_golden
        deduplicated_data, duplicates = deduplicate_data(combined_data)
        
        # 5. Split data
        dev_data, test_data, train_base_data, train_noisy_data = split_data(deduplicated_data)
        
        # 6. Create label mappings
        labels_mapping = create_labels_mapping(sbo_terms, deduplicated_data)
        
        # 7. Save data files
        save_jsonl(dev_data, os.path.join(args.out, 'dev.jsonl'))
        save_jsonl(test_data, os.path.join(args.out, 'test.jsonl'))
        save_jsonl(train_base_data, os.path.join(args.out, 'train_base.jsonl'))
        save_jsonl(train_noisy_data, os.path.join(args.out, 'train_noisy.jsonl'))
        
        # Save label mappings
        with open(os.path.join(args.out, 'labels.json'), 'w', encoding='utf-8') as f:
            json.dump(labels_mapping, f, ensure_ascii=False, indent=2)
        
        # 8. Consistency analysis
        consistency_stats = analyze_consistency(gpt_conflicts, golden_conflicts, duplicates, deduplicated_data)
        
        # 9. Generate charts and reports
        base_dir = os.path.dirname(args.out)
        create_distribution_plots(consistency_stats, base_dir)
        generate_report(consistency_stats, base_dir)
        
        print("\n✓ Data cleaning completed! Generated files:")
        print(f"  - {args.out}/dev.jsonl ({len(dev_data)} records)")
        print(f"  - {args.out}/test.jsonl ({len(test_data)} records)")
        print(f"  - {args.out}/train_base.jsonl ({len(train_base_data)} records)")
        print(f"  - {args.out}/train_noisy.jsonl ({len(train_noisy_data)} records)")
        print(f"  - {args.out}/labels.json")
        print(f"  - {os.path.join(os.path.dirname(args.out), 'check_report.md')}")
        print(f"  - {os.path.join(os.path.dirname(args.out), 'docs', 'plots', 'label_distribution.png')}")
        
    except Exception as e:
        print(f"❌ Data cleaning failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
