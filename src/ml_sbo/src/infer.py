#!/usr/bin/env python3


import torch
import torch.nn.functional as F
import json
import argparse
import os
import pandas as pd
from transformers import AutoTokenizer
import warnings

warnings.filterwarnings("ignore")

# Import training modules
try:
    from train import SBOClassifier
except ImportError:
    from .train import SBOClassifier


class SBOInferencer:
    """
    SBO Classification Inference Engine
    
    Input: Model checkpoint path and device configuration
    Output: SBO classification predictions with confidence scores and explanations
    Purpose: Performs inference on EC numbers and reaction descriptions to predict appropriate SBO terms
    """
    
    def __init__(self, ckpt_path, device=None):
        """
        Initialize SBO inference engine.
        
        Input:
            - ckpt_path (str): Path to model checkpoint directory
            - device (torch.device, optional): Device for computation (auto-detects if None)
        
        Output: Initialized SBOInferencer object ready for predictions
        Purpose: Loads trained model, tokenizer, and label mappings for SBO classification
        """
        self.device = device or torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load model
        # print("Loading model...")
        checkpoint = torch.load(
            os.path.join(ckpt_path, 'pytorch_model.bin'), 
            map_location=self.device,
            weights_only=False
        )
        
        # Rebuild configuration and label mappings
        config_dict = checkpoint['config']
        self.config = type('Config', (), config_dict)()
        self.labels_mapping = checkpoint['labels_mapping']
        
        # Create index mappings (using complete 42 labels)
        # JSON saves integer keys as strings, convert back here
        idx2label_raw = self.labels_mapping.get('idx2label', {})
        self.idx2id = {int(k): v for k, v in idx2label_raw.items()}
        self.id2idx = self.labels_mapping.get('label2idx', {})
        self.id2name = self.labels_mapping['id2name']
        self.id2comment = self.labels_mapping['id2comment']
        self.id2is_leaf = self.labels_mapping['id2is_leaf']
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(ckpt_path)
        
        # Rebuild and load model
        self.model = SBOClassifier(self.config).to(self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()
        
        
        # print(f"Model loading completed, supporting {self.config.num_classes} classes")
    
    def extract_keywords(self, text, keywords_probs=None, top_k=5):
        """
        Extract relevant biochemical keywords from input text.
        
        Input:
            - text (str): Input text to analyze
            - keywords_probs (dict, optional): Probability scores for keywords (unused in current implementation)
            - top_k (int): Maximum number of keywords to return
        
        Output: List of relevant keyword strings found in the text
        Purpose: Identifies biochemical terms and processes to support SBO classification reasoning
        """

        # Based on predefined vocabulary
        common_keywords = [
            'acetyl', 'hydroxyl', 'methyl', 'phosphate', 'sulfate',
            'oxidation', 'reduction', 'hydrolysis', 'deamination', 
            'NAD', 'NADP', 'ATP', 'CoA', 'monooxygenase'
        ]
        
        found_keywords = []
        text_lower = text.lower()
        
        for keyword in common_keywords:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
        
        # Limit quantity
        return found_keywords[:top_k]
    
    def generate_reason(self, text, predicted_label, confidence):
        """
        Generate explanation for the prediction reasoning.
        
        Input:
            - text (str): Input text that was classified
            - predicted_label (str): Predicted SBO label ID
            - confidence (float): Prediction confidence score (0-1)
        
        Output: String explanation describing why this label was predicted
        Purpose: Provides interpretable reasoning for SBO classification decisions
        """
        label_name = self.id2name.get(predicted_label, predicted_label)
        
        reasons = []
        
        if 'acetyl' in text.lower():
            reasons.append("Text contains acetylation-related vocabulary")
        if 'hydroxyl' in text.lower() or 'OH' in text:
            reasons.append("Detected hydroxylation-related features")
        if 'NAD' in text or 'NADH' in text:
            reasons.append("Involves NAD(H)-related oxidation-reduction processes")
        if 'phosphat' in text.lower():
            reasons.append("Contains phosphorylation-related information")
        if 'oxidation' in text.lower() or 'reduction' in text.lower():
            reasons.append("Clear oxidation-reduction reaction indicators")
        
        if reasons:
            base_reason = "; ".join(reasons)
        else:
            base_reason = f"Based on text feature analysis, matches typical patterns of {label_name}"
        
        # Add confidence information
        if confidence >= 0.9:
            confidence_desc = "with very high confidence"
        elif confidence >= 0.7:
            confidence_desc = "with high confidence"
        else:
            confidence_desc = "with low confidence"
        
        return f"{base_reason}, predicted {confidence_desc}."
    
    def predict(self, input_data, top_k=3, need_reason=True, 
                need_keywords=True):
        """
        Execute SBO classification prediction with support for multiple input formats.
        
        Input:
            - input_data (dict or str): Input data in new structured format or legacy text format
            - top_k (int): Number of top prediction alternatives to return
            - need_reason (bool): Whether to generate explanation reasoning
            - need_keywords (bool): Whether to extract keywords from text
        
        Output: Dictionary containing predicted SBO ID, confidence, alternatives, reasoning, and keywords
        Purpose: Main prediction method that processes EC numbers and descriptions to predict SBO terms
        """
        
        # Parse input data format
        if isinstance(input_data, dict) and 'reaction_id' in input_data:
            # New dictionary format
            reaction_data = input_data['reaction_id']
            ec_text = reaction_data.get('ec_text_to_llm', '')
            ec_num = reaction_data.get('ec_to_llm', '')
            processed_text = f"EC {ec_num}: {ec_text}" if ec_text else ec_num
            reaction_id = reaction_data.get('reaction_id', 'unknown')
            original_sbo = reaction_data.get('original_sbo', '')
        else:
            # Compatible with old text format
            processed_text = input_data if isinstance(input_data, str) else str(input_data)
            reaction_id = 'legacy_input'
            original_sbo = ''
        
        # Tokenization and encoding
        encoding = self.tokenizer(
            processed_text,
            truncation=True,
            padding='max_length',
            max_length=512,
            return_tensors='pt'
        )
        
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)
        
        # Model inference
        with torch.no_grad():
            outputs = self.model(input_ids, attention_mask)
            logits = outputs['class_logits']
            
            temperature = 1.2
            calibrated_logits = logits / temperature
            probs = F.softmax(calibrated_logits, dim=-1)
        
        # Get Top-K predictions
        top_probs, top_indices = torch.topk(probs, k=min(top_k, probs.size(-1)), dim=-1)
        top_probs = top_probs.squeeze().cpu().numpy()
        top_indices = top_indices.squeeze().cpu().numpy()
        
        # Build alternatives list
        alternatives = []
        for i, (idx, prob) in enumerate(zip(top_indices, top_probs)):
            label_id = self.idx2id[idx]
            label_name = self.id2name.get(label_id, label_id)
            
            alternatives.append({
                "label_id": label_id,
                "label_name": label_name,
                "confidence": float(prob)
            })
        
        # Return top1 result directly
        max_confidence = float(top_probs[0])
        predicted_id = alternatives[0]["label_id"]
        predicted_name = alternatives[0]["label_name"]
        prediction_status = "CONFIDENT"
        
        # Generate keywords
        keywords = []
        if need_keywords:
            keywords = self.extract_keywords(processed_text)
        
        # Generate reasoning
        reason = ""
        if need_reason:
            if prediction_status == "CONFIDENT":
                reason = self.generate_reason(processed_text, predicted_id, max_confidence)
        
        # Build complete structure after LLM processing
        if isinstance(input_data, dict) and 'reaction_id' in input_data:
            # Retain all fields before LLM input, add recommended fields after LLM processing
            result = {
                'reaction_id': {
                    # Retain all original input fields
                    'reaction_id': input_data['reaction_id'].get('reaction_id', ''),
                    'original_sbo': input_data['reaction_id'].get('original_sbo', ''),
                    'original_sbo_term': input_data['reaction_id'].get('original_sbo_term', ''),
                    'original_sbo_comment': input_data['reaction_id'].get('original_sbo_comment', ''),
                    'original_sbo_is_leaf': input_data['reaction_id'].get('original_sbo_is_leaf', False),
                    'ec_numbers': input_data['reaction_id'].get('ec_numbers', []),
                    'ec_to_llm': input_data['reaction_id'].get('ec_to_llm', ''),
                    'ec_text_to_llm': input_data['reaction_id'].get('ec_text_to_llm', ''),
                    # Add LLM recommended SBO information
                    'recommended_sbo_id': predicted_id,
                    'recommend_sbo_term': predicted_name,
                    'recommend_sbo_comment': self.id2comment.get(predicted_id, ""),
                    'recommend_sbo_is_leaf': self.id2is_leaf.get(predicted_id, False),
                    'recommend_sbo_reason': reason
                }
            }
        else:
            # Compatible with old format output
            result = {
                "label_id": predicted_id,
                "label_name": predicted_name,
                "confidence": max_confidence,
                "prediction_status": prediction_status,
                "alternatives": alternatives,
                "reason": reason,
                "keywords": keywords,
            }
        
        return result


