# Importation des bibliothèques nécessaires
import cv2
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk  # Tkinter pour l'interface de sélection d'image
from tkinter import filedialog

root = tk.Tk()
root.withdraw() 
# Ouvre une boîte de dialogue pour choisir une image (formats acceptés : JPG, JPEG, PNG)
image_path = filedialog.askopenfilename(title="Sélectionnez une image", filetypes=[("Images", "*.jpg;*.jpeg;*.png")])

# Vérifier si l'utilisateur a sélectionné un fichier
if not image_path:
    raise FileNotFoundError("Aucune image sélectionnée.")

print(f"L'image sélectionnée est : {image_path}")

# Charger l'image avec OpenCV
image = cv2.imread(image_path)
if image is None:
    raise FileNotFoundError(f"L'image spécifiée est introuvable : {image_path}")

# OpenCV charge l'image en format BGR par défaut, il faut la convertir en RGB
image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# Création d'un masque de la même taille que l'image (valeurs initialisées à 0)
mask = np.zeros(image.shape[:2], dtype=np.uint8)

# Définition d'un rectangle autour de l'objet à segmenter (on suppose l'objet centré)
height, width = image.shape[:2]
rect = (10, 10, width - 20, height - 20)

# Création des modèles de fond et de premier plan (requis par GrabCut)
bgd_model = np.zeros((1, 65), dtype=np.float64)
fgd_model = np.zeros((1, 65), dtype=np.float64)

# Appliquer GrabCut pour améliorer la segmentation
cv2.grabCut(image, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)

# Convertir le masque en binaire
mask_binary = np.where((mask == 2) | (mask == 0), 0, 1).astype(np.uint8)

# Application du masque sur l'image originale pour isoler l'objet
background_removed = cv2.bitwise_and(image_rgb, image_rgb, mask=mask_binary)

# Convertir l'image en format RGBA (ajout d'une couche alpha pour le fond transparent)
result = cv2.cvtColor(background_removed, cv2.COLOR_RGB2RGBA)
result[:, :, 3] = mask_binary * 255  # Transparence basée sur le masque

# Créer un fond coloré (par exemple, bleu clair)
background_color = (135, 206, 235)  # Bleu clair
colored_background = np.full_like(image_rgb, background_color, dtype=np.uint8)

# Fusion de l'image segmentée avec le fond coloré
alpha = mask_binary[:, :, None]  # Ajouter une dimension pour le canal alpha
colored_result = (background_removed * alpha + colored_background * (1 - alpha)).astype(np.uint8)

# Afficher les résultats
plt.figure(figsize=(15, 10))

# Image originale
plt.subplot(1, 3, 1)
plt.title("Image Originale")
plt.imshow(image_rgb)
plt.axis("off")

# Image segmentée avec fond transparent
plt.subplot(1, 3, 2)
plt.title("Image Segmentée (Fond Transparent)")
plt.imshow(result)
plt.axis("off")

# Image segmentée sur fond coloré
plt.subplot(1, 3, 3)
plt.title("Image Segmentée (Fond Coloré)")
plt.imshow(colored_result)
plt.axis("off")

plt.show()

# Sauvegarde en format PNG (avec couche alpha pour la transparence)
output_path_transparent = "result_transparent.png"
output_path_colored = "result_colored.png"
cv2.imwrite(output_path_transparent, cv2.cvtColor(result, cv2.COLOR_RGBA2BGRA))
cv2.imwrite(output_path_colored, cv2.cvtColor(colored_result, cv2.COLOR_RGB2BGR))
print(f"L'image segmentée avec fond transparent a été sauvegardée à : {output_path_transparent}")
print(f"L'image segmentée avec fond coloré a été sauvegardée à : {output_path_colored}")
