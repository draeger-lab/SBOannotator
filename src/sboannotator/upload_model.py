import os
import shutil
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning,
                        message=".*found in sys.modules.*")


def get_model_path():
    """
    Get and validate user input model file path.
    
    Input:
        None (interactive function)
    
    Output:
        str: Validated absolute path to the model file
    
    Purpose:
        Prompts user for model file path, validates existence and file type,
        handles quotes and provides error feedback for invalid paths.
    """
    while True:
        model_path = input("Please enter the model file path: ").strip()

        if not model_path:
            print("Path cannot be empty. Please try again.")
            continue

        # Handle quotes
        model_path = model_path.strip('"').strip("'")



        if not os.path.exists(model_path):
            print(f"Error: File '{model_path}' does not exist. Please check the path.")
            continue

        if not os.path.isfile(model_path):
            print(f"Error: '{model_path}' is not a file. Please enter a valid file path.")
            continue

        # print(f"✓ Valid file found: {model_path}")
        return model_path


def copy_model_to_customer_dir(source_path):
    """
    Copy model file to Customer_Models directory.
    
    Input:
        source_path (str): Absolute path to the source model file
    
    Output:
        str: Absolute path to the copied model file in Customer_Models directory
    
    Purpose:
        Copies model file from source location to Customer_Models directory,
        handles filename conflicts by appending numbers, creates directory if needed.
        From src/sboannotator/upload_model.py perspective, goes to ../../models/Customer_Models
    """
    # Get current file (upload_model.py) directory, which is src/sboannotator/
    current_dir = os.path.dirname(os.path.abspath(__file__))


    # Up two levels (project root directory)
    # src/sboannotator -> src -> project root directory
    parent_dir = os.path.dirname(os.path.dirname(current_dir))


    # Target directory models/Customer_Models
    target_dir = os.path.join(parent_dir, 'models', 'Customer_Models')


    # Create directory
    os.makedirs(target_dir, exist_ok=True)


    # Get filename
    filename = os.path.basename(source_path)
    target_path = os.path.join(target_dir, filename)

    # Handle filename conflicts
    counter = 1
    original_filename = filename
    while os.path.exists(target_path):
        name, ext = os.path.splitext(original_filename)
        filename = f"{name}_{counter}{ext}"
        target_path = os.path.join(target_dir, filename)
        counter += 1

    try:
        # Copy file


        shutil.copy2(source_path, target_path)

        return target_path

    except Exception as e:
        print(f"Error copying file: {e}")
        raise


# If running this file directly for testing

def convert_to_relative_path(absolute_path):
    """
    Convert absolute path to relative path from src/sboannotator perspective.
    
    Input:
        absolute_path (str): Absolute path to the model file
    
    Output:
        str: Relative path from src/sboannotator directory perspective
    
    Purpose:
        Converts absolute file path to relative path format suitable for
        use within the sboannotator module structure.
    """
    # Extract filename from absolute path
    filename = os.path.basename(absolute_path)

    # Construct relative path
    relative_path = f"../../models/Customer_Models/{filename}"

    return relative_path
if __name__ == "__main__":
    print("Testing upload_model functions...")
    try:
        path = get_model_path()
        result = copy_model_to_customer_dir(path)
        print(f"Success! File copied to: {result}")
        print(convert_to_relative_path(result))
    except Exception as e:
        print(f"Error: {e}")
