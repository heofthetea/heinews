from app import __HOST__
# All these functions contain a template text that gets sent per mail. Exists as a function instead of just a string because to every
# message, a custom link will have to be put into it.


def verification(link: str, user_name: str) -> dict:
    return {
        "head": "Verifikation für Deinen HEINEWS-Account",
        "body": \
f"""
Hey {user_name}! 
Cool, dass Du dich dazu entschieden hast, einen Account auf unserer Website zu erstellen. Mit Deinem Account kannst du zum beispiel an Umfragen teilnehmen oder Aritkel upvoten. Das einzige, dass dazu noch fehlt, ist, \
dass wir Deine Email verifizieren können. Alles, was Du dafür tun musst, ist auf diesen Link zu klicken - Der Rest sollte sich von alleine erledigen. (Und wie immer - Wenn etwas nicht so funktioniert, wie es sollte, \
darfst Du uns sehr gerne kontaktieren, damit sich unsere Entwickler darum kümmern können.)

{link}

Viel Spaß auf unserer Website!!"""
    }


def reset(link: str):
    return {
        "head": "Passwort Deines HEINEWS-Accounts zurücksetzen",
        "body": \
f"""
Du scheinst unzufrieden mit Deinem aktuellen Passwort zu sein - oder hast Du es einfach vergessen? :) Wie auch immer, das sollte sich schnell geregelt haben. Folge einfach dem Link hier und gebe Dein neues Passwort ein. \
(Und wie immer - Wenn etwas nicht so funktioniert, wie es sollte, darfst Du uns sehr gerne kontaktieren, damit sich unsere Entwickler darum kümmern können.)

{link}"""
    }


def delete(link: str):
    return {
        "head": "Deinen HEINEWS-Accounts löschen",
        "body": \
f"""
Schade, dass Du uns verlässt... :( Wenn Du Feedback oder Verbesserungsvorschläge hast - Nehme gerne über unsere offizielle Email (zeitung@hhg-ostfildern.de) Kontakt auf. Um Deinen Account entgültig zu löschen, folge diesem Link:

{link}"""
    }


def account_yeeted():
    return {
        "head": "Dein HEINEWS-Account wurde von unseren Moderatoren gelöscht.",
        "body": """Aus Gründen, die vermutlich ein Fehlverhalten o.ä. darstellen, hat sich unser Moderationsteam dafür entschieden, Deinen 
        Account zu löschen. Du kannst dir nach einer gewissen Zeit einen neuen Account erstellen."""
    }

# @param announcement: Announcement object
def announcement(announcement: object):
    link = f"{__HOST__}/article/announcement/{announcement.id}"
    return {
        "head": f"Neuigkeiten der Schülerzeitung: {announcement.title}",
        "body": f"{announcement.content}\n{link}"
    }

# @param article: Article object
def article(title: str, description: str, id: str) -> dict:
    link = f"{__HOST__}/article/{id}"
    return {
        "head": "Es gibt einen neuen Artikel auf der HEINEWS-WEBSITE!",
        "body": f"{title}\n{description}\n\nLies hier weiter: {link}"
    }
