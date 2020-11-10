import SimpleITK as sitk
import matplotlib.pyplot as plt
import numpy as np
from ipywidgets import interact, interactive
from ipywidgets import widgets
from keras.models import load_model
import keras.losses
from segmentation_models.losses import *
from segmentation_models.metrics import *
import imageio

model = load_model("D:\\TCC\\Backup\\h5s\\f81-flair-64\\flair_64_model.h5", custom_objects={'Dice Coefficient' : FScore(), 'Dice Loss' : DiceLoss()}, compile=False)

def myshow(img, title=None, margin=0.05, dpi=80 ):
    nda = sitk.GetArrayFromImage(img)

    spacing = img.GetSpacing()
    slicer = False

    if nda.ndim == 3:
        # fastest dim, either component or x
        c = nda.shape[-1]

        # the the number of components is 3 or 4 consider it an RGB image
        if not c in (3,4):
            slicer = True

    elif nda.ndim == 4:
        c = nda.shape[-1]

        if not c in (3,4):
            raise RuntimeError("Unable to show 3D-vector Image")

        # take a z-slice
        slicer = True

    if (slicer):
        ysize = nda.shape[1]
        xsize = nda.shape[2]
    else:
        ysize = nda.shape[0]
        xsize = nda.shape[1]


    # Make a figure big enough to accomodate an axis of xpixels by ypixels
    # as well as the ticklabels, etc...
    figsize = (1 + margin) * ysize / dpi, (1 + margin) * xsize / dpi
    def callback(z=None):

        extent = (0, xsize*spacing[1], ysize*spacing[0], 0)

        fig = plt.figure(figsize=figsize, dpi=dpi)

        # Make the axis the right size...
        ax = fig.add_axes([margin, margin, 1 - 2*margin, 1 - 2*margin])

        plt.set_cmap("gray")

        if z is None:
            ax.imshow(nda,extent=extent,interpolation=None)
        else:
            ax.imshow(nda[z,...],extent=extent,interpolation=None)

        if title:
            plt.title(title)

        plt.show()

    if slicer:
        interact(callback, z=(0,nda.shape[0]-1))
    else:
        callback()

def myshow3d(img, xslices=[], yslices=[], zslices=[], title=None, margin=0.05, dpi=80):
    size = img.GetSize()
    img_xslices = [img[s,:,:] for s in xslices]
    img_yslices = [img[:,s,:] for s in yslices]
    img_zslices = [img[:,:,s] for s in zslices]

    maxlen = max(len(img_xslices), len(img_yslices), len(img_zslices))


    img_null = sitk.Image([0,0], img.GetPixelID(), img.GetNumberOfComponentsPerPixel())

    img_slices = []
    d = 0

    if len(img_xslices):
        img_slices += img_xslices + [img_null]*(maxlen-len(img_xslices))
        d += 1

    if len(img_yslices):
        img_slices += img_yslices + [img_null]*(maxlen-len(img_yslices))
        d += 1

    if len(img_zslices):
        img_slices += img_zslices + [img_null]*(maxlen-len(img_zslices))
        d +=1

    if maxlen != 0:
        if img.GetNumberOfComponentsPerPixel() == 1:
            img = sitk.Tile(img_slices, [maxlen,d])
        #TODO check in code to get Tile Filter working with VectorImages
        else:
            img_comps = []
            for i in range(0,img.GetNumberOfComponentsPerPixel()):
                img_slices_c = [sitk.VectorIndexSelectionCast(s, i) for s in img_slices]
                img_comps.append(sitk.Tile(img_slices_c, [maxlen,d]))
            img = sitk.Compose(img_comps)


    myshow(img, title, margin, dpi)

def sliceSaver(image):
    middle = int(image.GetSize()[2]/2)
    axialSlice = np.rot90(sitk.GetArrayFromImage(image)[middle,:,:], 2)
    coronalSlice = np.rot90(sitk.GetArrayFromImage(image)[:,middle,:], 2)
    sagitalSlice = np.rot90(sitk.GetArrayFromImage(image)[:,:,middle], 2)

    imageio.imwrite('D:\\TCC\\input\\axialSlice.png', axialSlice)
    imageio.imwrite('D:\\TCC\\input\\coronalSlice.png', coronalSlice)
    imageio.imwrite('D:\\TCC\\input\\sagitalSlice.png', sagitalSlice)
    
def dc(seg, ref):
    dice = sitk.LabelOverlapMeasuresImageFilter()
    dice.Execute(seg, ref)
    return dice.GetDiceCoefficient()

def volume(image, label=1):
    # check if is a file or a path, if is a path then load the image
    if(isinstance(image, str)):
        image = sitk.ReadImage(image, sitk.sitkInt16)
           
    maskArray = sitk.GetArrayFromImage(image) # get the calcification mask pixel array
    pxX, pxY, pxZ = image.GetSpacing() # get the x, y and z spacing (mm³) from metadata

    count, _, _ = np.where(maskArray == label) # count the number of voxels
    volume = len(count)*pxX*pxY*pxZ # multiply number of voxels with voxel spacing (x,y,z) getting the result in mm³
    
    return int(volume)/1000

def volumeProportion(refMask, segMask): # refference mask and segmentation mask
    # check if is a file or a path, if is a path then load the image
    if(isinstance(refMask, str)):
        refMask = sitk.ReadImage(refMask, sitk.sitkInt16)
        
    if(isinstance(segMask, str)):
        segMask = sitk.ReadImage(segMask, sitk.sitkInt16)
    
    refVol = volume(refMask) # get volume from reference mask
    segVol = volume(segMask) # get volume from segmentation mask
    
    proportion = (segVol/refVol)*100 # calculate proportion in %

    return proportion

def downsample(image, size):
    
    new_size = [size, size, size]

    xyfactor = image.GetSize()[0]/size
    zfactor = image.GetSize()[2]/size

    resample = sitk.ResampleImageFilter()
    resample.SetInterpolator(sitk.sitkLinear)
    resample.SetOutputDirection(image.GetDirection())
    resample.SetOutputOrigin(image.GetOrigin())
    new_spacing = (image.GetSpacing()[0]*xyfactor, image.GetSpacing()[1]*xyfactor, image.GetSpacing()[2]*zfactor)
    resample.SetOutputSpacing(new_spacing)

    orig_size = np.array(image.GetSize(), dtype=np.int)
    orig_spacing = [spacing for spacing in image.GetSpacing()]
    new_size = np.ceil(new_size).astype(np.int) #  image dimensions are in integers
    new_size = [int(s) for s in new_size]
    resample.SetSize(new_size)

    return resample.Execute(image)

def prediction(image):
    imageArr = sitk.GetArrayFromImage(image)

    array = np.array([imageArr])
    array = array[None, ...]

    #print(f'Predicting... {array.shape}')
    
    output = model.predict(array)
    output = np.squeeze(output)
    output.shape
    #print(f'Output prediction: {output.shape}')

    tpm = sitk.GetImageFromArray(output[0])
    tpm.CopyInformation(image)

    return tpm