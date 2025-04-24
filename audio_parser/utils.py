from datetime import datetime

def get_file_name():
    now = datetime.now()
    formatted = now.strftime("%d_%m_%Y_%H_%M_%S")
    return formatted