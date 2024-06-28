import random

def repeat_and_shuffle(file_path, repeat_count, shuffle=True):
    # Read the content from the input file
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Repeat each line for the specified number of times
    repeated_lines = [line.strip() for line in lines for _ in range(repeat_count)]

    # Shuffle the data order if shuffle is True
    if shuffle:
        random.shuffle(repeated_lines)

    # Save the shuffled data to a new file
    new_file_path = 'commands/commands_infotransfer_arm_' + 'P8' + '.json'
    with open(new_file_path, 'w') as new_file:
        new_file.write('\n'.join(repeated_lines))

    print(f"Shuffled data has been saved to '{new_file_path}'.")

# Example usage
file_path = 'study_data/template_infotransfer_arm.json'  # Path to the input file
repeat_count = 5     # Number of times to repeat each line
shuffle_data = True    # Whether to shuffle the data order

repeat_and_shuffle(file_path, repeat_count, shuffle_data)
