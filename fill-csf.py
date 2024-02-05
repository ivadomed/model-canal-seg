#Authors : William Sirois

#J'importe ce dont j'ai besoin
import nibabel as nib
import matplotlib.pyplot as plt
import cv2 as cv
from skimage.morphology import disk
from skimage.segmentation import flood_fill
import scipy as sc
import numpy as np

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
#Image qui sera remplie (besoin pour éviter les floodfill quand ce n'est pas fermé)
img_fill=img_b.copy()

#Méthode du floodfill avec le centre de masse
imagenbr=img_b.shape[2]#Je prend le nombre de coupe transversale
slice=0
h,w=img_b[:,:,1].shape

while slice<imagenbr : #J'itère sur les images de coupe
    seed=(sc.ndimage.center_of_mass(img_b[:,:,slice]))
    
    if np.isnan(seed[0]) and np.isnan(seed[1]) : #Si l'image est toute noire on ne change rien
        img_fill[:,:,slice]=img_b[:,:,slice] 

    else : #Si la segmentation n'est pas nulle dans la slice
        seed=list(seed)
        seed[0]=int(seed[0])
        seed[1]=int(seed[1])
        if img_fill[:,:,slice][seed[0],seed[1]]==1 : #Si mon centre de masse est sur un pixel qui vaut 1 alors je fait une fermeture

            img_fill[:,:,slice]=cv.morphologyEx(img_b[:,:,slice], cv.MORPH_CLOSE,disk(20))
        else : #Sinon je remplis à partir du centre de masse avec un floodfill
            img_fill[:,:,slice]=flood_fill(img_fill[:,:,slice],(seed[0],seed[1]),1)

            if np.sum(img_fill[:,:,slice]==1)==(h*w): #Si ma forme n'est pas fermée je reprend l'image de base et je fais un floodfill
                img_fill[:,:,slice]=cv.morphologyEx(img_b[:,:,slice], cv.MORPH_CLOSE,disk(20))
            
    slice=slice+1 #Je passe à la prochaine slice

#Je sauvegarde l'image(Je ne sais pas comment renommer mes images seulement une façon qui ressemble à la votre)
save_Nifti1(img_fill,img,"sub-cmrrb03_T2w_canal-manual_RPI_r.nii.gz")