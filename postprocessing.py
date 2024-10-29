import numpy as np
import nibabel as nib
from scipy.ndimage import label

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

def process_segmentation_file(input_file, output_file):
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

if __name__ == "__main__":
    # Exemples d'utilisation
    input_nifti_file = "path_to_your_segmentation_file.nii.gz"
    output_nifti_file = "path_to_your_cleaned_segmentation_file.nii.gz"
    
    process_segmentation_file(input_nifti_file, output_nifti_file)
