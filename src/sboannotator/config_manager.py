"""
Ultra Simple Configuration Manager
Ultra-simplified configuration manager - assumes configuration file always exists
"""
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QApplication
import json
from pathlib import Path

# Current module file directory
PKG_DIR = Path(__file__).parent

def load_config(config_file='database_config.json'):
    """
    Load configuration file.
    
    Input:
        config_file (str): Path to the configuration file (default: 'database_config.json')
    
    Output:
        dict: Configuration data loaded from JSON file
    
    Purpose:
        Loads database configuration from JSON file for SBO annotation processing.
    """
    cfg_path = Path(config_file)
    cfg_path = PKG_DIR / cfg_path   # Change to relative module directory to find
    with cfg_path.open('r', encoding='utf-8') as f:
        return json.load(f)

def get_database_order(config_file='database_config.json'):
    """
    Get database order from configuration.
    
    Input:
        config_file (str): Path to the configuration file (default: 'database_config.json')
    
    Output:
        list: Ordered list of database names for annotation processing
    
    Purpose:
        Retrieves the database priority order for sequential SBO annotation.
    """
    config = load_config(config_file)
    return config['database_order']


import json
from pathlib import Path

# Assume PKG_DIR is defined elsewhere in the project
PKG_DIR = Path(__file__).parent