def main():
    """
    Command-line interface for SBO classification inference.
    
    Input: Command line arguments specifying model path and input data
    Output: Prints classification results to console
    Purpose: Provides CLI access to SBO classification functionality for batch processing
    """
    parser = argparse.ArgumentParser(description='SBO Classification Inference CLI')
    
    # Required parameters
    parser.add_argument('--ckpt', required=True, help='Model checkpoint path')
    
    # Input parameters (supports two formats)
    parser.add_argument('--text', help='Text to be classified (old format)')
    parser.add_argument('--input_file', help='Input JSON file (new format)')
    parser.add_argument('--ec_num', help='EC number (new format)')
    parser.add_argument('--ec_text', help='EC text description (new format)')
    
    # Optional parameters
    parser.add_argument('--sbo_id', help='Optional SBO ID context')
    parser.add_argument('--top_k', type=int, default=3, help='Number of candidates to return')
    parser.add_argument('--need_reason', action='store_true', default=True, help='Whether to generate explanation reasoning')
    parser.add_argument('--need_keywords', action='store_true', default=True, help='Whether to extract keywords')
    
    # Output format
    parser.add_argument('--output_format', choices=['json', 'pretty'], default='pretty', 
                        help='Output format')
    
    args = parser.parse_args()
    
    try:
        # Create inferencer
        inferencer = SBOInferencer(args.ckpt)
        
        # Prepare input data
        if args.input_file:
            # Read new format input from file
            with open(args.input_file, 'r', encoding='utf-8') as f:
                input_data = json.load(f)
        elif args.ec_num and args.ec_text:
            # Build new format input from command line
            input_data = {
                'reaction_id': {
                    'reaction_id': f"cli_{args.ec_num}",
                    'original_sbo': args.sbo_id or "SBO:0000000",
                    'original_sbo_term': "unknown",
                    'original_sbo_comment': "unknown",
                    'original_sbo_is_leaf': False,
                    'ec_numbers': [args.ec_num],
                    'ec_to_llm': args.ec_num,
                    'ec_text_to_llm': args.ec_text
                }
            }
        elif args.text:

            input_data = args.text
        else:
            raise ValueError("Must provide one of: --text, --input_file, or --ec_num + --ec_text")
        
        # Execute inference
        result = inferencer.predict(
            input_data=input_data,
            top_k=args.top_k,
            need_reason=args.need_reason,
            need_keywords=args.need_keywords,
        )
        
        # Output dictionary directly
        print(result)
        
    except Exception as e:
        print(f"❌ Inference failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
