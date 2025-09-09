#!/usr/bin/env python3


import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer, AutoModel, AutoConfig,
    get_linear_schedule_with_warmup
)
from torch.optim import AdamW
import json
import copy
import argparse
import os
import numpy as np
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import classification_report, f1_score
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
from tqdm import tqdm
import warnings

warnings.filterwarnings("ignore")


class SBODataset(Dataset):
    """
    SBO classification dataset for loading and preprocessing training data.
    
    Input: JSONL file with reaction data, tokenizer, labels mapping, max sequence length
    Output: Tokenized sequences with labels, keywords, and metadata for model training
    Function: Processes EC numbers and text descriptions into model-ready format
    """
    
    def __init__(self, jsonl_path, tokenizer, labels_mapping, max_length=512):
        """
        Initialize the SBO dataset.
        
        Input:
            - jsonl_path (str): Path to JSONL file containing training data
            - tokenizer: HuggingFace tokenizer for text encoding
            - labels_mapping (dict): Mapping between SBO IDs and indices
            - max_length (int): Maximum sequence length for tokenization
        
        Output: Initialized dataset object with loaded and preprocessed data
        Function: Loads reaction data and prepares it for model training
        """
        self.tokenizer = tokenizer
        self.max_length = max_length
        # Use complete 42 label mappings
        self.label2idx = labels_mapping['label2idx']
      
        self.idx2label = {int(k): v for k, v in labels_mapping['idx2label'].items()}
        self.id2is_leaf = labels_mapping['id2is_leaf']
        self.data = []
        
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                item = json.loads(line.strip())
                
                reaction_data = item['reaction_id']
                label_id = reaction_data['recommended_sbo_id']
                
                if label_id in self.label2idx:  # Ensure label is in mapping
                    # Build input text
                    ec_text = reaction_data.get('ec_text_to_llm', '')
                    ec_num = reaction_data.get('ec_to_llm', '')
                    input_text = f"EC {ec_num}: {ec_text}" if ec_text else ec_num
                    
                    # Build training sample
                    train_item = {
                        'reaction_id': reaction_data['reaction_id'],
                        'text': input_text,
                        'label_id': label_id,
                        'label_idx': self.label2idx[label_id],
                        'is_leaf': self.id2is_leaf[label_id],
                        'keywords': reaction_data.get('keywords', []),
                        'reason': reaction_data.get('recommend_sbo_reason', ''),
                        'source': reaction_data.get('source', 'unknown')
                    }
                    self.data.append(train_item)
        
        print(f"Loading data: {jsonl_path} - {len(self.data)} records")
    
    def __len__(self):
        """
        Get dataset size.
        
        Input: None
        Output: int - Number of samples in dataset
        Function: Returns total number of training samples
        """
        return len(self.data)
    
    def __getitem__(self, idx):
        """
        Get a single training sample by index.
        
        Input: idx (int) - Index of the sample to retrieve
        Output: Dictionary containing input_ids, attention_mask, labels, keywords_labels, reason, is_leaf
        Function: Tokenizes text and returns model-ready tensors for training
        """
        item = self.data[idx]
        
        # Text encoding
        encoding = self.tokenizer(
            item['text'],
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        # Labels (using precomputed indices)
        label_idx = item['label_idx']
        
        # Keywords multi-labels (if available)
        keywords_labels = self._encode_keywords(item.get('keywords', []))
        
        return {
            'input_ids': encoding['input_ids'].squeeze(),
            'attention_mask': encoding['attention_mask'].squeeze(),
            'labels': torch.tensor(label_idx, dtype=torch.long),
            'keywords_labels': keywords_labels,
            'reason': item.get('reason', ''),
            'is_leaf': torch.tensor(item.get('is_leaf', 0), dtype=torch.long),
        }
    
    def _encode_keywords(self, keywords):
        """
        Encode keywords into multi-label binary vector.
        
        Input: keywords (list) - List of keyword strings
        Output: torch.Tensor - Binary vector of shape (num_keywords,) indicating presence of each keyword
        Function: Converts keyword list to fixed-size binary encoding for multi-label prediction
        """
        common_keywords = [
            'acetyl', 'hydroxyl', 'methyl', 'phosphate', 'sulfate',
            'oxidation', 'reduction', 'hydrolysis', 'deamination', 
            'NAD', 'NADP', 'ATP', 'CoA', 'monooxygenase'
        ]
        
        labels = torch.zeros(len(common_keywords), dtype=torch.float)
        for i, keyword in enumerate(common_keywords):
            if any(keyword.lower() in kw.lower() for kw in keywords):
                labels[i] = 1.0
        
        return labels


class FocalLoss(nn.Module):
    """
    Focal Loss implementation for handling class imbalance in classification.
    
    Input: Model logits and true labels
    Output: Computed focal loss value
    Function: Applies focal weighting to cross-entropy loss to focus on hard examples
    """
    
    def __init__(self, alpha=1, gamma=2, reduction='mean'):
        """
        Initialize Focal Loss.
        
        Input:
            - alpha (float): Weighting factor for rare class
            - gamma (float): Focusing parameter (higher = more focus on hard examples)
            - reduction (str): How to reduce the loss ('mean', 'sum', 'none')
        
        Output: Initialized FocalLoss module
        Function: Sets up focal loss parameters for class imbalance handling
        """
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction
    
    def forward(self, inputs, targets):
        """
        Compute focal loss.
        
        Input:
            - inputs (torch.Tensor): Model logits of shape (batch_size, num_classes)
            - targets (torch.Tensor): True class indices of shape (batch_size,)
        
        Output: torch.Tensor - Computed focal loss
        Function: Applies focal weighting to cross-entropy loss to handle class imbalance
        """
        ce_loss = F.cross_entropy(inputs, targets, reduction='none')
        pt = torch.exp(-ce_loss)
        focal_loss = self.alpha * (1-pt)**self.gamma * ce_loss
        
        if self.reduction == 'mean':
            return focal_loss.mean()
        elif self.reduction == 'sum':
            return focal_loss.sum()
        else:
            return focal_loss


class SBOClassifier(nn.Module):
    """
    Multi-task SBO classifier with main classification and keyword prediction.
    
    Input: Tokenized sequences with attention masks
    Output: Class logits, keyword predictions, attention weights
    Function: Performs SBO classification and auxiliary keyword prediction tasks
    """
    
    def __init__(self, config):
        """
        Initialize the SBO classifier model.
        
        Input: config (Config) - Configuration object with model parameters
        Output: Initialized SBOClassifier model
        Function: Sets up encoder, classification head, keyword head, and attention mechanism
        """
        super(SBOClassifier, self).__init__()
        
        # Encoder
        self.encoder = AutoModel.from_pretrained(config.encoder_name)
        hidden_size = self.encoder.config.hidden_size
        
        # Classification head
        self.classifier = nn.Sequential(
            nn.Dropout(config.dropout),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(hidden_size // 2, config.num_classes)
        )
        
        # Keywords multi-label head
        self.keywords_classifier = nn.Sequential(
            nn.Dropout(config.dropout),
            nn.Linear(hidden_size, config.num_keywords),
            nn.Sigmoid()
        )
        
        self.reason_head = nn.MultiheadAttention(
            hidden_size, num_heads=8, batch_first=True
        )
        
        self.config = config
        
        # Leaf/Non-leaf weights (for priority loss)
        if hasattr(config, 'labels_mapping'):
            self.leaf_weight = getattr(config, 'leaf_weight', 1.0)
            self.non_leaf_weight = getattr(config, 'non_leaf_weight', 0.5)
            self.labels_mapping = config.labels_mapping.copy()
            # JSON saves integer keys as strings, convert back here
            self.labels_mapping['idx2label'] = {int(k): v for k, v in self.labels_mapping['idx2label'].items()}
    
    def forward(self, input_ids, attention_mask, labels=None, keywords_labels=None):
        """
        Forward pass through the model.
        
        Input:
            - input_ids (torch.Tensor): Tokenized input sequences
            - attention_mask (torch.Tensor): Attention mask for padding
            - labels (torch.Tensor, optional): True class labels for loss computation
            - keywords_labels (torch.Tensor, optional): True keyword labels for auxiliary loss
        
        Output: Dictionary containing class_logits, keywords_logits, attention_weights, loss (if labels provided)
        Function: Performs forward pass and computes multi-task loss if training
        """
        # Encoding
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        sequence_output = outputs.last_hidden_state  # [batch, seq_len, hidden]
        pooled_output = outputs.pooler_output if hasattr(outputs, 'pooler_output') else outputs.last_hidden_state[:, 0]
        
        # Classification prediction
        class_logits = self.classifier(pooled_output)
        
        # Keywords prediction  
        keywords_logits = self.keywords_classifier(pooled_output)
        
        reason_attn, _ = self.reason_head(sequence_output, sequence_output, sequence_output)
        
        outputs = {
            'class_logits': class_logits,
            'keywords_logits': keywords_logits,
            'attention_weights': reason_attn,
            'hidden_states': sequence_output
        }
        
        # Compute loss
        if labels is not None:
            loss = 0.0
            
            # Classification loss (with leaf/non-leaf priority)
            if hasattr(self, 'labels_mapping'):
                # Calculate sample weights: leaf categories high weight, non-leaf categories low weight
                sample_weights = torch.ones_like(labels, dtype=torch.float)
                for i, label_idx in enumerate(labels):
                    label_id = self.labels_mapping['idx2label'][label_idx.item()]
                    is_leaf = self.labels_mapping['id2is_leaf'][label_id]
                    sample_weights[i] = self.leaf_weight if is_leaf else self.non_leaf_weight
                
                # Use weighted loss
                if self.config.use_focal:
                    criterion = FocalLoss(gamma=2.0)
                    base_loss = criterion(class_logits, labels)
                    class_loss = (base_loss * sample_weights).mean()
                else:
                    criterion = nn.CrossEntropyLoss(reduction='none')
                    base_loss = criterion(class_logits, labels)
                    class_loss = (base_loss * sample_weights).mean()
            else:
                # Standard loss computation (backward compatibility)
                if self.config.use_focal:
                    criterion = FocalLoss(gamma=2.0)
                    class_loss = criterion(class_logits, labels)
                else:
                    if self.config.class_weights is not None:
                        weights = torch.tensor(self.config.class_weights, device=class_logits.device)
                        criterion = nn.CrossEntropyLoss(weight=weights)
                    else:
                        criterion = nn.CrossEntropyLoss()
                    class_loss = criterion(class_logits, labels)
            
            loss += class_loss
            
            # Keywords loss
            if keywords_labels is not None:
                keywords_loss = F.binary_cross_entropy(keywords_logits, keywords_labels)
                loss += 0.3 * keywords_loss
            
            outputs['loss'] = loss
            outputs['class_loss'] = class_loss
        
        return outputs


class Config:
    """
    Training configuration class.
    
    Input: Command line arguments from argparse
    Output: Configured training parameters
    Function: Stores and manages all training hyperparameters and settings
    """
    def __init__(self, args):
        """
        Initialize training configuration.
        
        Input: args (argparse.Namespace) - Command line arguments
        Output: Configured Config object with all training parameters
        Function: Sets up model architecture, training, and optimization parameters
        """
        self.encoder_name = args.encoder
        self.num_classes = None  # Set when loading data
        self.num_keywords = 14  # Number of predefined keywords
        self.dropout = args.dropout
        self.use_focal = args.use_focal
        self.class_weights = None
        
        # Training parameters
        self.batch_size = args.batch_size
        self.learning_rate = args.learning_rate
        self.epochs = args.epochs
        # Stage-wise training epochs
        self.stage1_epochs = args.stage1_epochs if args.stage1_epochs is not None else args.epochs
        self.stage2_epochs = args.stage2_epochs if args.stage2_epochs is not None else args.epochs
        self.warmup_ratio = 0.1
        
        # Noise handling
        self.noise_adapt = args.noise_adapt
        self.noise_ratio = args.noise_ratio
        self.label_smoothing = args.label_smoothing
        self.top_k_loss = args.top_k_loss
        
        # Leaf/Non-leaf priority weights
        self.leaf_weight = getattr(args, 'leaf_weight', 1.0)
        self.non_leaf_weight = getattr(args, 'non_leaf_weight', 0.5)
        self.labels_mapping = None  # Will be set during training


def load_data(data_dir):
    """
    Load training data and label mappings.
    
    Input: data_dir (str) - Directory containing labels.json file
    Output: dict - Labels mapping with SBO ID to index conversions
    Function: Loads label mappings for SBO classification from JSON file
    """
    print("Loading data...")
    
    # Load label mappings
    with open(os.path.join(data_dir, 'labels.json'), 'r', encoding='utf-8') as f:
        labels_mapping = json.load(f)
    
    return labels_mapping


def compute_class_weights_from_data(train_data_path, labels_mapping):
    """
    Compute class weights from training data for handling class imbalance.
    
    Input:
        - train_data_path (str): Path to training JSONL file
        - labels_mapping (dict): Label mapping dictionary
    
    Output: list or None - Computed class weights for balanced training
    Function: Calculates inverse frequency weights to balance class distribution
    """
    label_counts = Counter()
    
    with open(train_data_path, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line.strip())
            label_counts[item['label_id']] += 1
    
    # Convert to index counts
    used_labels = labels_mapping['used_labels']
    id2idx = {label_id: idx for idx, label_id in enumerate(used_labels)}
    
    y = []
    for label_id, count in label_counts.items():
        if label_id in id2idx:
            y.extend([id2idx[label_id]] * count)
    
    if len(y) > 0:
        class_weights = compute_class_weight(
            'balanced', classes=np.unique(y), y=y
        )
        return class_weights.tolist()
    
    return None


def create_data_loaders(data_dir, tokenizer, labels_mapping, config):
    """
    Create PyTorch data loaders for training, validation, and noisy data.
    
    Input:
        - data_dir (str): Directory containing train/dev/test JSONL files
        - tokenizer: HuggingFace tokenizer
        - labels_mapping (dict): Label mapping dictionary
        - config (Config): Training configuration
    
    Output: tuple - (train_loader, dev_loader, noisy_loader)
    Function: Creates batched data loaders for multi-stage training
    """
    print("Creating data loaders...")
    
    # Training set
    train_dataset = SBODataset(
        os.path.join(data_dir, 'train_base.jsonl'),
        tokenizer, labels_mapping
    )
    
    # Validation set
    dev_dataset = SBODataset(
        os.path.join(data_dir, 'dev.jsonl'),
        tokenizer, labels_mapping
    )
    
    # Noise training set (for second stage use)
    noisy_dataset = None
    if config.noise_adapt:
        noisy_dataset = SBODataset(
            os.path.join(data_dir, 'train_noisy.jsonl'),
            tokenizer, labels_mapping
        )
    
    train_loader = DataLoader(train_dataset, batch_size=config.batch_size, shuffle=True)
    dev_loader = DataLoader(dev_dataset, batch_size=config.batch_size, shuffle=False)
    noisy_loader = DataLoader(noisy_dataset, batch_size=config.batch_size, shuffle=True) if noisy_dataset else None
    
    return train_loader, dev_loader, noisy_loader


def evaluate_model(model, data_loader, device):
    """
    Evaluate model performance on given dataset.
    
    Input:
        - model (SBOClassifier): Trained model to evaluate
        - data_loader (DataLoader): Data loader for evaluation dataset
        - device (torch.device): Device for computation
    
    Output: tuple - (avg_loss, f1_score, predictions, true_labels)
    Function: Computes loss, F1 score and collects predictions for performance analysis
    """
    model.eval()
    all_preds = []
    all_labels = []
    total_loss = 0.0
    
    with torch.no_grad():
        for batch in tqdm(data_loader, desc="Evaluating"):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device) 
            labels = batch['labels'].to(device)
            keywords_labels = batch['keywords_labels'].to(device)
            
            outputs = model(input_ids, attention_mask, labels, keywords_labels)
            
            total_loss += outputs['loss'].item()
            preds = torch.argmax(outputs['class_logits'], dim=-1)
            
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    avg_loss = total_loss / len(data_loader)
    f1 = f1_score(all_labels, all_preds, average='macro')
    
    return avg_loss, f1, all_preds, all_labels


def final_evaluation(model, data_dir, tokenizer, labels_mapping, device, best_f1, stage_name="Final"):
    """
    Comprehensive evaluation after training completion.
    
    Input:
        - model (SBOClassifier): Trained model
        - data_dir (str): Directory containing test data
        - tokenizer: HuggingFace tokenizer
        - labels_mapping (dict): Label mappings
        - device (torch.device): Computation device
        - best_f1 (float): Best F1 score achieved during training
        - stage_name (str): Name of training stage for reporting
    
    Output: None (prints detailed evaluation metrics)
    Function: Performs detailed evaluation including classification report, top-K accuracy, confidence statistics
    """
    from sklearn.metrics import classification_report, confusion_matrix
    import numpy as np
    
    print("=" * 60)
    print(f"🎯 {stage_name} Model Performance Evaluation")
    print("=" * 60)
    
    # Load test data
    test_dataset = SBODataset(
        os.path.join(data_dir, 'test.jsonl'),
        tokenizer, labels_mapping
    )
    test_loader = DataLoader(test_dataset, batch_size=16, shuffle=False)
    
    # Validation set evaluation
    dev_dataset = SBODataset(
        os.path.join(data_dir, 'dev.jsonl'),
        tokenizer, labels_mapping
    )
    dev_loader = DataLoader(dev_dataset, batch_size=16, shuffle=False)
    
    print(f"📊 Validation set sample count: {len(dev_dataset)}")
    print(f"📊 Test set sample count: {len(test_dataset)}")
    
    # Evaluate validation set
    dev_loss, dev_f1, dev_preds, dev_labels = evaluate_model(model, dev_loader, device)
    print(f"\n✅ Validation set performance:")
    print(f"   Loss: {dev_loss:.4f}")
    print(f"   F1-Score: {dev_f1:.4f} (best during training: {best_f1:.4f})")
    
    # Evaluate test set
    test_loss, test_f1, test_preds, test_labels = evaluate_model(model, test_loader, device)
    print(f"\n🏆 Test set performance:")
    print(f"   Loss: {test_loss:.4f}")
    print(f"   F1-Score: {test_f1:.4f}")
    
    # Detailed classification report (test set only)
    model.eval()
    all_preds = []
    all_labels = []
    all_probs = []
    
    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            keywords_labels = batch['keywords_labels'].to(device)
            
            outputs = model(input_ids, attention_mask, labels, keywords_labels)
            probs = torch.softmax(outputs['class_logits'], dim=-1)
            preds = torch.argmax(outputs['class_logits'], dim=-1)
            
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())
    
    # Get class names
    used_labels = labels_mapping['used_labels']
    label_names = [used_labels[i] for i in range(len(used_labels))]
    
    # Classification report
    print(f"\n📋 Detailed classification report:")
    print("=" * 80)
    
    try:
        report = classification_report(
            all_labels, all_preds, 
            target_names=label_names,
            labels=list(range(len(label_names))),
            zero_division=0,
            digits=4
        )
        print(report)
    except Exception as e:
        print(f"⚠️  Classification report generation failed: {str(e)}")
    
    # Top-K accuracy
    all_probs = np.array(all_probs)
    all_labels = np.array(all_labels)
    
    # Top-1 accuracy
    top1_acc = np.mean(np.argmax(all_probs, axis=1) == all_labels)
    
    # Top-3 accuracy
    top3_preds = np.argsort(all_probs, axis=1)[:, -3:]
    top3_acc = np.mean([label in top3_preds[i] for i, label in enumerate(all_labels)])
    
    print(f"\n🎯 Top-K accuracy:")
    print(f"   Top-1: {top1_acc:.4f}")
    print(f"   Top-3: {top3_acc:.4f}")
    
    # Confidence statistics
    max_probs = np.max(all_probs, axis=1)
    print(f"\n📈 Confidence statistics:")
    print(f"   Average confidence: {np.mean(max_probs):.4f}")
    print(f"   Median confidence: {np.median(max_probs):.4f}")
    print(f"   Minimum confidence: {np.min(max_probs):.4f}")
    print(f"   Maximum confidence: {np.max(max_probs):.4f}")
    
    print("=" * 60)
    print("✅ Evaluation completed!")
    print("=" * 60)


