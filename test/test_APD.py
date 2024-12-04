# test for APD measurement
# then also use to look at compression ratio (CR)

import nibabel as nib
import numpy as np

def calculer_diametre_ap(segmentation_path, slice_index):
    # Charger la segmentation NIfTI
    segmentation_nii = nib.load(segmentation_path)
    segmentation_data = segmentation_nii.get_fdata()
    
    # Vérifier si la slice demandée existe
    if slice_index < 0 or slice_index >= segmentation_data.shape[2]:
        raise ValueError("Index de la slice hors des dimensions de la segmentation.")
    
    # Extraire la slice 2D
    slice_2d = segmentation_data[:, :, slice_index]
    
    # Créer un masque pour la partie anatomique
    mask = slice_2d > 0  # Modifier si nécessaire selon vos valeurs de segmentation
    
    # Trouver les indices des pixels actifs dans l'axe antéro-postérieur (axe 0 : vertical)
    coords = np.where(mask)
    if coords[0].size == 0:
        raise ValueError("Aucune structure détectée dans cette slice pour la segmentation donnée.")
    
    # Calculer les limites supérieures et inférieures (min et max des indices dans l'axe 0)
    min_ap = np.min(coords[0])
    max_ap = np.max(coords[0])
    
    # Calculer le diamètre en pixels
    diametre_pixels = max_ap - min_ap
    
    # Convertir en mm si les dimensions du voxel sont disponibles
    voxel_dims = segmentation_nii.header.get_zooms()
    diametre_mm = diametre_pixels * voxel_dims[0]  # Voxel size dans l'axe 0 (antéro-postérieur)
    
    return diametre_pixels, diametre_mm

# Exemple d'utilisation
segmentation_path = "chemin/vers/segmentation.nii.gz"
slice_index = 50  # Index de la slice à analyser
diametre_pixels, diametre_mm = calculer_diametre_ap(segmentation_path, slice_index)

print(f"Diamètre antéro-postérieur : {diametre_pixels} pixels, {diametre_mm:.2f} mm")
