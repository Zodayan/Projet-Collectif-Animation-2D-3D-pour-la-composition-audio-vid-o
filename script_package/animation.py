import bpy
import math
import os
import wave
from wave import Wave_read

def main():
    # Ouverture du fichier wav en read-only
    sound = wave.open("StarWarsMini.wav", "rb")
    frame_per_sec = sound.getframerate()
    buffer = sound.readframes(sound.getnframes())
    nb_frames = 50
    frame_end =  int(len(buffer)/frame_per_sec * 24)//2 # *24 car animation a 24 fps
    int_buffer = [(buffer[i] / 256 * 44.1 * 1000) - 44.1 * 1000 / 2 for i in
                  range(0, len(buffer), len(buffer) // nb_frames)]

    # Supprimer tous les objets de la scène
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Ajouter un cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object  # Récupérer une référence à l'objet

    # Modifier les propriétés du matériau
    material = bpy.data.materials.new(name="CustomMaterial")
    material.diffuse_color = (1.0, 0.0, 0.0, 1.0)  # Rouge
    bpy.context.object.data.materials.append(material)

    # Étape 2 : Animer l'objet
    scene = bpy.context.scene

    for frame in range(nb_frames):

        if frame == 0:
            cube.location = (0, 0, int_buffer[frame]/max(int_buffer))
            cube.keyframe_insert("location", frame=1)
        else:
            cube.location = (0, 0, int_buffer[frame]/max(int_buffer))
            cube.keyframe_insert("location", frame=(frame * frame_end / nb_frames))

    # On ferme le fichier ouvert précédemment pour libérer la ressource
    sound.close()

    # On fait en sorte que l'animation ne dure que 100 frames
    bpy.context.scene.frame_end = frame_end

    # Ajouter une caméra
    bpy.ops.object.camera_add(location=(7, -7, 5))  # Position de la caméra
    camera = bpy.context.object  # Référence à l'objet caméra
    camera.rotation_euler = (1.2, 0, 0.8)  # Orientation de la caméra

    # Définir cette caméra comme caméra active pour le rendu
    bpy.context.scene.camera = camera

    # Étape 3 : Sauvegarder la scène et rendre l'animation
    #bpy.ops.wm.save_mainfile(filepath="animated_scene.blend")

    # Ajouter un fichier audio au séquenceur vidéo
    audio_file = os.getcwd() + "/StarWarsMini.mp3"  # Chemin du fichier audio

    # Activer le séquenceur pour inclure le son
    scene.sequence_editor_create()
    scene.sequence_editor.sequences.new_sound(
        name="Background Sound",
        filepath=audio_file,
        channel=1,
        frame_start=1,  # Début du son à la frame 1
    )

    # Configurer le rendu
    bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
    # On doit récupérer le current working directory, sinon l'animation va se créer à la racine de C:\
    bpy.context.scene.render.filepath = os.getcwd() + "/animation_cube.mp4"
    bpy.context.scene.render.ffmpeg.format = 'MPEG4'
    bpy.context.scene.render.ffmpeg.codec = 'H264'

    # Activer le son dans le rendu
    scene.render.ffmpeg.audio_codec = 'AAC'  # Codec audio (AAC est largement compatible)
    scene.render.ffmpeg.audio_bitrate = 192  # Définir le bitrate audio (en kbps)
    scene.render.ffmpeg.audio_mixrate = 44100
    scene.render.ffmpeg.audio_channels = 'MONO'

    # Rendre l'animation
    bpy.ops.render.render(animation=True)

if __name__ == '__main__':
    main()