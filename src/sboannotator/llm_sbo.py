import json
import sys


def askuseLLMornot():
    """
    Ask user if they want to use LLM for SBO annotation of EC reactions.
    
    Input:
        None (interactive function)
    
    Output:
        bool: True if user wants to use LLM, False otherwise
    
    Purpose:
        Interactive prompt for user decision on LLM usage for SBO annotation.
    """
    # Clear any remaining progress bar artifacts before asking user
    print("\033[2K\r", end="")  # Clear entire line and return to beginning
    print("\n" + "=" * 50, flush=True)
    sys.stdout.flush()
    sys.stderr.flush()
    choice = input("Use LLM for SBO annotation of EC reactions? (y/n): ").strip().lower()
    return choice in ['y', 'yes']

def read_document(parent_sbo_file_output_file):
    """
    Read JSON file and return dictionary containing reaction_id, original_sbo, ec_numbers.
    
    Input:
        parent_sbo_file_output_file (str): Path to the JSON file containing SBO annotation data
    
    Output:
        dict: Dictionary mapping reaction_id to reaction data containing original_sbo and ec_numbers
    
    Purpose:
        Loads reaction annotation data from JSON file for LLM processing.
    """

    with open(parent_sbo_file_output_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    data_dict = {}
    reactions = json_data.get('reactions', {})

    for reaction_id, reaction_data in reactions.items():
        original_sbo = reaction_data.get('sbo', None)
        ec_numbers = reaction_data.get('ec_numbers', [])

        data_dict[reaction_id] = {
            'reaction_id': reaction_id,
            'original_sbo': original_sbo,
            'ec_numbers': ec_numbers  # Keep complete EC number list
        }

    # print(f"Read {len(data_dict)} reactions")

    return data_dict


def analyze_reactions_for_llm(data_dict):
    """
    Analyze reaction data, filter reactions with EC numbers and same first digit.
    
    Input:
        data_dict (dict): Dictionary containing reaction data with EC numbers
    
    Output:
        dict: Filtered dictionary containing reactions suitable for LLM processing
    
    Purpose:
        Filters reactions to include only those with EC numbers that have consistent
        first digits, preparing data for LLM-based SBO recommendation.
    """

    filtered_dict = {}

    for reaction_id, reaction_data in data_dict.items():
        ec_numbers = reaction_data.get('ec_numbers', [])


        if len(ec_numbers) == 0:
            continue


        elif len(ec_numbers) == 1:
            new_reaction = reaction_data.copy()
            new_reaction['ec_to_llm'] = ec_numbers[0]
            filtered_dict[reaction_id] = new_reaction


        else:

            first_digits = [ec.split('.')[0] for ec in ec_numbers]

            if len(set(first_digits)) == 1:
                new_reaction = reaction_data.copy()
                new_reaction['ec_to_llm'] =  prefix_of_ec_numbers(ec_numbers)
                filtered_dict[reaction_id] = new_reaction
            else:
                continue

    return filtered_dict


import json


def delete_not_available_ec_to_llm_reaction(filtered_dict, ec_file_path):
    """
    Delete reactions with EC numbers that don't exist in the reference file.
    
    Input:
        filtered_dict (dict): Dictionary of filtered reactions
        ec_file_path (str): Path to EC reference file
    
    Output:
        dict: Dictionary containing only reactions with valid EC numbers
    
    Purpose:
        Removes reactions whose EC numbers are not found in the EC reference database,
        ensuring all processed reactions have valid EC information.
    """

    # Load EC file
    with open(ec_file_path, 'r', encoding='utf-8') as f:
        ec_data = json.load(f)

    # Create a new dict to store valid reactions
    valid_reactions = {}

    for reaction_id, reaction_data in filtered_dict.items():
        ec_to_llm = reaction_data.get('ec_to_llm')

        if ec_to_llm is not None:
            # Check if ec_to_llm exists in EC file
            found = any(ec_item.get('ec_number') == ec_to_llm for ec_item in ec_data)

            if found:
                valid_reactions[reaction_id] = reaction_data
            else:
                print(f"Removing reaction {reaction_id}: EC {ec_to_llm} not in EC file")
        else:
            print(f"Removing reaction {reaction_id}: no ec_to_llm")

    print(f"Before filtering: {len(filtered_dict)} reactions")
    print(f"After filtering: {len(valid_reactions)} reactions")

    return valid_reactions



def prefix_of_ec_numbers(ec_numbers):
    """
    Find the common prefix of EC number list.
    
    Input:
        ec_numbers (list): List of EC numbers to find common prefix
    
    Output:
        str: Common prefix of EC numbers, or None if no common prefix
    
    Purpose:
        Determines the most specific common prefix among a list of EC numbers,
        useful for grouping related enzymatic reactions.
    """

    if not ec_numbers:
        print("Error: EC number list is empty")
        return None

    if len(ec_numbers) == 1:
        return ec_numbers[0]

    # Split all EC numbers into components
    ec_parts = []
    for ec in ec_numbers:
        try:
            parts = ec.split('.')
            ec_parts.append(parts)
        except:
            print(f"Error: Invalid EC number format - {ec}")
            return None

    # Find the shortest EC number length
    min_length = min(len(parts) for parts in ec_parts)

    # Check from 4 levels down to 1, step by step
    for level in range(min(4, min_length), 0, -1):
        # Check if all EC numbers have the same prefix at current level
        first_prefix = '.'.join(ec_parts[0][:level])

        all_same = True
        for parts in ec_parts:
            current_prefix = '.'.join(parts[:level])
            if current_prefix != first_prefix:
                all_same = False
                break

        if all_same:
            return first_prefix

    # If no common prefix found
    print(f"Error: EC number list has no common prefix - {ec_numbers}")
    return None


import json


def add_original_sbo_details(data_dict, sbo_details_file='parentpath_childrentree_sbo_terms_202509031640.json'):
    """
    Add detailed information about original SBO terms to data dictionary.
    
    Input:
        data_dict (dict): Dictionary containing reaction data
        sbo_details_file (str): Path to SBO details JSON file
    
    Output:
        dict: Enhanced dictionary with SBO term details added
    
    Purpose:
        Enriches reaction data with detailed SBO term information including
        term names, comments, and leaf node status.
    """
    
    # Load SBO term detailed information
    with open(sbo_details_file, 'r', encoding='utf-8') as f:
        sbo_data = json.load(f)
    
    # Create SBO ID to detailed information mapping
    sbo_lookup = {}
    for sbo_entry in sbo_data:
        sbo_id = sbo_entry.get('sbo_id')
        if sbo_id:
            sbo_lookup[sbo_id] = {
                'term': sbo_entry.get('sbo_name', ''),
                'comment': sbo_entry.get('sbo_comment', ''),
                'is_leaf': sbo_entry.get('sbo_is_leaf', 'No') == 'Yes'
            }
    
    # Add detailed information about original SBO terms for each reaction
    enhanced_dict = {}
    for reaction_id, reaction_data in data_dict.items():
        enhanced_reaction = reaction_data.copy()
        
        original_sbo = reaction_data.get('original_sbo', '')
        if original_sbo and original_sbo in sbo_lookup:
            sbo_info = sbo_lookup[original_sbo]
            enhanced_reaction['original_sbo_term'] = sbo_info['term']
            enhanced_reaction['original_sbo_comment'] = sbo_info['comment']
            enhanced_reaction['original_sbo_is_leaf'] = sbo_info['is_leaf']
            
        enhanced_dict[reaction_id] = enhanced_reaction
    
    return enhanced_dict

def concatenate_ec_text(data_dict, ec_file_path):
    """
    Add EC text descriptions to reaction data.
    
    Input:
        data_dict (dict): Dictionary containing reaction data
        ec_file_path (str): Path to EC text descriptions file
    
    Output:
        dict: Enhanced dictionary with EC text descriptions added
    
    Purpose:
        Enriches reaction data with human-readable EC number descriptions
        for better LLM understanding and processing.
    """

    # Load EC text mappings
    with open(ec_file_path, 'r', encoding='utf-8') as f:
        ec_data = json.load(f)

    # Loop through reactions
    for reaction_id, reaction_data in data_dict.items():
        ec_to_llm = reaction_data.get('ec_to_llm')

        if ec_to_llm:
            # Find matching EC text in json
            ec_text = None
            for ec_item in ec_data:
                if ec_item.get('ec_number') == ec_to_llm:
                    ec_text = ec_item.get('ec_text')
                    break

            reaction_data['ec_text_to_llm'] = ec_text if ec_text else "No description found"
        else:
            reaction_data['ec_text_to_llm'] = None

    return data_dict


def recommend_sbo_with_model(data_with_ec_text):
    """
    Use ml_sbo deep learning model to recommend SBO terms for reactions.
    
    Input:
        data_with_ec_text (dict): Dictionary containing reaction information and EC text
    
    Output:
        dict: Enhanced dictionary containing recommended SBO information
    
    Purpose:
        Applies machine learning model to generate SBO term recommendations
        based on reaction EC numbers and descriptions.
    """
    # Import ml_sbo model
    from ml_sbo.src.infer import SBOInferencer
    from tqdm import tqdm
    
    # Initialize model (using absolute path)
    import os
    current_dir = os.path.dirname(os.path.dirname(__file__))  # Get src directory
    model_path = os.path.join(current_dir, "ml_sbo", "models", "stage1_80_stage2_10")
    
    # print('\nUsing ML model for SBO term recommendations...\n')
    inferencer = SBOInferencer(model_path)
    
    enhanced_data = {}
    
    # Add progress bar
    for reaction_id, reaction_data in tqdm(data_with_ec_text.items(), desc="Processing reactions"):
        # Build input format expected by ml_sbo
        input_data = {
            'reaction_id': {
                'reaction_id': reaction_id,
                'original_sbo': reaction_data.get('original_sbo', ''),
                'original_sbo_term': reaction_data.get('original_sbo_term', ''),
                'original_sbo_comment': reaction_data.get('original_sbo_comment', ''),
                'original_sbo_is_leaf': reaction_data.get('original_sbo_is_leaf', False),
                'ec_numbers': reaction_data.get('ec_numbers', []),
                'ec_to_llm': reaction_data.get('ec_to_llm', ''),
                'ec_text_to_llm': reaction_data.get('ec_text_to_llm', '')
            }
        }
        
        # Call ml_sbo model prediction
        result = inferencer.predict(input_data)
        
        # Directly use ml_sbo output structure (already contains all necessary fields)
        enhanced_data[reaction_id] = result['reaction_id']
    
    return enhanced_data


def delete_non_leave_sbo_from_recommend_data(recommended_data):
    """
    Delete non-leaf node SBO recommendations from recommendation data.
    
    Input:
        recommended_data (dict): Dictionary containing recommended SBO information
    
    Output:
        dict: Filtered dictionary containing only leaf node SBO recommendations
    
    Purpose:
        Filters recommendations to keep only specific (leaf) SBO terms,
        removing generic parent terms for more precise annotations.
    """
    leaf_recommended_data = {}
    
    for reaction_id, data in recommended_data.items():
        if data.get('recommend_sbo_is_leaf', False):
            # Complete data copy, ensure all fields including ec_text_to_llm are preserved
            leaf_recommended_data[reaction_id] = data.copy()
        else:
            # print(f"Filtered out non-leaf node SBO recommendation: {reaction_id} -> {data.get('recommended_sbo_id')} ({data.get('recommend_sbo_term')})")
            pass
    
    # print(f"Before filtering: {len(recommended_data)} recommendations")
    # print(f"After filtering: {len(leaf_recommended_data)} leaf node recommendations")
    
    return leaf_recommended_data


def let_user_choose_sbo_recommendations(recommended_data,choice):
    """
    Let user choose which reactions need to adopt recommended SBO.
    
    Input:
        recommended_data (dict): Dictionary containing recommended SBO information
        choice: User choice data structure
    
    Output:
        dict: Dictionary of recommendation data selected by user
    
    Purpose:
        Provides interface for user to review and select which SBO recommendations
        should be applied to the model.
    """
    # print("\n" + "=" * 80)
    # print("SBO Recommendation Selection")
    # print("=" * 80)
    
    if not recommended_data:
        # print("No available recommendation data")
          return {}
    
    selected_recommendations = {}
    
    # First ask whether to adopt all recommendations
    print(f"\nFound {len(recommended_data)} SBO recommendations")
    # choice = input("Adopt all recommendations? (y/n/review): ").strip().lower()
    #
    if choice in ['y', 'yes', 'yes']:
        print("✅ Adopt all recommendations")
        # Deep copy to ensure all fields are preserved
        return {k: v.copy() for k, v in recommended_data.items()}
    
    elif choice in ['n', 'no', 'no']:
        print("❌ Do not adopt any recommendations")
        return {}
    
    else:  # review or other input
        print("\nReview recommendations individually:")
        print("-" * 60)
        
        for i, (reaction_id, data) in enumerate(recommended_data.items(), 1):
            print(f"\n[{i}/{len(recommended_data)}] Reaction: {reaction_id}")
            
            # Display original SBO information
            original_sbo = data.get('original_sbo', 'None')
            original_sbo_term = data.get('original_sbo_term', '')
            print(f"Original SBO: {original_sbo} - {original_sbo_term}")
            
            print(f"EC numbers: {data.get('ec_numbers', [])}")
            print(f"EC text: {data.get('ec_text_to_llm', '')}")
            print(f"Recommended SBO: {data.get('recommended_sbo_id')} - {data.get('recommend_sbo_term')}")
            print(f"Recommendation reason: {data.get('recommend_sbo_reason', '')}")
            
            while True:
                user_choice = input("Adopt this recommendation? (y/n/q=quit): ").strip().lower()
                
                if user_choice in ['y', 'yes', 'yes']:
                    selected_recommendations[reaction_id] = data.copy()
                    print("✅ Adopted")
                    break
                elif user_choice in ['n', 'no', 'no']:
                    print("❌ Not adopted")
                    break
                elif user_choice in ['q', 'quit', 'quit']:
                    print("Exit selection early")
                    break
                else:
                    print("Please enter y(adopt), n(not adopt), or q(quit)")
            
            if user_choice in ['q', 'quit', 'quit']:
                break
            
            print("-" * 60)
    
    print(f"\nSummary: Adopted {len(selected_recommendations)}/{len(recommended_data)} recommendations")
    
    if selected_recommendations:
        print("\nAdopted recommendations:")
        for reaction_id, data in selected_recommendations.items():
            print(f"- {reaction_id}: {data.get('original_sbo')} -> {data.get('recommended_sbo_id')}")
    
    return selected_recommendations


def apply_sbo_recommendations_to_model(model_file_path, selected_recommendations,_signal,insert_table):
    """
    Update SBO terms in model file based on user-selected recommendations, save to LLM_Annotated_Models folder.
    Input: 
    - model_file_path: Original model file path
    - selected_recommendations: User-selected recommendation dictionary
    Output: File path of updated model
    """
    import libsbml
    import os
    
    # Read model
    doc = libsbml.readSBML(model_file_path)
    model = doc.getModel()
    
    if model is None:
        print(f"Error: Unable to read model file {model_file_path}")
        _signal.emit(f"Error: Unable to read model file {model_file_path}")
        return None
    
    print(f"\nApplying SBO recommendations to model...")
    _signal.emit(f"\nApplying SBO recommendations to model...")
    print("=" * 60)
    _signal.emit("===================================================================")
    updated_count = 0
    not_found_count = 0

    # Iterate through user-selected recommendations
    for reaction_id, rec_data in selected_recommendations.items():
        # Use libsbml getReaction method to find reaction by ID
        reaction = model.getReaction(reaction_id)
        
        if reaction is not None:
            original_sbo = rec_data.get('original_sbo', '')
            recommended_sbo_id = rec_data.get('recommended_sbo_id', '')
            
            # Extract SBO number part (libsbml setSBOTerm requires integer)
            if recommended_sbo_id.startswith('SBO:'):
                sbo_term_number = int(recommended_sbo_id.split(':')[1])
                
                # Use libsbml setSBOTerm method to set new SBO term
                reaction.setSBOTerm(sbo_term_number)
                insert_table.emit((reaction_id,original_sbo,recommended_sbo_id))
                print(f"✅ {reaction_id}: {original_sbo} -> {recommended_sbo_id}")
                _signal.emit(f"✅ {reaction_id}: {original_sbo} -> {recommended_sbo_id}")
                updated_count += 1
            else:
                print(f"⚠️  {reaction_id}: Invalid SBO ID format {recommended_sbo_id}")
                _signal.emit(f"⚠️  {reaction_id}: Invalid SBO ID format {recommended_sbo_id}")
        else:
            print(f"❌ {reaction_id}: Reaction not found in model")
            _signal.emit(f"❌ {reaction_id}: Reaction not found in model")
            not_found_count += 1
    
    # print("=" * 60)
    # print(f"Update statistics:")
    # print(f"- Successfully updated: {updated_count} reactions")
    # print(f"- Reactions not found: {not_found_count} reactions")
    # print(f"- Total selected: {len(selected_recommendations)} recommendations")
    
    # Create output file path (save to LLM_Annotated_Models folder)
    model_name = model.getId()
    llm_annotated_dir = "../../models/LLM_Annotated_Models"
    
    # Ensure directory exists
    os.makedirs(llm_annotated_dir, exist_ok=True)
    
    output_file_path = f"{llm_annotated_dir}/{model_name}_SBOannotated_LLM.xml"
    
    # Use libsbml writeSBMLToFile method to save updated model
    success = libsbml.writeSBMLToFile(doc, output_file_path)
    
    if success:
        print(f"\n✅ LLM-annotated model saved to: {output_file_path}")
        _signal.emit(f"\n✅ LLM-annotated model saved to: {output_file_path}")
        return output_file_path
    else:
        print(f"\n❌ Error occurred while saving model")
        _signal.emit(f"\n❌ Error occurred while saving model")
        return None

