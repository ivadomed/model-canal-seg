#Authors : William Sirois

#J'importe ce dont j'ai besoin
import nibabel as nib
import matplotlib.pyplot as plt
import cv2
from skimage.morphology import disk

#Fonction pour sauvegarder fournis par Sandrine
def save_Nifti1(data, original_image, filename):
    empty_header = nib.Nifti1Header()
    image = nib.Nifti1Image(data, original_image.affine, empty_header)
    nib.save(image, filename)

#Je load l'image(pour l'instant j'ai mis le nom du fichier mais il faudra mettre de manière itérative)
img=nib.load("sub-cmrrb03_T2w_csfseg-manual_RPI_r.nii")
img_np = img.get_fdata()

#Je copie l'image pour avoir l'image pour la sauvegarder à la fin
img_b=img_np.copy()

#Je fais une fermeture avec un disque de 20(juste un essai certainement pas la meilleure valeure)
img_fill=cv2.morphologyEx(img_b, cv2.MORPH_CLOSE,disk(20))

#Je sauvegarde l'image(Je ne sais pas comment renommer mes images seulement une façon qui ressemble à la votre)
save_Nifti1(img_fill,img,"sub-cmrrb03_T2w_canal-manual_RPI_r.nii")