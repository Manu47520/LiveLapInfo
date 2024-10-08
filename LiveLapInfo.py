import ac
import acsys
import os

# Variables globales
chrono_label = None
lap_label = None
validity_label = None
track_label = None
layout_label = None
reference_time_input = None
reference_time = 0  # Temps de référence en millisecondes
diff_label = None
best_time_label = None
best_time_file = None
best_time = None  # Meilleur temps en millisecondes
language = "en"  # Langue par défaut

# Textes en français et en anglais
texts = {
    "en": {
        "app_name": "Live Lap Info",
        "track": "Track",
        "layout": "Layout",
        "chrono": "Chrono",
        "lap": "Lap",
        "valid": "Valid lap",
        "invalid": "Invalid lap",
        "ref_time": "Reference time (m:ss:cc)",
        "diff": "Difference",
        "best_time": "Best time",
    },
    "fr": {
        "app_name": "Infos Tour en Direct",
        "track": "Circuit",
        "layout": "Configuration",
        "chrono": "Chrono",
        "lap": "Tour",
        "valid": "Tour valide",
        "invalid": "Tour invalide",
        "ref_time": "Temps de référence (m:ss:cc)",
        "diff": "Différence",
        "best_time": "Meilleur temps",
    }
}

def acMain(ac_version):
    global chrono_label, lap_label, validity_label, track_label, layout_label, reference_time_input, diff_label, best_time_label, best_time_file, language

    # Détecter la langue du jeu
    language = ac.getGameLanguage()
    if language not in texts:
        language = "en"  # Par défaut en anglais si la langue n'est pas supportée

    # Créer une application dans Assetto Corsa
    app_window = ac.newApp(texts[language]["app_name"])
    ac.setSize(app_window, 300, 350)
    
    # Ajouter les labels pour afficher les informations
    track_label = ac.addLabel(app_window, texts[language]["track"] + ": Loading...")
    ac.setPosition(track_label, 10, 10)

    layout_label = ac.addLabel(app_window, texts[language]["layout"] + ": Loading...")
    ac.setPosition(layout_label, 10, 30)

    chrono_label = ac.addLabel(app_window, texts[language]["chrono"] + ": 00:00.000")
    ac.setPosition(chrono_label, 10, 60)

    lap_label = ac.addLabel(app_window, texts[language]["lap"] + ": 1")
    ac.setPosition(lap_label, 10, 90)

    validity_label = ac.addLabel(app_window, texts[language]["valid"])
    ac.setPosition(validity_label, 10, 120)

    # Charger le temps de référence depuis le fichier
    last_ref_time = load_reference_time()

    # Champ pour entrer le temps de référence sous forme m:ss:cc
    reference_time_input = ac.addTextBox(app_window, last_ref_time)  # Valeur par défaut depuis le fichier
    ac.setPosition(reference_time_input, 10, 150)
    ac.setSize(reference_time_input, 100, 20)

    ref_label = ac.addLabel(app_window, texts[language]["ref_time"])
    ac.setPosition(ref_label, 10, 130)

    # Ajouter un label pour la différence avec le temps de référence
    diff_label = ac.addLabel(app_window, texts[language]["diff"] + ": 0.00")
    ac.setPosition(diff_label, 10, 180)

    # Ajouter un label pour le meilleur temps
    best_time_label = ac.addLabel(app_window, texts[language]["best_time"] + ": 00:00.000")
    ac.setPosition(best_time_label, 10, 210)

    # Récupérer et afficher le nom du circuit et le layout au démarrage
    track_name = ac.getTrackName()
    track_layout = ac.getTrackConfiguration()
    ac.setText(track_label, texts[language]["track"] + ": " + track_name)
    ac.setText(layout_label, texts[language]["layout"] + ": " + track_layout)

    # Déterminer le nom de fichier pour enregistrer le meilleur temps
    best_time_file = "apps/python/LiveLapInfo/{}_{}.txt".format(track_name, track_layout)

    # Charger le meilleur temps depuis le fichier correspondant
    load_best_time()

    return texts[language]["app_name"]

