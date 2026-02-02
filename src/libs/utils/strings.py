import string

translator = str.maketrans("", "", string.punctuation)


def standardize_string(input_string):
    processed_string = input_string.lower().replace(" ", "")
    translated_string = processed_string.translate(translator)

    return translated_string
