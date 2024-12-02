# test for concavity measurement
# look at scipy and skimage libraries
# for now not working perfectly....

import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull
from skimage.measure import label, find_contours, regionprops

# flake8: noqa

def measure_concavity(binary_2d_array):
    # Identifier les contours de la structure
    contours = find_contours(binary_2d_array, level=0.5)
    if not contours:
        raise ValueError("No contours found in the binary array.")
    
    # Utiliser le plus grand contour
    largest_contour = max(contours, key=len)
    
    # Enveloppe convexe
    hull = ConvexHull(largest_contour)
    
    # Aire de la structure et de l'enveloppe convexe
    original_area = np.sum(binary_2d_array)  # Nombre total de pixels à 1
    hull_area = hull.volume  # Aire de l'enveloppe convexe
    
    # Vérification
    print(f"Original area: {original_area}, Hull area: {hull_area}")
    if hull_area < original_area:
        print("Warning: Hull area is smaller than the original area. Check input contours.")
    
    # Calcul du ratio de concavité
    concavity_ratio = (hull_area - original_area) / hull_area if hull_area > 0 else 0
    
    return {
        "concavity_area": concavity_ratio,
        "original_contour": largest_contour,
        "hull": hull,
    }

# Exemple d'utilisation
binary_array = np.zeros((100, 100), dtype=int)
binary_array[30:70, 40:60] = 1  # Une structure rectangulaire
binary_array[30:45, 40:45] = 0  # Ajout d'une concavité
'''binary_array[65:70, 55:60] = 0 
binary_array[50:65, 51:60] = 0''' 

result = measure_concavity(binary_array)

# Affichage des résultats
print(f"Concavity (area ratio): {result['concavity_area']:.2f}")

# Visualisation
contour = result['original_contour']
hull = result['hull']

'''plt.imshow(binary_array, cmap='gray')
plt.plot(contour[:, 1], contour[:, 0], 'r-', label="Original contour")
for simplex in hull.simplices:
    plt.plot(hull.points[simplex, 1], hull.points[simplex, 0], 'b-', label="Convex hull" if simplex[0] == 0 else "")
plt.legend()
plt.show()'''

import numpy as np
import matplotlib.pyplot as plt

from skimage import measure


# Construct some test data
x, y = np.ogrid[-np.pi : np.pi : 100j, -np.pi : np.pi : 100j]
r = np.sin(np.exp(np.sin(x) ** 3 + np.cos(y) ** 2))

# Find contours at a constant value of 0.8
contours = measure.find_contours(r, 0.99)

# Display the image and plot all contours found
fig, ax = plt.subplots()
ax.imshow(r, cmap=plt.cm.gray)

for contour in contours:
    ax.plot(contour[:, 1], contour[:, 0], linewidth=2)

ax.axis('image')
ax.set_xticks([])
ax.set_yticks([])
plt.show()
