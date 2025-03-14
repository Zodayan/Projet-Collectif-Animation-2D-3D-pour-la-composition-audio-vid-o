import os
import subprocess

def list_images(directory="data"):
    """Liste toutes les images JPG et PNG disponibles dans un dossier."""
    images = [f for f in os.listdir(directory) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    return images

def segment_and_convert(image_path, save_name):
    """
    1. Segmente l'image et génère un fichier "_rgba.png".
    2. Demande à l'utilisateur un nom personnalisé pour `save_path`.
    3. Convertit l'image segmentée en 3D avec `save_path=save_name`.
    """

    # Extraire le nom de l'image sans extension
    image_name = os.path.basename(image_path).split('.')[0]

    # Nom de l'image segmentée
    segmented_image = f"data/{image_name}_rgba.png"

    # Commande pour segmenter l'image
    segmentation_cmd = f"python process.py {image_path}"
    print(f"🔹 Exécution : {segmentation_cmd}")
    subprocess.run(segmentation_cmd, shell=True, check=True)

    # Vérification que l'image segmentée a bien été générée
    if not os.path.exists(segmented_image):
        print(f" Erreur : L'image segmentée {segmented_image} n'a pas été générée.")
        return

    # Demander le nom personnalisé avant de lancer le rendu 3D
    print("\n Choisissez un nom pour l'objet 3D généré :")
    custom_name = input(f" Nom du fichier (par défaut : {save_name}): ").strip()

    # Si l'utilisateur ne met rien, utiliser le `save_name` par défaut
    if not custom_name:
        custom_name = save_name

    # Commande pour générer le modèle 3D avec le nom choisi
    render_cmd = f"python main.py --config configs/image.yaml input={segmented_image} save_path={custom_name}"
    print(f"🔹 Exécution : {render_cmd}")
    subprocess.run(render_cmd, shell=True, check=True)

    print(f" Processus terminé avec succès ! ")

if __name__ == "__main__":
    images = list_images()

    if not images:
        print(" Aucune image trouvée dans le dossier 'data/'. Ajoutez des fichiers JPG ou PNG.")
    else:
        print(" Images disponibles :")
        for i, img in enumerate(images, 1):
            print(f"{i}. {img}")

        # Demande à l'utilisateur de choisir une image
        choice = int(input("\n Sélectionne une image (1 - {}): ".format(len(images)))) - 1
        selected_image = os.path.join("data", images[choice])

        # Demande un nom de fichier personnalisé
        default_name = os.path.basename(selected_image).split('.')[0]

        print(f"\n Traitement de {selected_image}...\n")
        segment_and_convert(selected_image, default_name)
