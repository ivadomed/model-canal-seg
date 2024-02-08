#Authors : William Sirois

#J'importe ce dont j'ai besoin
import nibabel as nib
import matplotlib.pyplot as plt
import cv2 as cv
from skimage.morphology import disk
from skimage.segmentation import flood_fill
import scipy as sc
import numpy as np

def segmentcanal(csfseg,moelleseg) : 
#Fonction pour sauvegarder fournis par Sandrine
    def save_Nifti1(data, original_image, filename):
        empty_header = nib.Nifti1Header()
        image = nib.Nifti1Image(data, original_image.affine, empty_header)
        nib.save(image, filename)

#Je load l'image
    moelle=nib.load(moelleseg)
    moelle_np=moelle.get_fdata()
    img=nib.load(csfseg)
    img_np = img.get_fdata()

#Je copie l'image pour avoir l'image pour la sauvegarder à la fin
    img_b=img_np.copy()
    moelle_b=moelle_np.copy()
#Image qui sera remplie (besoin pour éviter les floodfill quand ce n'est pas fermé)
    img_fill=img_b.copy()

#Méthode du floodfill avec le centre de masse
    imagenbr=img_b.shape[2]#Je prend le nombre de coupe transversale
    slice=0
    h,w=img_b[:,:,1].shape

    while slice<imagenbr : #J'itère sur les images de coupe
        cmcsf=(sc.ndimage.center_of_mass(img_b[:,:,slice]))
        cmmoelle=(sc.ndimage.center_of_mass(moelle_b[:,:,slice]))
    
        if np.isnan(cmcsf[0]) and np.isnan(cmcsf[1]) : #Si il n'y as pas de segmentation sur le csf on ne change rien
            img_fill[:,:,slice]=img_b[:,:,slice] 

        else : #Si la segmentation n'est pas nulle dans la slice

            if np.isnan(cmmoelle[0]) and np.isnan(cmmoelle[1]) :#Si il n'y as pas de segmentation sur la moelle je ne change rien et je retire la segmentation du csf
                img_fill[:,:,slice]=0

            else :#Si il y as une segmentation de la moelle et du csf je prend le centre de masse de la moelle 
                cmmoelle=list(cmmoelle)
                cmmoelle[0]=int(cmmoelle[0])
                cmmoelle[1]=int(cmmoelle[1])
                img_fill[:,:,slice]=flood_fill(img_fill[:,:,slice],(cmmoelle[0],cmmoelle[1]),1)

                if np.sum(img_fill[:,:,slice]==1)==(h*w): #Si ma forme n'est pas fermée je reprend l'image de base et je fais une fermeture
                    img_fill[:,:,slice]=cv.morphologyEx(img_b[:,:,slice], cv.MORPH_CLOSE,disk(20))
            
        slice=slice+1 #Je passe à la prochaine slice

#Je sauvegarde l'image(Je ne sais pas comment renommer mes images seulement une façon qui ressemble à la votre)
    Nomdecanal=csfseg.replace("csfseg-manual_RPI_r.nii","canalseg-manual_RPI_r.nii.")
    save_Nifti1(img_fill,img, Nomdecanal)
segmentcanal("sub-pavia04_T2w_csfseg-manual_RPI_r.nii","sub-pavia04_T2w_seg.nii")