def acUpdate(deltaT):
    global chrono_label, lap_label, validity_label, diff_label, reference_time, best_time, best_time_label

    # Récupérer le numéro du tour en cours
    current_lap = ac.getCarState(0, acsys.CS.LapCount)

    # Récupérer le temps de tour en cours
    lap_time = ac.getCarState(0, acsys.CS.LapTime)
    
    # Convertir le temps en format lisible
    minutes = int(lap_time // 60000)
    seconds = (lap_time % 60000) / 1000.0
    time_str = "{:02}:{:06.3f}".format(minutes, seconds)

    # Récupérer la validité du tour
    is_lap_valid = ac.getCarState(0, acsys.CS.LapInvalidated)

    # Mettre à jour les labels avec les informations actuelles
    ac.setText(chrono_label, texts[language]["chrono"] + ": " + time_str)
    ac.setText(lap_label, texts[language]["lap"] + ": {}".format(current_lap))
    
    if is_lap_valid == 0:
        ac.setText(validity_label, texts[language]["valid"])
    else:
        ac.setText(validity_label, texts[language]["invalid"])

    # Récupérer le temps de référence depuis la zone de texte
    ref_time_str = ac.getText(reference_time_input)
    reference_time = convert_time_str_to_ms(ref_time_str)

    # Sauvegarder le temps de référence dans un fichier
    save_reference_time(ref_time_str)

    # Comparer le temps de référence avec le tour en cours
    diff = lap_time - reference_time
    if diff < 0:
        diff_str = "-{:06.2f}".format(abs(diff) / 1000.0)
    else:
        diff_str = "+{:06.2f}".format(diff / 1000.0)

    ac.setText(diff_label, texts[language]["diff"] + ": " + diff_str)

    # Sauvegarder le meilleur temps si le tour est valide et meilleur
    if is_lap_valid == 0 and (best_time is None or lap_time < best_time):
        best_time = lap_time
        save_best_time(lap_time)
        ac.setText(best_time_label, texts[language]["best_time"] + ": " + time_str)

def convert_time_str_to_ms(time_str):
    """Convertir un temps au format m:ss:cc en millisecondes"""
    try:
        minutes, seconds, centi = time_str.split(":")
        minutes = int(minutes)
        seconds = int(seconds)
        centi = int(centi)
        total_time = (minutes * 60000) + (seconds * 1000) + (centi * 10)
        return total_time
    except ValueError:
        return 0  # Valeur par défaut si l'entrée est invalide

def save_reference_time(time_str):
    """Sauvegarde le temps de référence dans un fichier texte"""
    try:
        with open("apps/python/LiveLapInfo/reference_time.txt", 'w') as file:
            file.write(time_str)
    except Exception as e:
        ac.log("Erreur lors de la sauvegarde du temps de référence: " + str(e))

def load_reference_time():
    """Charge le temps de référence depuis un fichier texte"""
    if os.path.exists("apps/python/LiveLapInfo/reference_time.txt"):
        try:
            with open("apps/python/LiveLapInfo/reference_time.txt", 'r') as file:
                return file.readline().strip()
        except Exception as e:
            ac.log("Erreur lors du chargement du temps de référence: " + str(e))
            return "1:30:00"  # Valeur par défaut si erreur
    else:
        return "1:30:00"  # Valeur par défaut si fichier non trouvé

def save_best_time(lap_time):
    """Sauvegarde le meilleur temps dans un fichier spécifique au circuit et layout"""
    try:
        with open(best_time_file, 'w') as file:
            minutes = int(lap_time // 60000)
            seconds = (lap_time % 60000) / 1000.0
            time_str = "{:02}:{:06.3f}".format(minutes, seconds)
            file.write(time_str)
    except Exception as e:
        ac.log("Erreur lors de la sauvegarde du meilleur temps: " + str(e))

def load_best_time():
    """Charge le meilleur temps depuis un fichier spécifique au circuit et layout"""
    global best_time
    if os.path.exists(best_time_file):
        try:
            with open(best_time_file, 'r') as file:
                best_time_str = file.readline().strip()
                ac.setText(best_time_label, texts[language]["best_time"] + ": " + best_time_str)
                best_time = convert_time_str_to_ms(best_time_str)
        except Exception as e:
            ac.log("Erreur lors du chargement du meilleur temps: " + str(e))
            ac.setText(best_time_label, texts[language]["best_time"] + ": N/A")
    else:
        ac.setText(best_time_label, texts[language]["best_time"] + ": N/A")
