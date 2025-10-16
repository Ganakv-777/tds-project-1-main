import os

def signature():
    """Central identity used by /task responses."""
    return {
        "email": os.getenv("USER_EMAIL", "21f3000911@ds.study.iitm.ac.in"),
        "name": os.getenv("USER_NAME", "GANA K V"),
    }