def train_stage(model, train_loader, dev_loader, config, device, stage_name="Stage1", custom_epochs=None):
    """
    Train model for a single stage with given data loader.
    
    Input:
        - model (SBOClassifier): Model to train
        - train_loader (DataLoader): Training data loader
        - dev_loader (DataLoader): Validation data loader
        - config (Config): Training configuration
        - device (torch.device): Computation device
        - stage_name (str): Name of training stage
        - custom_epochs (int, optional): Override number of epochs
    
    Output: tuple - (training_history, best_f1, best_model_state)
    Function: Executes training loop with optimization, validation, and best model saving
    """
    epochs = custom_epochs if custom_epochs is not None else config.epochs
    print(f"\n=== {stage_name} Training Start ===({epochs} epochs)")
    
    # Optimizer and scheduler
    optimizer = AdamW(model.parameters(), lr=config.learning_rate)
    
    total_steps = len(train_loader) * epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer, 
        num_warmup_steps=int(total_steps * config.warmup_ratio),
        num_training_steps=total_steps
    )
    
    best_f1 = 0.0
    best_model_state = None
    training_history = []
    
    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        
        progress_bar = tqdm(train_loader, desc=f"{stage_name} Epoch {1+1}/{epochs}")
        
        for batch in progress_bar:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            keywords_labels = batch['keywords_labels'].to(device)
            
            optimizer.zero_grad()
            
            outputs = model(input_ids, attention_mask, labels, keywords_labels)
            loss = outputs['loss']
            
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            
            total_loss += loss.item()
            progress_bar.set_postfix({'loss': loss.item()})
        
        avg_train_loss = total_loss / len(train_loader)
        
        # Validation
        dev_loss, dev_f1, _, _ = evaluate_model(model, dev_loader, device)
        
        print(f"Epoch {epoch+1}/{epochs}:")
        print(f"  Train Loss: {avg_train_loss:.4f}")
        print(f"  Dev Loss: {dev_loss:.4f}")
        print(f"  Dev F1: {dev_f1:.4f}")
        
        # Record training history
        training_history.append({
            'epoch': epoch + 1,
            'train_loss': avg_train_loss,
            'dev_loss': dev_loss,
            'dev_f1': dev_f1
        })
        
        # Save best model
        if dev_f1 > best_f1:
            best_f1 = dev_f1
            best_model_state = copy.deepcopy(model.state_dict())
            print(f"  ✓ New best F1: {best_f1:.4f}")
    
    print(f"{stage_name} completed, best F1: {best_f1:.4f}")
    return training_history, best_f1, best_model_state


