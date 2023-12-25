import os
import shutil
import datetime
import plistlib
import xml.etree.ElementTree as ET
import json
import re

#Where to backup on the Mac - desktop by default
backup_dir = '~/Desktop/Ubackup/'

#Ulysses backup files
Ulysses_backup_dir = '~/Library/Group Containers/X5AZV975AG.com.soulmen.shared/Ulysses/Backups/'

#Ulysses files non icloud
Ulysses_dir = '~/Library/Mobile Documents/X5AZV975AG~com~soulmen~ulysses3/Documents'

backup_dir = os.path.expanduser(backup_dir)

current_date = datetime.datetime.now()
formatted_date = current_date.strftime("%Y%m%d-%H%M")
markdown_dir = os.path.join(backup_dir, f"markdown-{formatted_date}/")
Ulysses_backup_dir = os.path.expanduser(Ulysses_backup_dir)
Ulysses_dir = os.path.expanduser(Ulysses_dir)


def secure_backup():

    current_date = datetime.date.today()
    formatted_date = current_date.strftime("%Y%m%d")
    last_backup = os.path.join(Ulysses_backup_dir, "Latest Backup.ulbackup")
    
    if os.path.exists(last_backup):
        last_backup_target = os.path.join(backup_dir, f"ulysses-{formatted_date}.ulbackup")
        shutil.copytree(last_backup, last_backup_target, dirs_exist_ok=True)
    else:
        print("No Ulysses backup found!")

def process_element(element):
    text = ''

    # Traitement du texte directement dans l'élément
    if element.text:
        text += element.text

    # Traitement récursif des sous-éléments
    for child in element:

        if child.tag == 'tags' or child.tag == 'tag':
            text += process_element(child)+" "

        # Pour les balises <element>
        elif child.tag == 'element':
            start_tag = child.get('startTag') or ''
            end_tag = child.get('endTag') or ''
            element_text = child.text or ''

            # Ajouter le formatage Markdown et le texte de l'élément
            text += start_tag + element_text + end_tag

        # Ajouter le texte après le sous-élément (tail)
        if child.tail:
            text += child.tail

    return text.strip()

def convert_ulysses_to_markdown(xml_content):

    root = ET.fromstring(xml_content)

    markdown = ""
    for p in root.iter('p'):
        markdown += process_element(p) + '\n\n'

    markdown = re.sub(r'\n{3,}', '\n\n', markdown)
    return markdown.strip()

def build_path(filename,ext=".md"):
    global saved_path    
    md_file= os.path.join(markdown_dir,saved_path,filename+ext)
    destination_dir = os.path.dirname(md_file)
    os.makedirs(destination_dir, exist_ok=True)
    return md_file

def update_saved_path(id,flag):
    global saved_path

    if flag:
        # Remplacer le dernier segment du chemin par l'identifiant
        path_parts = saved_path.split(os.sep)[:-1]  # Enlever le dernier segment
        path_parts.append(id)
        saved_path = os.sep.join(path_parts)
    else:
        saved_path = os.path.join(saved_path, id)

def analyser_ulgroup(file):
    # Vérifier si le résultat est déjà dans le cache
    if file in cache_noms_dossiers:
        return cache_noms_dossiers[file]

    contenu = plist_loader(file)
    if contenu:
        nom_dossier = contenu.get('displayName', 'Nom Inconnu')
        child_order = contenu.get('childOrder', [])
        cache_noms_dossiers[file] = (nom_dossier, child_order)
        return (nom_dossier, child_order)
    else:
        return ('Unknown Name', [])

def real_dir_names(file):
    # Diviser le chemin et extraire les noms
    segments = file.split('/')
    noms_dossiers = []
    ordre_dossier = {}

    for segment in segments:
        if segment.endswith('-ulgroup'):
            fichier_ulgroup = os.path.join('/'.join(segments[:segments.index(segment) + 1]), 'Info.ulgroup')
            nom_dossier, child_order = analyser_ulgroup(fichier_ulgroup)

            # Calculer la longueur nécessaire pour le formatage
            max_length = len(str(len(child_order)))

            ordre_dossier.update({d: str(index + 1).zfill(max_length) for index, d in enumerate(child_order)})
            prefixe_ordre = ordre_dossier.get(segment, "0" * max_length)
            noms_dossiers.append(f"{prefixe_ordre}-{nom_dossier}")


    return "/".join(noms_dossiers)

