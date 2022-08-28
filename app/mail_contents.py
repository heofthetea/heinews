# All these functions contain a template text that gets sent per mail. Exists as a function instead of just a string because to every
# message, a custom link will have to be put into it.
def verification(link: str):
    return {
        "head": "Verifikation für deinen HEINEWS-Account",
        "body": f"{link}"
    }


def reset(link: str):
    return {
        "head": "Passwort deines HEINEWS-Accounts zurücksetzen",
        "body": f"{link}"
    }


def delete(link: str):
    return {
        "head": "Deinen HEINEWS-Accounts löschen",
        "body": f"{link}"
    }


def account_yeeted():
    return {
        "head": "Dein HEINEWS-Account wurde von unseren Moderatoren gelöscht.",
        "body": """Aus Gründen, die vermutlich ein Fehlverhalten o.ä. darstellen, hat sich unser Moderationsteam dafür entschieden, deinen 
        Account zu löschen. Du kannst dir nach einer gewissen Zeit einen neuen Account erstellen."""
    }

# @param announcement: Announcement object
def announcement(announcement: object):
    return {
        "head": f"Neuigkeiten der Schülerzeitung: {announcement.title}",
        "body": announcement.content
    }