def save_config(config_data, config_file='database_config.json'):
    """
    Save configuration to file.
    
    Input:
        config_data (dict): Configuration data to save
        config_file (str): Path to the configuration file (default: 'database_config.json')
    
    Output:
        None
    
    Purpose:
        Saves database configuration data to JSON file for persistent storage.
    """
    cfg_path = Path(config_file)
    cfg_path = PKG_DIR / cfg_path
    with cfg_path.open('w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)


def load_config(config_file='database_config.json'):
    """
    Load configuration from file (duplicate function).
    
    Input:
        config_file (str): Path to the configuration file (default: 'database_config.json')
    
    Output:
        dict: Configuration data loaded from JSON file
    
    Purpose:
        Loads database configuration from JSON file (duplicate of function above).
    """
    cfg_path = Path(config_file)
    cfg_path = PKG_DIR / cfg_path
    with cfg_path.open('r', encoding='utf-8') as f:
        return json.load(f)


def user_change_database_configuration(communicator,config_file='database_config.json'):
    """
    Interactive function for users to modify database configuration order.
    
    Input:
        communicator: PyQt communicator object for GUI interaction
        config_file (str): Path to the configuration file (default: 'database_config.json')
    
    Output:
        None (modifies configuration file)
    
    Purpose:
        Provides interactive interface for users to modify database processing order,
        with preset options and custom configuration capabilities.
    """
    input_response = [None]  # Use list to implement mutable object reference

    # Define callback function to handle input results
    def handle_input_result(result):
        input_response[0] = result

    # Connect signal
    communicator.input_result.connect(handle_input_result)

    # Load current configuration
    config = load_config(config_file)
    current_order = config['database_order']
    usage_examples = config.get('_usage_examples', {})

    print("\n" + "=" * 60)
    communicator.append_text_database.emit("===================================================================")
    print("Database Configuration Manager")
    communicator.append_text_database.emit("Database Configuration Manager")
    print("=" * 60)
    communicator.append_text_database.emit("===================================================================")
    print(f"Current database order: {current_order}")
    communicator.append_text_database.emit(f"Current database order: {current_order}")
    print("=" * 60)
    communicator.append_text_database.emit("===================================================================")


    # Display preset options
    print("\nPreset Configuration Options:")
    communicator.append_text_database.emit("\nPreset Configuration Options:")
    preset_options = {}
    option_num = 1

    for key, value in usage_examples.items():
        if not key.startswith('_'):  # Skip comment fields
            preset_options[option_num] = key
            print(f"  {option_num}. {key}")
            communicator.append_text_database.emit(f"  {option_num}. {key}")
            print(f"     Order: {value['database_order']}")
            communicator.append_text_database.emit(f"     Order: {value['database_order']}")
            print(f"     Description: {value['_description']}")
            communicator.append_text_database.emit(f"     Description: {value['_description']}\n")
            print()
            option_num += 1

    # Add custom option
    custom_option = option_num
    preset_options[custom_option] = 'custom'
    print(f"  {custom_option}. Custom Order")
    communicator.append_text_database.emit(f"  {custom_option}. Custom Order")
    print("     Manually input database order")
    communicator.append_text_database.emit("     Manually input database order\n")
    print()

    # Add exit option
    exit_option = option_num + 1
    print(f"  {exit_option}. Keep current configuration and exit")
    communicator.append_text_database.emit(f"  {exit_option}. Keep current configuration and exit")

    # User selection
    while True:
        try:
            print("\n" + "-" * 60)
            communicator.append_text_database.emit("-------------------------------------------------------------------------")
            # choice = input(f"Please select configuration option (1-{exit_option}): ").strip()

            # Where user input is needed
            communicator.request_input.emit("Selection", f"Please select configuration option (1-{exit_option}): ", "text")

            # Wait for user input (loop check until result obtained)
            while input_response[0] is None:
                QThread.msleep(100)  # Brief sleep to reduce CPU usage
                QApplication.processEvents()  # Process event loop

            # Get user input result
            choice = input_response[0]
            input_response[0] = None

            choice_num = int(choice.strip())

            if choice_num == exit_option:
                print("Current configuration maintained, exiting configuration manager.")
                communicator.append_text_database.emit("Current configuration maintained, exiting configuration manager.")
                return

            elif choice_num == custom_option:
                # Custom configuration
                print("\nCustom Database Order")
                communicator.append_text_database.emit("\nCustom Database Order")
                print("Available databases: bigg, kegg, reactome, seed")
                communicator.append_text_database.emit("Available databases: bigg, kegg, reactome, seed")
                print("Please enter database names separated by commas (e.g.: bigg,kegg,seed)")
                communicator.append_text_database.emit("Please enter database names separated by commas (e.g.: bigg,kegg,seed)")

                while True:
                    # custom_input = input("Database order: ").strip()
                    # Where user input is needed
                    communicator.request_input.emit("Selection", "Database order: ",
                                                    "text")

                    # Wait for user input (loop check until result obtained)
                    while input_response[0] is None:
                        QThread.msleep(100)  # Brief sleep to reduce CPU usage
                        QApplication.processEvents()  # Process event loop

                    # Get user input result
                    custom_input = input_response[0]
                    input_response[0] = None
                    custom_input = custom_input.strip()
                    if not custom_input:
                        print("Input cannot be empty, please try again.")
                        communicator.append_text_database.emit("Input cannot be empty, please try again.")
                        continue

                    # Parse user input
                    new_order = [db.strip() for db in custom_input.split(',')]

                    # Validate database names
                    valid_dbs = {'bigg', 'kegg', 'reactome', 'seed'}
                    invalid_dbs = [db for db in new_order if db not in valid_dbs]

                    if invalid_dbs:
                        print(f"Invalid database names: {invalid_dbs}")
                        communicator.append_text_database.emit(f"Invalid database names: {invalid_dbs}")
                        print(f"   Valid options: {list(valid_dbs)}")
                        communicator.append_text_database.emit(f"   Valid options: {list(valid_dbs)}")
                        continue

                    if len(new_order) == 0:
                        print("At least one database must be selected.")
                        communicator.append_text_database.emit("At least one database must be selected.")
                        continue

                    break

            elif 1 <= choice_num < custom_option:
                # Preset configuration
                selected_preset = preset_options[choice_num]
                new_order = usage_examples[selected_preset]['database_order']
                print(f"\nSelected preset configuration: {selected_preset}")
                communicator.append_text_database.emit(f"\nSelected preset configuration: {selected_preset}")
                print(f"New database order: {new_order}")
                communicator.append_text_database.emit(f"New database order: {new_order}")

            else:
                print(f"Invalid option, please enter a number between 1-{exit_option}.")
                communicator.append_text_database.emit(f"Invalid option, please enter a number between 1-{exit_option}.")
                continue

            # Confirm changes
            print(f"\nCurrent order: {current_order}")
            communicator.append_text_database.emit(f"\nCurrent order: {current_order}")
            print(f"New order: {new_order}")
            communicator.append_text_database.emit(f"New order: {new_order}")

            # confirm = input("\nConfirm configuration change? (y/n): ").strip().lower()
            # Where user input is needed
            communicator.request_input.emit("Selection", f"Confirm configuration change? (y/n):", "yesno")

            # Wait for user input (loop check until result obtained)
            while input_response[0] is None:
                QThread.msleep(100)  # Brief sleep to reduce CPU usage
                QApplication.processEvents()  # Process event loop

            # Get user input result
            confirm = input_response[0]
            input_response[0] = None
            confirm = confirm.strip()

            if confirm.lower() in ['y', 'yes']:
                # Save new configuration
                config['database_order'] = new_order
                save_config(config, config_file)
                print(f"\nConfiguration successfully saved!")
                communicator.append_text_database.emit(f"\nConfiguration successfully saved!")
                print(f"New database order: {new_order}")
                communicator.append_text_database.emit(f"New database order: {new_order}")
                return
            else:
                print("Configuration change cancelled.")
                communicator.append_text_database.emit("Configuration change cancelled.")
                # Break the loop to return to main menu or exit
                continue

        except ValueError:
            print(f"Please enter a valid number (1-{exit_option}).")
            communicator.append_text_database.emit(f"Please enter a valid number (1-{exit_option}).")
        except KeyboardInterrupt:
            print("\n\nConfiguration change cancelled.")
            communicator.append_text_database.emit("\n\nConfiguration change cancelled.")
            return
        except Exception as e:
            print(f"An error occurred: {e}")
            communicator.append_text_database.emit(f"An error occurred: {e}")
            return


