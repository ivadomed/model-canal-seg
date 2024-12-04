# this aims to test code to measure the fluid signal loss
# we use the image and the segmentation
# after normalizing the image we get the FSL using a boolean mask

import nibabel as nib
import numpy as np

def calculer_intensite_moyenne(image_path, segmentation_path):
    # Charger les fichiers NIfTI
    image_nii = nib.load(image_path)
    segmentation_nii = nib.load(segmentation_path)
    
    # Obtenir les tableaux NumPy
    image_data = image_nii.get_fdata()
    segmentation_data = segmentation_nii.get_fdata()
    
    # Vérifier si les dimensions correspondent
    if image_data.shape != segmentation_data.shape:
        raise ValueError("Les dimensions de l'image et de la segmentation ne correspondent pas.")
    
    # Normaliser les valeurs de l'image (min-max scaling)
    image_normalized = (image_data - np.min(image_data)) / (np.max(image_data) - np.min(image_data))
    
    # Créer un masque booléen à partir de la segmentation (1 pour la partie anatomique, 0 ailleurs)
    mask = segmentation_data > 0  # Modifier si nécessaire selon vos valeurs de segmentation
    
    # Appliquer le masque pour sélectionner les valeurs correspondantes dans l'image normalisée
    valeurs_masquees = image_normalized[mask]
    
    # Calculer la moyenne des intensités
    intensite_moyenne = np.mean(valeurs_masquees)
    
    return intensite_moyenne

# Exemple d'utilisation
image_path = "chemin/vers/image.nii.gz"
segmentation_path = "chemin/vers/segmentation.nii.gz"
moyenne = calculer_intensite_moyenne(image_path, segmentation_path)
print(f"Intensité moyenne : {moyenne}")
