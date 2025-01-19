# intents.py

import re

# Pemetaan intent ke permission terkait
INTENT_PERMISSION_MAP = {
    'edit_document': ['edit_document'],
    'view_document': ['view_document'],
    'delete_document': ['delete_document'],
}

def detect_intent(user_input):
    user_input = user_input.lower()
    if re.search(r'\bedit\b', user_input) and re.search(r'\bdocument\b', user_input):
        return 'edit_document'
    elif re.search(r'\bview\b', user_input) and re.search(r'\bdocument\b', user_input):
        return 'view_document'
    elif re.search(r'\bdelete\b', user_input) and re.search(r'\bdocument\b', user_input):
        return 'delete_document'
    else:
        return None