def plist_loader(path):
    try:
        with open(path, 'rb') as f:
            contenu = plistlib.load(f)
            return contenu

    except Exception as e:
        print(f"Error reading file {path}: {e}")
        return False

def metadata_id(path):
    path = path.replace("/Metadata.plist", "")
    return os.path.basename(path).split('.')[0]

def find_oder(id):
    global ulgroup_data
    #print(ulgroup_data)
    if "sheetClusters" in ulgroup_data:
        total_length = len(ulgroup_data["sheetClusters"])
        max_digits = len(str(total_length))

        id += ".ulysses"

        for i, cluster in enumerate(ulgroup_data["sheetClusters"]):
            if id in cluster:
                return str(i + 1).zfill(max_digits)
    return "0"

def sort_files(filename):
    if filename.endswith('.ulgroup'):
        return (0, filename)
    elif filename.endswith('.ulysses'):
        return (1, filename)
    elif filename.endswith('.plist'):
        return (2, filename)
    else:
        return (3, filename)
    
def markdown_to_filename(markdown_text):

    # Supprimer les lignes de tirets
    markdown_text = re.sub(r'^-+\n?', '', markdown_text, flags=re.MULTILINE)

    # Extraire le premier paragraphe non vide
    paragraphs = markdown_text.strip().split('\n\n')
    first_paragraph = next((p for p in paragraphs if p.strip()), "")

    # Supprimer les balises Markdown
    text_only = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', first_paragraph)  # Supprimer les liens
    text_only = re.sub(r'[_*#>`]', '', text_only)  # Supprimer les autres balises Markdown

    # Prendre les 128 premiers caractères
    filename = text_only[:128]

    # Nettoyer pour obtenir un nom de fichier valide
    filename = re.sub(r'[\\/*?:"<>|]', '', filename)  # Supprimer les caractères non valides
    filename = filename.strip().replace(' ', '_')  # Remplacer les espaces par des underscores

    return filename
    
os.system('clear')

#secure_backup()

cache_noms_dossiers = {}
data_file_extensions = {'.png', '.jpg', '.jpeg', '.tiff', '.pdf'}
total_txt = 0
total_xml = 0
total_empty = 0
saved_path = ""
plist_flag = False
ulgroup_data = {}

for dirpath, dirnames, filenames in os.walk(Ulysses_dir):

    # Trier les fichiers pour que .ulgroup soient traités en premier, puis .plist
    filenames.sort(key=sort_files)

    for filename in filenames:

        # Construire le chemin complet du fichier
        filepath = os.path.join(dirpath, filename)

        #print(filename)

        if filename.startswith('.'):
            continue

        elif filename.endswith('.txt'):
            #Pure mardown file (but not often there, therefore not usable)
            total_txt += 1

        elif filename.endswith('.xml'):
            #XML Ulysses Markdown
            total_xml += 1

            with open(filepath) as f:
                xml = f.read()
            
            markdown = convert_ulysses_to_markdown(xml)
            if len(markdown)>0:

                md_filename = markdown_to_filename(markdown)
                md_file = build_path(f"{order}-{md_filename}")
                
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(markdown)
                
            else:
                #Empty sheet
                total_empty += 1

        elif filename.endswith('.ulgroup'):
            #Plist file describing folders and sub-folders
            #exit("ulgroup")
            saved_path = real_dir_names(filepath)
            order = "0"
            plist_flag = False
            ulgroup_data = plist_loader(filepath)
            #Plist backup
            ulgroup_str = json.dumps(ulgroup_data)
            ulgroup_file = build_path("Info",".txt")
            with open(ulgroup_file, 'w', encoding='utf-8') as f:
                f.write(ulgroup_str)

        elif filename.endswith('.plist'):
            #Metada of text/media contener
            #print(filepath)
            id = metadata_id(filepath)
            order = find_oder(id)
            plist_flag = True
            plist_data = plist_loader(filepath)
            if plist_data:
                plist_str = json.dumps(plist_data)
                plist_file = build_path(f"plist/{order}",".txt")
                with open(plist_file, 'w', encoding='utf-8') as f:
                    f.write(plist_str)

        elif os.path.splitext(filename)[1].lower() in data_file_extensions:
            #Images, PDF and other files attached to projects
            media_file = build_path(f"media-{order}/",filename)
            shutil.copy2(filepath, media_file)
   
        else:
            #Trash
            #print("Trash",filename)
            continue

print("txt:",total_txt)
print("xml:",total_xml)
print("empty xml:",total_empty)