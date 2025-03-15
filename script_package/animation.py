import math
import re
import time

import bpy
import os
import numpy as np
from scipy.io import wavfile

FRAMERATE_VIDEO = 24

def recuperer_son_depuis_plage_frequences(son: np.ndarray, sample_rate: int, freq1: int | None, freq2: int | None) -> np.ndarray:
    """
    Cette fonction permet de récupérer une version réduite du son avec uniquement les fréquences de la plage indiquée
    :param son: Buffer représentant le son.
    :param freq1: Borne inférieur de la plage de fréquences. Une valeur de type None sur cette borne permet de l'ignorer.
    :param freq2: Borne supérieur de la plage de fréquences. Une valeur de type None sur cette borne permet de l'ignorer.
    :return: Le buffer de son recomposé avec les fréquences sonores de la plage [freq1, freq2].
    Si freq1 = None et freq2 = None, alors on renvoie simplement le son de base
    """

    if freq1 is None and freq2 is None:
        return son

    # On applique la FFT (Fast Fourier Transformation), qui va permettre d'extraire les fréquences présentes dans le son
    tableau_fft = np.fft.fft(son)
    # Tableau des fréquences associées aux valeurs de tableau_fft
    frequences = np.fft.fftfreq(len(son), 1 / sample_rate)

    # On applique des modifications au son
    # On ne garde que les fréquences présentes dans l'intervalle [0, freq2]
    if freq1 is None:
        tableau_fft[ (np.abs(frequences) > freq2) ] = 0
    # On ne garde que les fréquences présentes dans l'intervalle [freq1, +infini)
    elif freq2 is None:
        tableau_fft[ (freq1 > np.abs(frequences)) ] = 0
    # On ne garde que les fréquences entre freq1 et freq2
    else:
        tableau_fft[ (np.abs(frequences) < freq1) or (np.abs(frequences) > freq2) ] = 0

    # On va inverser la FFT pour revenir sur un array de son utilisable
    son_recompose = np.fft.ifft(tableau_fft)
    son_recompose = np.round(son_recompose.real).astype(np.int16)  # On convertit le tableau en entiers réels

    return son_recompose

def recuperer_son_wav(path_son: str) -> tuple[np.ndarray, float, int]:
    """
    Permet de récupérer le premier son au format .wav, dans le dossier "musique"
    :param path_son:  doit être le chemin absolu vers l'emplacement le fichier son. Le fichier son doit être au format wav
    :return: un tuple constitué du framerate, de la durée, du son sous forme de tableau numpy
    """

    # On passe le chemin en chemin absolu, car bpy a du mal avec les chemins relatifs
    path_son = os.path.abspath(path_son)

    # On récupère le fichier wav avec scipy sous forme d'un buffer
    sample_rate, buffer = wavfile.read(path_son)

    # si le son a plusieurs tracks, il faut faire son = buffer.T[0]
    son = buffer
    longueur_son = len(son)/sample_rate

    return son, longueur_son, sample_rate

def recupereration_objets_gltf(folder_path: str) -> list[bpy.types.Object]:
    """
    :param folder_path: chemin vers le dossier dans lequel récupérer les objets 3D, au format gltf/glb
    :return: une liste constituée d'objets 3D déjà ajoutés dans la scene
    """

    # On passe le chemin en chemin absolu, car bpy a du mal avec les chemins relatifs
    folder_path = os.path.abspath(folder_path)

    liste_objets = []

    # Récupération des chemins vers les objets
    liste_path_objets = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            liste_path_objets.append(os.path.join(root, file))

    objets_a_ajouter = []
    for path_objet in liste_path_objets:
        # Ajoute l'objet dans la scene
        # On trie les fichiers dans le dossier pour importer seulement les fichiers en .obj
        filename, file_extension = os.path.splitext(path_objet)
        if file_extension == '.obj':
            objets_a_ajouter.append(path_objet)

    print(objets_a_ajouter)
    for path_objet in objets_a_ajouter:
        # Ajoute l'objet dans la scene
        bpy.ops.wm.obj_import(filepath=path_objet)

    # On positionne nos objets sur la scene
    i = 0
    for objet in  bpy.context.view_layer.objects:
        objet.location = (i, i, i)
        objet.rotation_euler = (0, 0, 0)
        liste_objets.append(objet)
    i += 1

    return liste_objets

def ajouter_camera_et_lumiere() -> None:
    """
    Cette fonction permet d'ajouter la caméra et la source de lumière à la scene utilisée par Blender
    """

    # Ajouter une caméra
    bpy.ops.object.camera_add(location=(7, -7, 4))  # Position de la caméra
    camera = bpy.context.object  # Référence à l'objet caméra
    camera.rotation_euler = (1.13446, 0, 0.80)  # Orientation de la caméra

    # Définir cette caméra comme caméra active pour le rendu
    bpy.context.scene.camera = camera

    # Ajout d'une lumière
    light = bpy.data.lights.new(name="lumiere", type="POINT")
    light_object = bpy.data.objects.new(name="object_lumiere", object_data=light)
    light.energy = 500  # Intensité lumineuse
    light.color = (1, 1, 1)  # Couleur RGB de la lumière
    light_object.location = (0, -5, -2)

    # Lier l'objet de la lumière à la scène actuelle
    bpy.context.collection.objects.link(light_object)

