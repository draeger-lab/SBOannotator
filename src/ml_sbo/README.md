# 🚀 SBO Biochemical Reaction Classification System

A deep learning-based automatic classification system for SBO (Systems Biology Ontology) biochemical reactions, supporting 42 SBO classification categories.

## 📁 Project Structure

```
ml_sbo/
├── src/                          # Core code
│   ├── prepare.py               # Data preprocessing
│   ├── train.py                 # Model training
│   └── infer.py                 # Inference prediction
├── models/                      # Trained models
│   └── stage1_80_stage2_10/    # Recommended model
├── data/                        # Data files
│   ├── train_base.jsonl
│   ├── dev.jsonl
│   ├── test.jsonl
│   └── labels.json
└── README.md                    # This file
