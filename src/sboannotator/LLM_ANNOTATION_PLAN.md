# LLM-Based SBO Term Annotation: Implementation Plan

## Overview

This document outlines a plan for implementing an LLM-based annotation assistant for SBOannotator, which will help automatically suggest appropriate Systems Biology Ontology (SBO) terms for reactions in SBML models.

## Project Objectives

1. Create a modular, extensible interface for interacting with different LLM providers
2. Develop intelligent reaction feature extraction for improved term suggestions
3. Design effective prompting strategies for accurate SBO term assignment
4. Integrate the LLM assistant with the existing SBOannotator workflow
5. Evaluate and benchmark the accuracy of LLM-based annotations against existing methods

## Architecture

The solution follows a modular design with clear separation of concerns:

```
                 ┌───────────────────┐
                 │   SBOannotator    │
                 └─────────┬─────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────┐
│          SBOAnnotationAssistant                 │
│                                                 │
│  ┌─────────────────┐      ┌─────────────────┐   │
│  │ Feature         │      │ Response        │   │
│  │ Extraction      │      │ Processing      │   │
│  └─────────────────┘      └─────────────────┘   │
│                                                 │
│  ┌─────────────────┐      ┌─────────────────┐   │
│  │ Prompt          │      │ Suggestion      │   │
│  │ Engineering     │      │ Validation      │   │
│  └─────────────────┘      └─────────────────┘   │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────────────┐
│               LLMProvider (Interface)         │
└───────────────┬───────────────┬───────────────┘
                │               │
    ┌───────────▼────┐  ┌───────▼────────┐
    │ OpenAIProvider │  │ AnthropicProvider │
    └────────────────┘  └──────────────────┘
```

## Implementation Phases

### Phase 1: Foundation (Current PR)

- [x] Design the abstract LLM provider interface
- [x] Create the SBOAnnotationAssistant class with core functionality
- [x] Define placeholder methods for reaction feature extraction and prompt generation
- [x] Outline initial provider implementations for OpenAI and Anthropic

### Phase 2: Feature Extraction

- [ ] Implement comprehensive reaction feature extraction:
    - [ ] Identify metabolite patterns (e.g., ATP/ADP for phosphorylation)
    - [ ] Detect compartment changes for transport reactions
    - [ ] Extract EC numbers from reaction annotations
    - [ ] Analyze reaction reversibility and stoichiometry
    - [ ] Process reaction names for keyword indicators

### Phase 3: Prompt Engineering

- [ ] Develop effective prompting strategies:
    - [ ] Research optimal prompts for biochemical reaction classification
    - [ ] Include relevant SBO term definitions in context
    - [ ] Structure prompts to encourage specific, accurate responses
    - [ ] Optimize for token efficiency
    - [ ] Format instructions for structured output

### Phase 4: Response Processing

- [ ] Create robust response parsing:
    - [ ] Extract recommended SBO terms from LLM output
    - [ ] Handle various response formats gracefully
    - [ ] Parse confidence scores and explanations
    - [ ] Implement fallback logic for ambiguous responses

### Phase 5: Integration & Validation

- [ ] Integrate with SBOannotator:
    - [ ] Add LLM-based annotation as optional enhancement
    - [ ] Implement configuration options for LLM settings
    - [ ] Create hybrid approach that combines rule-based and LLM methods
    - [ ] Develop validation metrics to compare LLM suggestions against existing annotations
    - [ ] Implement benchmark tooling to evaluate different LLM models and prompts

## Technical Details

### Reaction Feature Extraction

The quality of LLM suggestions depends heavily on effective feature extraction. Key features include:

- **Metabolite Patterns**: Identifying characteristic metabolites (ATP/ADP, NAD/NADH, etc.)
- **Compartment Analysis**: Detecting cross-compartment transport
- **EC Number Integration**: Using existing EC annotations to inform suggestions
- **Reaction Properties**: Analyzing reversibility, stoichiometry, and other properties
- **Naming Analysis**: Extracting insights from reaction names (e.g., "kinase" indicating phosphorylation)

### Prompt Engineering

Effective prompts must:

1. Provide sufficient context about SBO terms and their meanings
2. Present reaction details in a structured format
3. Guide the LLM toward precise ontological classification
4. Specify response format for easier parsing
5. Include few-shot examples of correct classifications

Example prompt structure:
```
You are a Systems Biology expert tasked with assigning SBO terms to biochemical reactions.

Reaction details:
- ID: {reaction_id}
- Name: {reaction_name}
- Reactants: {reactants}
- Products: {products}
- [Additional extracted features]

Relevant SBO terms include:
- SBO:0000176 (Biochemical reaction): General biochemical transformation
- SBO:0000200 (Redox reaction): Involves electron transfer (e.g., NAD/NADH)
- [Additional relevant terms]

Based on these details, what is the most appropriate SBO term for this reaction?
Provide your answer in JSON format with fields: sbo_term, confidence, explanation.
```

### Provider Implementation

For each LLM provider, we need to:

1. Implement authentication and API handling
2. Optimize request parameters (temperature, max tokens, etc.)
3. Manage rate limiting and error handling
4. Process provider-specific response formats

## Future Enhancements

1. **Fine-tuning**: Create specialized models fine-tuned on SBO classification
2. **Batch Processing**: Optimize for efficient batch annotation
3. **Confidence Thresholds**: Implement adaptive confidence thresholds
4. **User Feedback Loop**: Incorporate user corrections to improve suggestions
5. **Term Expansion**: Expand beyond reactions to other model components

## Evaluation

The LLM-based annotation will be evaluated on:

1. **Accuracy**: Agreement with expert-annotated models
2. **Coverage**: Percentage of reactions receiving specific (non-generic) SBO terms
3. **Consistency**: Consistency of annotations across similar reactions
4. **Performance**: Annotation speed and resource usage
5. **Explainability**: Quality of explanations for suggested terms

## Conclusion

This LLM-based annotation assistant represents a significant enhancement to SBOannotator, enabling more accurate and comprehensive annotation of SBML models. The modular design ensures adaptability to different LLM providers and future ontological developments.

The current PR establishes the foundation for this work, demonstrating an understanding of both the SBOannotator codebase and the requirements for effective LLM integration.