def animer_objets_3d(liste_objets: list[bpy.types.Object], buffer_son: np.ndarray ,duree_son: float, framerate_son: int) -> None:
    """
    Permet d'effectuer l'animation
    :param liste_objets: La liste des objets 3D à animer.
    :param buffer_son: Buffer représentant le son sur lequel l'animation se base.
    :param duree_son: Durée du son (en secondes).
    :param framerate_son: Framerate du son en samples/seconde.
    """

    # Récupération du son en fréquences basses pour baser les mouvements de rotation sur l'axe x.
    son_faibles_frequences = recuperer_son_depuis_plage_frequences(buffer_son, framerate_son, None, 1000)

    # Récupération du son en fréquences hautes pour baser les mouvements de rotation sur l'axe z.
    son_hautes_frequences = recuperer_son_depuis_plage_frequences(buffer_son, framerate_son, 4000, None)

    # Définition des paramètres d'animation en fonction de la musique
    nb_keyframes_animation = 50
    frame_end = int(duree_son * FRAMERATE_VIDEO)  # n° de la frame de fin pour l'animation

    # Définition du buffer contenant les valeurs d'intensité des échantillons du son au moment des keyframes (d'amplitude frame_per_sec et centré en 0)
    buffer = np.array([(abs(buffer_son[i]) / 256 * framerate_son) - framerate_son / 2 for i in
                  range(0, len(buffer_son), len(buffer_son) // nb_keyframes_animation)])

    buffer_faibles_frequences = np.array([(abs(son_faibles_frequences[i]) / 256 * framerate_son) - framerate_son / 2 for i in
                                     range(0, len(son_faibles_frequences),
                                           len(son_faibles_frequences) // nb_keyframes_animation)])

    buffer_hautes_frequences = np.array([(abs(son_hautes_frequences[i]) / 256 * framerate_son) - framerate_son / 2 for i in
                                     range(0, len(son_hautes_frequences),
                                           len(son_hautes_frequences) // nb_keyframes_animation)])

    i = 0
    for objet in liste_objets:
        # On précise le mode de rotation de l'objet (car de base, il est en Quaternions)
        objet.rotation_mode = "XYZ"

        for frame in range(nb_keyframes_animation):
            #objet.location = ( i - len(liste_objets) // 2, i - len(liste_objets) // 2,
            #                   (-1) ** i * buffer[frame] / max(abs(buffer)) )

            objet.location = (i - len(liste_objets) // 2 + np.cos(frame),
                              i - len(liste_objets) // 2 + np.sin(frame),
                              (-1) ** i * buffer[frame] / max(abs(buffer)) )

            # On fait bouger les modèles sur un angle entre -90° et +90° autours des axes Y et Z.
            objet.rotation_euler = (0,
                                    math.radians( 90 * buffer_hautes_frequences[frame] / max(abs(buffer_hautes_frequences))),
                                    math.radians( 90 * buffer_faibles_frequences[frame] / max(abs(buffer_faibles_frequences))))

            if frame == 0:
                objet.keyframe_insert("location", frame=1)
                objet.keyframe_insert("rotation_euler", frame=1)
            else:
                objet.keyframe_insert("location", frame=(frame * frame_end / nb_keyframes_animation))
                objet.keyframe_insert("rotation_euler", frame=(frame * frame_end / nb_keyframes_animation))
        i += 1

    # On fait en sorte que l'animation ait le nombre de frames nécessaires pour durer l'entièreté du son
    bpy.context.scene.frame_end = frame_end

def ajouter_audio_animation(frame_per_sec: int, path_son: str) -> None:
    """
    Permet de configurer et ajouter du son à la vidéo produite
    :param frame_per_sec: indique le framerate de l'animation
    :param path_son: indique le chemin absolu vers le son. Le son doit être au format wav.
    """

    # Activer le séquenceur pour inclure le son
    scene = bpy.context.scene
    scene.sequence_editor_create()
    scene.sequence_editor.sequences.new_sound(
        name="Background Sound",
        filepath=path_son,
        channel=1,
        frame_start=1,  # Début du son à la frame 1
    )

    # Activer le son dans le rendu
    scene.render.ffmpeg.audio_codec = 'AAC'  # Codec audio (AAC est largement compatible)
    scene.render.ffmpeg.audio_bitrate = 192  # Définir le bitrate audio (en kbps)
    scene.render.ffmpeg.audio_mixrate = frame_per_sec
    scene.render.ffmpeg.audio_channels = 'MONO'

def render_animation(nom_fichier: str = "animation") -> None:
    """
    Permet de render l'animation.
    Cette fonction va créer un fichier mp4 correspondant à l'animation voulue dans le dossier "animation"
    :param nom_fichier: Nom du fichier mp4 produit oar la fonction.
    """

    # Configurer le rendu
    bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
    # On doit récupérer le current working directory, sinon l'animation va se créer à la racine de C:\
    bpy.context.scene.render.filepath = "".join(
        re.split("(\\\)", (os.getcwd()))[:-1]) + f"animations/{nom_fichier}.mp4"
    bpy.context.scene.render.ffmpeg.format = 'MPEG4'
    bpy.context.scene.render.ffmpeg.codec = 'H264'

    # Rendre l'animation
    bpy.ops.render.render(animation=True)

def main():

    #####################################
    # PARTIE RECUPERATION DE LA MUSIQUE #
    #####################################

    path_son = "../musique/StarWarsMini.wav"

    buffer_son, duree_son, framerate_son = recuperer_son_wav(path_son)

    ####################
    # PARTIE ANIMATION #
    ####################

    # Supprimer tous les objets de la scène
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    liste_objets = recupereration_objets_gltf("../objets3D")

    # Animer l'objet
    animer_objets_3d(liste_objets, buffer_son, duree_son, framerate_son)

    # Ajouter de la caméra et de la lumière
    ajouter_camera_et_lumiere()

    # Ajouter un fichier audio au séquenceur vidéo
    ajouter_audio_animation(framerate_son, path_son)

    # Permet de générer l'animation
    render_animation()

if __name__ == '__main__':
    main()