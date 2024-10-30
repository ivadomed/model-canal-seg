import numpy as np
import nibabel as nib
from scipy.ndimage import label
import os

def keep_largest_connected_component(segmentation):
    """
    Garde uniquement le plus grand composant connexe d'une image de segmentation binaire.
    
    Parameters:
        segmentation (numpy.ndarray): Image de segmentation binaire (3D).
    
    Returns:
        numpy.ndarray: Image de segmentation avec uniquement le plus grand composant connexe.
    """
    # Label tous les composants connexes
    labeled_array, num_features = label(segmentation)
    
    # Si plusieurs composants connexes sont trouvés
    if num_features > 1:
        # Calculer les tailles de chaque composant
        component_sizes = np.bincount(labeled_array.ravel())
        print('component_sizes:', component_sizes)
        
        # Ignorer la taille du background (index 0)
        component_sizes[0] = 0
        
        # Trouver l'indice du plus grand composant
        largest_component = component_sizes.argmax()
        print('largest_component:', largest_component)
        
        # Créer une nouvelle image avec uniquement le plus grand composant
        largest_component_mask = (labeled_array == largest_component).astype(np.uint8)
        print('largest_component_mask_size:', np.bincount(largest_component_mask.ravel()))
        
        '''return largest_component_mask'''
    else:
        print('No post-processing needed')
        '''# S'il n'y a qu'un seul composant connexe, on retourne l'image d'origine
        return segmentation'''

def process_segmentation_file(input_file, output_file=None):
    """
    Charge un fichier NIfTI, applique le post-traitement et sauvegarde le résultat.
    
    Parameters:
        input_file (str): Chemin du fichier NIfTI d'entrée (segmentation binaire).
        output_file (str): Chemin du fichier NIfTI de sortie (après post-traitement).
    """
    print('Processing:', input_file)

    # Charger l'image NIfTI
    img = nib.load(input_file)
    segmentation = img.get_fdata()
    keep_largest_connected_component(segmentation)

    '''# Appliquer le post-traitement
    cleaned_segmentation = keep_largest_connected_component(segmentation)'''

    '''# Sauvegarder le résultat dans un nouveau fichier NIfTI
    cleaned_img = nib.Nifti1Image(cleaned_segmentation, img.affine)
    nib.save(cleaned_img, output_file)'''

def process_segmentation_folder(input_folder, output_folder=None):
    """
    Charge tous les fichiers NIfTI d'un dossier, applique le post-traitement et sauvegarde les résultats.
    
    Parameters:
        input_folder (str): Chemin du dossier d'entrée contenant les fichiers NIfTI de segmentation.
        output_folder (str): Chemin du dossier de sortie pour les fichiers NIfTI après post-traitement.
    """
    for file_name in os.listdir(input_folder):
        if file_name.endswith('.nii.gz'):
            input_file = os.path.join(input_folder, file_name)
            # output_file = os.path.join(output_folder, file_name)
            process_segmentation_file(input_file)

# input = "C:/Users/abels/OneDrive/Documents/NeuroPoly/canal_seg/segmentation/training/data/test_for_postprocessing/segmentations_raw"
input = "C:/Users/abels/OneDrive/Documents/NeuroPoly/canal_seg/segmentation/training/data/datasets/Dataset011_clean_copy/labelsTr"
process_segmentation_folder(input)