def train_model(config, data_dir, output_dir):
    """
    Main training pipeline with two-stage training strategy.
    
    Input:
        - config (Config): Training configuration
        - data_dir (str): Directory containing training data
        - output_dir (str): Directory to save trained model
    
    Output: tuple - (trained_model, tokenizer, labels_mapping)
    Function: Orchestrates complete training process including data loading, two-stage training, and model saving
    """
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    # Load data
    labels_mapping = load_data(data_dir)
    config.num_classes = len(labels_mapping['all_labels'])  # Use complete 42 classes
    print(f"Number of classes: {config.num_classes} (includes all SBO labels)")
    print(f"  - Used in data: {len(labels_mapping['used_labels'])}")
    print(f"  - Leaf labels: {len(labels_mapping['leaf_labels'])}")
    print(f"  - Non-leaf labels: {len(labels_mapping['non_leaf_labels'])}")
    
    # Calculate class weights
    if not config.use_focal:
        class_weights = compute_class_weights_from_data(
            os.path.join(data_dir, 'train_base.jsonl'),
            labels_mapping
        )
        config.class_weights = class_weights
        print(f"Class weights calculated: {len(class_weights) if class_weights else 0} classes")
    
    # Set label mappings in configuration
    config.labels_mapping = labels_mapping
    
    # Initialize tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(config.encoder_name)
    model = SBOClassifier(config).to(device)
    
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Create data loaders
    train_loader, dev_loader, noisy_loader = create_data_loaders(
        data_dir, tokenizer, labels_mapping, config
    )
    
    # Stage 1: Basic training (clean data)
    print(f"\n🚀 Starting Stage1 training - {config.stage1_epochs} epochs")
    stage1_history, stage1_best_f1, stage1_best_state = train_stage(
        model, train_loader, dev_loader, config, device, "Stage1-Base", config.stage1_epochs
    )
    
    # Evaluation after Stage1 completion
    print(f"\n🎯 Stage1 training completion evaluation")
    print("=" * 50)
    final_evaluation(model, data_dir, tokenizer, labels_mapping, device, stage1_best_f1, "Stage1")
    
    # Initialize global best model
    global_best_f1 = stage1_best_f1
    global_best_state = stage1_best_state
    
    # Stage 2: Noise adaptive training (if enabled)
    stage2_history = []
    if config.noise_adapt and noisy_loader:
        print(f"\n=== Stage2 Noise Adaptive Training ===")
        
        # Reduce learning rate
        config.learning_rate *= 0.1
        
        # Combine clean data and noise data
        combined_loader = train_loader  
        
        print(f"\n🚀 Starting Stage2 training - {config.stage2_epochs} epochs")
        stage2_history, stage2_best_f1, stage2_best_state = train_stage(
            model, noisy_loader, dev_loader, config, device, "Stage2-NoiseAdapt", config.stage2_epochs
        )
        
        # Evaluation after Stage2 completion
        print(f"\n🎯 Stage2 training completion evaluation")
        print("=" * 50)
        final_evaluation(model, data_dir, tokenizer, labels_mapping, device, stage2_best_f1, "Stage2")
        
        # Update global best model (if Stage2 is better)
        if stage2_best_f1 > global_best_f1:
            global_best_f1 = stage2_best_f1
            global_best_state = stage2_best_state
            print(f"\n✓ Stage2 exceeds Stage1, global best F1: {global_best_f1:.4f}")
        else:
            print(f"\n✓ Stage1 remains best, global best F1: {global_best_f1:.4f}")
    
    # Save model and results
    os.makedirs(output_dir, exist_ok=True)
    
    # Save best model (not the last model)
    if global_best_state is not None:
        print(f"\n✓ Saving global best model (F1: {global_best_f1:.4f})")
        model.load_state_dict(global_best_state)
    
    # 保存模型
    model.save_pretrained = lambda path: torch.save({
        'model_state_dict': model.state_dict(),
        'config': config.__dict__,
        'labels_mapping': labels_mapping,
        'best_f1': global_best_f1
    }, os.path.join(path, 'pytorch_model.bin'))
    
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    # Save training history
    training_log = {
        'stage1_history': stage1_history,
        'stage2_history': stage2_history,
        'config': config.__dict__,
        'num_classes': config.num_classes,
        'class_weights': config.class_weights
    }
    
    log_dir = os.path.join(os.path.dirname(output_dir), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    with open(os.path.join(log_dir, 'metrics.json'), 'w', encoding='utf-8') as f:
        json.dump(training_log, f, ensure_ascii=False, indent=2)
    
    # Save class weights
    if config.class_weights:
        with open(os.path.join(os.path.dirname(output_dir), 'class_weight.json'), 'w') as f:
            json.dump({
                'class_weights': config.class_weights,
                'labels': labels_mapping['used_labels']
            }, f, indent=2)
    
    print(f"\n✓ Training completed! Model saved to: {output_dir}")
    print(f"✓ Training log saved to: {log_dir}/metrics.json")
    
    # Immediately perform final evaluation
    print(f"\n🔍 Starting final model evaluation...")
    final_evaluation(model, data_dir, tokenizer, labels_mapping, device, global_best_f1, "Final")
    
    return model, tokenizer, labels_mapping


def main():
    """
    Main entry point for training script.
    
    Input: Command line arguments via argparse
    Output: None (saves trained model and logs)
    Function: Parses arguments, creates configuration, and launches training pipeline
    """
    parser = argparse.ArgumentParser(description='SBO two-stage training')
    
    # Data and model parameters
    parser.add_argument('--data', required=True, help='Data directory path')
    parser.add_argument('--out', required=True, help='Output model directory path')
    parser.add_argument('--encoder', default='distilbert-base-uncased', 
                        help='Pretrained encoder model (default: distilbert-base-uncased)')
    
    # Training parameters
    parser.add_argument('--batch_size', type=int, default=16, help='Batch size')
    parser.add_argument('--learning_rate', type=float, default=2e-5, help='Learning rate')
    parser.add_argument('--epochs', type=int, default=3, help='Training epochs (compatibility preserved)')
    parser.add_argument('--stage1_epochs', type=int, default=None, help='Stage1 training epochs')
    parser.add_argument('--stage2_epochs', type=int, default=None, help='Stage2 training epochs')
    parser.add_argument('--dropout', type=float, default=0.1, help='Dropout rate')
    
    # Loss function options
    parser.add_argument('--use_focal', action='store_true', help='Use Focal Loss')
    
    # Noise handling parameters
    parser.add_argument('--noise_adapt', action='store_true', help='Enable noise adaptive training')
    parser.add_argument('--noise_ratio', type=float, default=0.6, help='Noise sample ratio')
    parser.add_argument('--label_smoothing', type=float, default=0.0, help='Label smoothing coefficient')
    parser.add_argument('--top_k_loss', type=int, default=0, help='Top-K loss filtering')
    
    # Leaf/Non-leaf priority parameters
    parser.add_argument('--leaf_weight', type=float, default=1.0, help='Leaf category weight')
    parser.add_argument('--non_leaf_weight', type=float, default=0.5, help='Non-leaf category weight (as fallback option)')
    
    args = parser.parse_args()
    
    # Create configuration
    config = Config(args)
    
    try:
        # Start training
        model, tokenizer, labels_mapping = train_model(config, args.data, args.out)
        
        print(f"\n🎉 训练成功完成!")
        print(f"📁 模型文件: {args.out}/")
        print(f"📊 训练日志: {os.path.dirname(args.out)}/logs/metrics.json")
        print(f"⚖️ 类权重: {os.path.dirname(args.out)}/class_weight.json")
        
    except Exception as e:
        print(f"❌ Training failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
