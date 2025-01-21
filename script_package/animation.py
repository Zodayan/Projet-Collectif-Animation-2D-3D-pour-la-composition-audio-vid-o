import re

import bpy
import os
import wave
import numpy as np

FRAMERATE_VIDEO = 24

def recupereration_objets_gltf(folder_path: str) -> list[bpy.types.Object]:
    """
    :param folder_path: chemin vers le dossier dans lequel récupérer les objets 3D, au format gltf/glb
    :return: une liste constituée d'objets 3D déjà ajoutés dans la scene
    """

    liste_objets = []

    # Récupération des chemins vers les objets
    liste_path_objets = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            liste_path_objets.append(os.path.join(root, file))

    i = 0
    for path_objet in liste_path_objets:
        # Ajoute l'objet dans la scene
        bpy.ops.import_scene.gltf(filepath=path_objet)
        objet = bpy.context.selected_objects[0]
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

def animer_objets_3d(liste_objets: list[bpy.types.Object], nb_keyframes_animation: int, int_buffer: list[int], frame_end: int) -> None:
    """
    Permet d'effectuer l'animation
    """

    i = 0
    for objet in liste_objets:
        for frame in range(nb_keyframes_animation):

            if frame == 0:
                objet.location = (i, i, int_buffer[frame] / max(int_buffer))
                objet.keyframe_insert("location", frame=1)
            else:
                objet.location = (i, i, int_buffer[frame] / max(int_buffer))
                objet.keyframe_insert("location", frame=(frame * frame_end / nb_keyframes_animation))
        i += 1

    # On fait en sorte que l'animation ne dure que 100 frames
    bpy.context.scene.frame_end = frame_end

def ajouter_audio_animation(frame_per_sec) -> None:
    """
    Permet de configurer et ajouter du son à la vidéo produite
    """
    audio_file = os.getcwd() + "/StarWarsMini.mp3"  # Chemin du fichier audio

    # Activer le séquenceur pour inclure le son
    scene = bpy.context.scene
    scene.sequence_editor_create()
    scene.sequence_editor.sequences.new_sound(
        name="Background Sound",
        filepath=audio_file,
        channel=1,
        frame_start=1,  # Début du son à la frame 1
    )

    # Activer le son dans le rendu
    scene.render.ffmpeg.audio_codec = 'AAC'  # Codec audio (AAC est largement compatible)
    scene.render.ffmpeg.audio_bitrate = 192  # Définir le bitrate audio (en kbps)
    scene.render.ffmpeg.audio_mixrate = frame_per_sec
    scene.render.ffmpeg.audio_channels = 'MONO'

def render_animation(frame_per_sec) -> None:
    """
    Permet de render l'animation
    """

    scene = bpy.context.scene

    # Configurer le rendu
    bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
    # On doit récupérer le current working directory, sinon l'animation va se créer à la racine de C:\
    bpy.context.scene.render.filepath = "".join(
        re.split("(\\\)", (os.getcwd()))[:-1]) + "animations/animation_objet.mp4"
    bpy.context.scene.render.ffmpeg.format = 'MPEG4'
    bpy.context.scene.render.ffmpeg.codec = 'H264'

    # Rendre l'animation
    bpy.ops.render.render(animation=True)

def main():
    """
    # Activer le GPU
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'OPTIX'  # Ou 'CUDA'
    bpy.context.preferences.addons['cycles'].preferences.get_devices()

    # Activer tous les GPU disponibles
    for device in bpy.context.preferences.addons['cycles'].preferences.devices:
        device.use = True
    """

    #####################################
    # PARTIE RECUPERATION DE LA MUSIQUE #
    #####################################

    # Ouverture du fichier wav en read-only
    sound = wave.open("StarWarsMini.wav", "rb")

    # Récupération des informations sur le son
    frame_per_sec = sound.getframerate()
    nb_frames = sound.getnframes()
    sample_width = sound.getsampwidth()
    nb_channels = sound.getnchannels()
    sound_duration = nb_frames / frame_per_sec

    # On calcule le nombre d'octets présents dans le son
    nb_bytes = nb_frames * nb_channels * sample_width

    # Récupération du son sous forme de tableau d'octets
    buffer = sound.readframes(sound.getnframes())

    # On ferme le fichier ouvert précédemment pour libérer la ressource
    sound.close()

    # Transformation du buffer d'entiers 8-bits en buffer d'entiers 16-bits signés
    buffer = np.frombuffer(buffer, dtype=np.int16)

    # Définition des paramètres d'animation en fonction de la musique
    nb_keyframes_animation = 50
    frame_end =  int(sound_duration * FRAMERATE_VIDEO) # n° de la frame de fin pour l'animation
    # Définition du buffer contenant les valeurs d'intensité des échantillons du son au moment des keyframes (d'amplitude frame_per_sec et centré en 0)
    int_buffer = [(buffer[i] / 256 * frame_per_sec) - frame_per_sec / 2 for i in
                  range(0, len(buffer), len(buffer) // nb_keyframes_animation)]

    ####################
    # PARTIE ANIMATION #
    ####################

    # Supprimer tous les objets de la scène
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    liste_objets = recupereration_objets_gltf("../objets3D")

    # Animer l'objet
    animer_objets_3d(liste_objets, nb_keyframes_animation, int_buffer, frame_end)

    # Ajouter de la caméra et de la lumière
    ajouter_camera_et_lumiere()

    # Ajouter un fichier audio au séquenceur vidéo
    ajouter_audio_animation(frame_per_sec)

    # Permet de générer l'animation
    render_animation(frame_per_sec)

if __name__ == '__main__':
    main()