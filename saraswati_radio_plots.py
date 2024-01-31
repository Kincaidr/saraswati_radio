#!/usr/bin/env python
from astropy import coordinates as coords
import matplotlib.pyplot as plt
import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from matplotlib.pyplot import show, plot, draw
from scipy.constants import pi
import scipy.constants as constants
import statistics as stats
import astropy.cosmology as cp
import sys
from astropy.io import fits
import glob
import matplotlib.cm as cm
import os
import numpy as np
import bdsf
from astropy.stats import SigmaClip
from astropy.stats import sigma_clipped_stats
import aplpy
import re
from scipy.stats import norm
from astropy.cosmology import FlatLambdaCDM
from astropy.cosmology import Planck13, z_at_value
from matplotlib.patches import Circle
from astropy.wcs import WCS
from astropy.nddata.utils import Cutout2D
from astropy.table import Table, Column
from scipy.optimize import curve_fit
from scipy.optimize import minimize, basinhopping
from scipy.stats import cumfreq

def write_catalog(fits_files,cluster_name,app_image,int_image):
    

    img = bdsf.process_image(int_image, rms_box=(40,40),rms_box_bright=(15,15),adaptive_thresh=150,thresh_isl=4.0,thresh_pix=5.0,
                 detection_image=app_image,interactive=False,clobber=True,spectralindex_do = False,atrous_do = False) #spectralindex_do = True
    
 
    # img = bdsf.process_image(int_image, rms_box=(40,40),rms_box_bright=(15,15),adaptive_thresh=150,thresh_isl=4.0,thresh_pix=5.0,
    #                detection_image=app_image,interactive=False,clobber=True,spectralindex_do = False,atrous_do = False,shapelet_do = False) 
    
    # img = bdsf.process_image(int_image, rms_box=(20,10),adaptive_thresh=100,thresh_isl=4.0,thresh_pix=5.0,
    #                          detection_image=app_image)
    
    img.export_image(outfile=fits_files+cluster_name+'_rms_map.fits',clobber=True,img_type='rms')
    img.export_image(outfile=fits_files+cluster_name+'_res_map.fits',clobber=True,img_type='gaus_resid')

    img.write_catalog(outfile=fits_files+cluster_name+'_srl.fits',format='fits', catalog_type='srl',clobber=True)

    #sdsd
    # img = bdsf.process_image(int_image, rms_box=(40,40),rms_box_bright=(15,15),adaptive_thresh=150,thresh_isl=4.0,thresh_pix=5.0,
    #                detection_image=app_image,interactive=False,clobber=True,spectralindex_do = False,atrous_do = False,shapelet_do = True) 
        


def write_simulated_catalog(fits_files,cluster_name,app_image,int_image):
    

    #img = bdsf.process_image(int_image, rms_box=(30,30),rms_box_bright=(12,12),adaptive_thresh=150,thresh_isl=4.0,thresh_pix=5.0,
       #            detection_image=app_image,interactive=False,clobber=True,spectralindex_do = False) #spectralindex_do = True
    
    #img = bdsf.process_image(int_image, rms_box=(40,40),rms_box_bright=(15,15),adaptive_thresh=150,thresh_isl=3.0,thresh_pix=5.0,
    #               detection_image=app_image,interactive=False,clobber=True,spectralindex_do = True,atrous_do = False) 
    
    img = bdsf.process_image(int_image,thresh_isl=3.0,thresh_pix=5.0,
                   detection_image=app_image,interactive=False,clobber=True,spectralindex_do = True,atrous_do = False) 

    img.write_catalog(outfile=fits_files+cluster_name+'_srl.fits',format='fits', catalog_type='srl',clobber=True)




def plot_image(folder_path,cluster_name,res_image,fits_image,tessel_region):


    def rms_value(fits_image):

        image = fits.open(fits_image)
        prihdr = image[0].header
        data = image[0].data
        image_data = data#[0,0,:,:]
        image_data=np.nan_to_num(image_data)
        image_mean, image_median, image_stddev = sigma_clipped_stats(image_data, sigma = 3.0)#, iters = 5)

        print (image_stddev)
        rms=image_stddev 

        return(rms)


    def correct_axes(fits_image):

        data_hdu = fits.open(fits_image)[0]
        data = data_hdu.data
        header = data_hdu.header
        #data = data[0,0,:,:]
        data = data[:,:]

        header = header.copy()
        header['WCSAXES'] = 2
        header['NAXIS'] = 2
        del header['*3']
        del header['*4']
        new_fits_image=fits_image.replace(fits_image[:-4],'_corrected_axes.fits')
        w = WCS(header)

        fits.writeto(new_fits_image, header=header, data=data, overwrite=True)
        return(new_fits_image,data,header,w)
    
    def tessels(region_file):


        # Read the .reg file
        with open(region_file, 'r') as file:
            content = file.read()

        # Use regular expressions to extract lines without "point"
        pattern = re.compile(r"(^point\(.+?\) # .+$)", re.MULTILINE)
        filtered_content = re.sub(pattern, '', content)

        new_region_file='region_file_new.reg'
        
        with open(new_region_file, 'w') as file:
            file.write(filtered_content)

        return(new_region_file)
    
    new_fits_res_image,res_data,res_header,w1=correct_axes(res_image)

    new_fits_image,data,header,w=correct_axes(fits_image)

    position = SkyCoord(res_header['CRVAL1']*u.deg, res_header['CRVAL2']*u.deg,frame='fk5',equinox='J2000.0') 

    #cutout = Cutout2D(res_data,position=position,size=u.Quantity((60,60), u.arcmin),wcs=w1,mode='partial').data

    cutout_image='res_cutout.fits'
    #fits.writeto(cutout_image, header=res_header, data=cutout, overwrite=True)
    
    rms=rms_value(new_fits_res_image)

    rms=15e-6
   

    new_region_file=tessels(tessel_region)

    data_hdu = fits.open(fits_image)[0]
    data_header = data_hdu.header

    f= aplpy.FITSFigure(new_fits_image) 

    #f.show_colorscale(cmap='inferno',vmin =0,vmax=0.00005) 
    
    f.show_colorscale(cmap='gray',vmin =(-5*rms),vmax=(20*rms)) # cutouts

    #f.show_colorscale(cmap='gray',vmin =(1.0175e-05),vmax=(11e-05),vmid=0.0175e-05,stretch='log')
    

    f.recenter(data_header['CRVAL1'], data_header['CRVAL2'], width =2,height = 2)
    f.add_colorbar()
    
    f.colorbar.set_font(size=30)

    f.tick_labels.set_font(size=30)
    f.axis_labels.set_font(size=30)
    f.add_scalebar(0.0688)
    f.scalebar.set_label('1 Mpc')
    f.scalebar.set_color('black')
    f.scalebar.set_font_size(size=14)
    
    f.colorbar.set_axis_label_text('Jy/beam')
    f.colorbar.set_axis_label_font(size='x-large')
    f.colorbar.set_font(size='large')
    #f.show_regions(new_region_file)
    f.tick_labels.set_font(size='x-large')
    f.axis_labels.set_font(size='x-large')
    f.add_beam()
    f.beam.set_major(0.00222222)  # degrees
    f.beam.set_minor(0.00166667)
    f.beam.set_color("black")
    f.beam.set_hatch('+')
    f.beam.set_edgecolor('yellow')
    f.savefig(folder_path+cluster_name+'_kms_image.pdf')



def pb_attenuation(fits_files,cluster_name,radio_catalog_fits,radio_catalog_app_fits):

   
    import IPython;IPython.embed()

    int_cat=Table.read( radio_catalog_fits)

    app_cat=Table.read(radio_catalog_app_fits)


    rms=(15e-6)

    app_flux=app_cat['Total_flux']

    mask=app_flux/rms >= 20

    app_flux= app_flux[mask]

    int_flux=int_cat['Total_flux']

    mask=int_flux/rms >= 20

    int_flux=int_flux[mask]


    if len(int_flux) > len(app_flux):
        int_flux=int_flux[:len(app_flux)]
    else:
        app_flux=app_flux[:len(int_flux)]

    plt.plot(app_flux,app_flux)

    plt.scatter(app_flux,int_flux)

    plt.xlim(0,1)
    plt.ylim(0,1)
    plt.show()


def smearing(folder_path,cluster_name,radio_catalog,cluster_centre):

    
    t=Table.read(radio_catalog)

    ra=t['RA']
    dec=t['DEC']

    position=SkyCoord(ra, dec, frame='icrs',unit=(u.deg,u.deg))
    
    cluster_centre=SkyCoord(str(354.4195 ), str(0.27909), frame='icrs',unit=(u.deg,u.deg))

    distance= np.abs(cluster_centre.separation(position))

    mask=distance.deg < 2

    t_new=t[mask]

    distance=distance[mask]

    flux_MeerKAT=t_new['Total_flux']

    peak_MeerKAT=t_new['Peak_flux']

    flux_err_MeerKAT=t_new['E_Total_flux']

    Ratio=(flux_MeerKAT/peak_MeerKAT)

    num_bins = 5

    # Calculate the bin edges based on the x data range
    bin_edges = np.linspace(distance.min(), distance.max(), num_bins + 1)

    # Use np.digitize to bin the x data
    bin_indices = np.digitize(distance, bin_edges)

    # Calculate the median of y for each bin
    bin_medians = [np.median(Ratio[bin_indices == i]) for i in range(1, num_bins + 1)]

    
    plt.plot(bin_edges[:-1] + np.diff(bin_edges) / 2, bin_medians, color='red', marker='x', label='Median flux ratio')
                
    plt.scatter(distance,Ratio, alpha=0.7,s=10,label='Compact sources')

    
    plt.ylim(0,5)
    
    plt.axhline(y=1, color='black',linewidth=2)
    #plt.title(f"{cluster_name} Measured integrated flux density vs peak flux ", fontsize=13)
    plt.xlabel('Distance from pointing centre (deg)',fontsize=15)
    plt.ylabel(r'$S_{T}/S_{P}$',fontsize=15)
    plt.tight_layout()
    plt.legend()
    plt.savefig(folder_path+cluster_name+'_ratio_fluxes.pdf')
    plt.show() 
  



def  radio_cutouts(output_path,fits_image_A2631,fits_image_Zwcl2341):


    def correct_axes(fits_image):

        data_hdu = fits.open(fits_image)[0]
        data = data_hdu.data
        header = data_hdu.header
        data = data[0,0,:,:]
        header = header.copy()
        header['WCSAXES'] = 2
        header['NAXIS'] = 2
        del header['*3']
        del header['*4']
        del header['HISTORY']
        new_fits_image='deleted_axes.fits'
        w = WCS(header)

        fits.writeto(new_fits_image, header=header, data=data, overwrite=True)
        return(new_fits_image,header)
    
    
    
    new_fits_image,header=correct_axes(fits_image_A2631)

 
    fig = plt.figure(figsize=(10, 10))


   
            
    f= aplpy.FITSFigure(new_fits_image,figure=fig, subplot=[0.05, 0.74, 0.2, 0.2]) 

    #f.show_colorscale(cmap='inferno',vmin =0,vmax=0.00005) 
    
    f.show_colorscale(cmap='gray',vmin =(1.0175e-05),vmax=(11e-05),vmid=0.0175e-05,stretch='log') # cutouts

    f.recenter(353.3307451, -0.4450689, width =0.08,height = 0.08)
    
    f.add_scalebar(50/3600)
    f.scalebar.set_length(50/3600)
    f.scalebar.set_label(r'$50''$')
    f.scalebar.set_color('green')
    f.scalebar.set_font_size(size=20)
    f.ticks.hide()
    f.tick_labels.hide()
    f.axis_labels.hide()
    f.axis_labels.hide_x()
    f.axis_labels.hide_y()

    f= aplpy.FITSFigure(new_fits_image,figure=fig, subplot=[0.28, 0.74, 0.2, 0.2]) 

    #f.show_colorscale(cmap='inferno',vmin =0,vmax=0.00005) 
    
    f.show_colorscale(cmap='gray',vmin =(1.0175e-05),vmax=(11e-05),vmid=0.0175e-05,stretch='log') # cutouts

    f.recenter(354.4408546, -0.7057400, width =0.05,height = 0.05)
    
    f.add_scalebar(30/3600)
    f.scalebar.set_length(30/3600)
    f.scalebar.set_label(r'$30''$')
    f.scalebar.set_color('green')
    f.scalebar.set_font_size(size=20)
    f.ticks.hide()
    f.tick_labels.hide()
    f.axis_labels.hide()
    f.axis_labels.hide_x()
    f.axis_labels.hide_y()

    f= aplpy.FITSFigure(new_fits_image,figure=fig, subplot=[0.51, 0.74, 0.2, 0.2]) 

    #f.show_colorscale(cmap='inferno',vmin =0,vmax=0.00005) 
    
    f.show_colorscale(cmap='gray',vmin =(1.0175e-05),vmax=(11e-05),vmid=0.0175e-05,stretch='log')  # cutouts

    f.recenter(354.6049207, -0.1103067, width =0.03,height = 0.03)
    
    f.add_scalebar(30/3600)
    f.scalebar.set_length(30/3600)
    f.scalebar.set_label(r'$30''$')
    f.scalebar.set_color('green')
    f.scalebar.set_font_size(size=20)
    f.ticks.hide()
    f.tick_labels.hide()
    f.axis_labels.hide()
    f.axis_labels.hide_x()
    f.axis_labels.hide_y()

    f= aplpy.FITSFigure(new_fits_image,figure=fig, subplot=[0.74, 0.74, 0.2, 0.2]) 

    #f.show_colorscale(cmap='inferno',vmin =0,vmax=0.00005) 
    
    f.show_colorscale(cmap='gray',vmin =(1.0175e-05),vmax=(11e-05),vmid=0.0175e-05,stretch='log')  # cutouts

    f.recenter(354.4219862, 0.2838064, width =0.07,height = 0.07)
    
    f.add_scalebar(50/3600)
    f.scalebar.set_length(50/3600)
    f.scalebar.set_label(r'$50''$')
    f.scalebar.set_color('green')
    f.scalebar.set_font_size(size=20)
    f.ticks.hide()
    f.tick_labels.hide()
    f.axis_labels.hide()
    f.axis_labels.hide_x()
    f.axis_labels.hide_y()



    f= aplpy.FITSFigure(new_fits_image,figure=fig, subplot=[0.05, 0.51, 0.2, 0.2]) 

    #f.show_colorscale(cmap='inferno',vmin =0,vmax=0.00005) 
    
    f.show_colorscale(cmap='gray',vmin =(1.0175e-05),vmax=(11e-05),vmid=0.0175e-05,stretch='log') # cutouts

    f.recenter(353.7103476, -0.1737802, width =0.05,height = 0.05)
    
    f.add_scalebar(30/3600)
    f.scalebar.set_length(30/3600)
    f.scalebar.set_label(r'$30''$')
    f.scalebar.set_color('green')
    f.scalebar.set_font_size(size=20)
    f.ticks.hide()
    f.tick_labels.hide()
    f.axis_labels.hide()
    f.axis_labels.hide_x()
    f.axis_labels.hide_y()

    


    f= aplpy.FITSFigure(new_fits_image,figure=fig, subplot=[0.28, 0.51, 0.2, 0.2]) 

    #f.show_colorscale(cmap='inferno',vmin =0,vmax=0.00005) 
    
    f.show_colorscale(cmap='gray',vmin =(1.0175e-05),vmax=(11e-05),vmid=0.0175e-05,stretch='log')  # cutouts

    f.recenter(354.1316771, 0.2962445, width =0.05,height = 0.05)
    
    f.add_scalebar(30/3600)
    f.scalebar.set_length(30/3600)
    f.scalebar.set_label(r'$30''$')
    f.scalebar.set_color('green')
    f.scalebar.set_font_size(size=20)
    f.ticks.hide()
    f.tick_labels.hide()
    f.axis_labels.hide()
    f.axis_labels.hide_x()
    f.axis_labels.hide_y()

    

    f= aplpy.FITSFigure(new_fits_image,figure=fig, subplot=[0.51, 0.51, 0.2, 0.2]) 

    #f.show_colorscale(cmap='inferno',vmin =0,vmax=0.00005) 
    
    f.show_colorscale(cmap='gray',vmin =(1.0175e-05),vmax=(11e-05),vmid=0.0175e-05,stretch='log') # cutouts

    f.recenter(353.9070295, 0.2746370, width =0.07,height = 0.07)
    
    f.add_scalebar(50/3600)
    f.scalebar.set_length(50/3600)
    f.scalebar.set_label(r'$50''$')
    f.scalebar.set_color('green')
    f.scalebar.set_font_size(size=20)
    f.ticks.hide()
    f.tick_labels.hide()
    f.axis_labels.hide()
    f.axis_labels.hide_x()
    f.axis_labels.hide_y()

    new_fits_image,header=correct_axes(fits_image_Zwcl2341)

    f= aplpy.FITSFigure(new_fits_image,figure=fig, subplot=[0.74, 0.51, 0.2, 0.2]) 

    #f.show_colorscale(cmap='inferno',vmin =0,vmax=0.00005) 
    
    f.show_colorscale(cmap='gray',vmin =(1.0175e-05),vmax=(11e-05),vmid=0.0175e-05,stretch='log')  # cutouts

    f.recenter(356.1199781, 0.6516063, width =0.05,height = 0.05)
    
    f.add_scalebar(30/3600)
    f.scalebar.set_length(30/3600)
    f.scalebar.set_label(r'$30''$')
    f.scalebar.set_color('green')
    f.scalebar.set_font_size(size=20)
    f.ticks.hide()
    f.tick_labels.hide()
    f.axis_labels.hide()
    f.axis_labels.hide_x()
    f.axis_labels.hide_y()

    f.savefig(output_path+'_cutout.pdf')
       # fits.writeto(folder_path+cluster_name+cutout_image, header=header, data=cutout, overwrite=True)



def rms_plot(folder_path,cluster_name,fits_image,rms_image):


    def rms_value(rms_image):

        image = fits.open(fits_image)
        prihdr = image[0].header
        data = image[0].data
        image_data = data#[0,0,:,:]
        image_data=np.nan_to_num(image_data)

        img_min, img_max = np.min(image_data),np.max(image_data)
        img_mean=np.mean(image_data);img_median=np.median(image_data);img_std=np.std(image_data)
        

        sigclip = SigmaClip(sigma = 3.0)#, iters=5)
        image_data_sigclip = sigclip(image_data)
        image_min_clip, image_max_clip = np.min(image_data_sigclip),np.max(image_data_sigclip)
        image_mean_clip=np.mean(image_data_sigclip);image_median_clip=np.median(image_data_sigclip);image_std_clip=np.std(image_data_sigclip)
        

        image_mean, image_median, image_stddev = sigma_clipped_stats(image_data, sigma = 3.0)#, iters = 5)
   
        #print ('rms is',image_stddev)
        rms=image_stddev 

        return(rms)


    def correct_axes(rms_image):

        data_hdu = fits.open(rms_image)[0]
        data_data = data_hdu.data
        data_header = data_hdu.header
        new_data = data_data[:,:]

        data_header['WCSAXES'] = 2
        data_header['NAXIS'] = 2
        del data_header['*3']
        del data_header['*4']
        new_fits_image='deleted_axes.fits'
        w = WCS(data_header)
        fits.writeto(new_fits_image, header=data_header, data=new_data, overwrite=True)
        return(new_fits_image,new_data,data_header,w)
    
    
    new_fits_image,new_data,data_header,w=correct_axes(rms_image)
    position = SkyCoord(data_header['CRVAL1']*u.deg, data_header['CRVAL2']*u.deg,frame='fk5',equinox='J2000.0') 
    cutout = Cutout2D(new_data,position=position,size=u.Quantity((30,30), u.arcmin),wcs=w,mode='partial').data
    cutout_image='cutout.fits'
    fits.writeto(cutout_image, header=data_header, data=cutout, overwrite=True)


    rms_full=rms_value(rms_image)
    rms_cutout=rms_value(cutout_image )
    rms_cutout=15e-6

    print('rms full value is ', rms_value(rms_image))

    contours=[5,10] * np.array(rms_cutout)
    data_hdu = fits.open(new_fits_image)[0]
    data_header = data_hdu.header

    f= aplpy.FITSFigure(new_fits_image) 

    f.show_colorscale(cmap='cubehelix_r',pmin =0.5,pmax=50) # cutouts


    f.recenter(data_header['CRVAL1'], data_header['CRVAL2'], width =2,height = 2)
    f.add_colorbar()
    
    f.colorbar.set_font(size=30)
    f.show_contour(levels=contours,smooth=5)
    f.tick_labels.set_font(size=30)
    f.axis_labels.set_font(size=30)
    f.add_scalebar(0.0688)
    f.scalebar.set_label('1 Mpc')
    f.scalebar.set_color('green')
    f.scalebar.set_font_size(size=14)
    f.colorbar.set_axis_label_text('Jy/beam')
    f.colorbar.set_axis_label_font(size='x-large')
    f.colorbar.set_font(size='large')
    #f.show_regions(new_region_file)
    f.tick_labels.set_font(size='x-large')
    f.axis_labels.set_font(size='x-large')
    #f.add_colorbar()

    # f.add_beam()
    # f.beam.set_major(0.00222222)  # degrees
    # f.beam.set_minor(0.00166667)
    # f.beam.set_color("black")
    # f.beam.set_hatch('+')
    # f.beam.set_edgecolor('yellow')
    
    f.savefig(folder_path+cluster_name+'_kms_rms_image.pdf')



def cumulative_rms_map(output_path,cluster_name,fits_image):


    def rms_value(image_data):

    
        image_data=np.nan_to_num(image_data)

        img_min, img_max = np.min(image_data),np.max(image_data)
        img_mean=np.mean(image_data);img_median=np.median(image_data);img_std=np.std(image_data)
        

        sigclip = SigmaClip(sigma = 3.0)#, iters=5)
        image_data_sigclip = sigclip(image_data)
        image_min_clip, image_max_clip = np.min(image_data_sigclip),np.max(image_data_sigclip)
        image_mean_clip=np.mean(image_data_sigclip);image_median_clip=np.median(image_data_sigclip);image_std_clip=np.std(image_data_sigclip)
        

        image_mean, image_median, image_stddev = sigma_clipped_stats(image_data, sigma = 3.0)#, iters = 5)
   
        #print ('rms is',image_stddev)
        rms=image_stddev 

        return(rms)


    def correct_axes(fits_image):

        data_hdu = fits.open(fits_image)[0]
        data_data = data_hdu.data
        data_header = data_hdu.header
        new_data = data_data[0,0,:,:]
       
        data_header['WCSAXES'] = 2
        data_header['NAXIS'] = 2
        del data_header['*3']
        del data_header['*4']
        new_fits_image='deleted_axes.fits'
        w = WCS(data_header)
        fits.writeto(new_fits_image, header=data_header, data=new_data, overwrite=True)
        return(new_fits_image,new_data,data_header,w)
    

    new_fits_image,new_data,data_header,w=correct_axes(fits_image)

   
    #import IPython;IPython.embed()


    data=new_data.flatten()

    _, x = np.histogram(data,bins=100)
    x += ((x[1]-x[0])/2)
    x = x[:-1]
    #plt.hist(data,cumulative=True,bins=100,histtype='step')
    y = cumfreq(data, numbins=100).cumcount
    plt.plot(x*10**3, y*(1.5/3600)**2)
   # plt.xlim(0,0.0015 )

    plt.xlabel(r'cumulative RMS $(\mu Jy/bm)$',fontsize=17)
    plt.ylabel(r'Area ($deg^2$)',fontsize=17)
    plt.savefig(output_path+cluster_name+'_cumulative_rms.pdf')
    plt.show()


    
def resolved_unresolved_sources(output_path,radio_catalog):

    
    radio_catalogue= fits.open(radio_catalog)
    radio_cat=radio_catalogue[1].data


    flux_MeerKAT=radio_cat['Total_Flux']

    peak_MeerKAT=radio_cat['Peak_flux']

    code=radio_cat['S_Code']

    rms = 15e-6
    y=flux_MeerKAT/peak_MeerKAT
    x=peak_MeerKAT/rms

    mask=(x < (10**3)) & (y < 1)

    x, y = x[mask], y[mask]
    mid=len(y)//3

    ord=np.argsort(x)
    x, y = x[ord], y[ord]

    x1=x[:mid]
    x2=x[mid:2*mid]
    x3=x[2*mid:]


    y1=y[:mid]
    y2=y[mid:2*mid]
    y3=y[2*mid:]

    def func(params, x1, y1, x2, y2,x3,y3):

        a, b = params
        f1 = 1 + a*(x1)**(-b)
        
        counter1 = np.sum(f1 < y1)

        val1 = abs(0.9 - (counter1/len(x1)))
    
        f2 = 1 + a*(x2)**(-b)
        counter2 = np.sum(f2 < y2)
        val2 = abs(0.9 - (counter2/len(x2)))
    

        f3 = 1 + a*(x3)**(-b)
        counter3 = np.sum(f3 < y3)
        val3 = abs(0.9 - (counter3/len(x3)))
        print(val1,val2,val3)
        return val1+val2+val3

    x0 = [-1, 0.3]
    minimizer_kwargs = {"args":(x1, y1, x2, y2, x3, y3)}
    res = basinhopping(func, x0, minimizer_kwargs=minimizer_kwargs, niter=1000) #, tol=1e-6,method='Nelder-Mead')#'Nelder-Mead')#, constraints={'k':[0, 10], 'c':[0, 15]})#,method='Powell')


    print(res.x[0],res.x[1])
    mask_unres=(np.array(code[mask]) == 'S') 

    mask_res=(np.array(code[mask]) != 'S') 
    
    
    t = np.linspace(x.min(), 10**6, 10000)
    
    #import IPython;IPython.embed()

    x0=-0.9137940578423331
    x1=0.4642323636146572
    # x0=res.x[0]
    # x1=res.x[1]


    
    y=flux_MeerKAT/peak_MeerKAT
    x=peak_MeerKAT/rms
    curve=1+x0*(x)**(-x1)

    curve1=1+x0*(t)**(-x1)

    #fig  = plt.figure(figsize=(15, 7))

    unresolved_mask= (y > curve) & (y < (2-curve))

    resolved_mask= ~unresolved_mask

    total_unresolved=np.sum(unresolved_mask)

    total_resolved=np.sum(resolved_mask)

    print("Total unresolved sources",total_unresolved)
    print("Total resolved sources",total_resolved)



    fig,ax=plt.subplots()
    ax.fill_between(t,curve1,2-curve1,alpha=0.6,label='unresolved sources')

    plt.plot(t,curve1,linewidth=2,color='black')
    plt.plot(t,-(curve1-2),linewidth=2,color='black')

    # plt.plot(t,int_curve,linewidth=2,color='red')
    # plt.plot(t,2-int_curve,linewidth=2,color='red')
    plt.axhline(y=1,color='r',linestyle='--')


    plt.scatter(x,y,alpha=0.5,s=10,color='grey')

    plt.xlabel(r'$S_P/\sigma$',fontsize=18)
    # plt.xlim(0,500)
    # plt.ylim(-1,8)
    plt.ylabel(r'$S_T/ S_P$',fontsize=18)
    plt.xscale('log')
    plt.yscale('log')
    #plt.ylim([0., 11])
    plt.xlim([3, 1000])
    plt.tight_layout()
    plt.legend()
    plt.savefig(output_path+'_resolved_unresolved.pdf')
    plt.show()

    return(unresolved_mask,resolved_mask)



def spectral_distributions(output_path,radio_catalogue_fits):

    radio_catalogue= fits.open(radio_catalogue_fits)
    radio_cat=radio_catalogue[1].data
    import IPython;IPython.embed()
    flux_MeerKAT_raw=radio_cat['Total_Flux_1']*10**3 
    spec_indx_raw=radio_cat['Spec_indx_1']
    e_spec_indx=radio_cat['E_Spec_indx_1']
    code=radio_cat['S_Code_1']
    
    mask=  (spec_indx_raw > -3) & (spec_indx_raw < 3) # & (flux_MeerKAT_raw / radio_cat["Peak_flux_1"] > 0.8) & (flux_MeerKAT_raw/ radio_cat["Peak_flux_1"] < 1.5) & (radio_cat["Peak_flux_1"] / 15e-6  > 100) & (radio_cat["Peak_flux_1"] > np.percentile(radio_cat["Peak_flux_1"], 5.0))& (radio_cat["E_Total_flux_1"] / flux_MeerKAT_raw * 100 < 10) 
    

    spec_indx = spec_indx_raw[mask]

    n, bins = np.histogram(spec_indx, bins=30)
    bin_centers = (bins[:-1] + bins[1:]) / 2

    spec_bin_centre=(bins[np.argmax(n)]+bins[np.argmax(n)+1])/2

    median_value=np.median(spec_indx)

    print('Median value', median_value)

    print('Total entries', len(spec_indx))

    fig = plt.figure(figsize=(15, 7))

    plt.hist(spec_indx, bins=bin_centers,alpha=0.7)
    plt.axvline(median_value,linestyle='dashed',color='black')
    plt.xlabel(r'$\alpha_{855}^{1710}$',fontsize=20)
    plt.ylabel('Count',fontsize=20)
   # plt.title(cluster_name,fontsize=22)
    plt.text(0.95, 0.95, rf'$\alpha$ = {median_value:.2f}', transform=plt.gca().transAxes, ha='right', va='top',fontsize=20)
    plt.savefig(output_path+'_spec_index_histogram.pdf')
    plt.show()





def spectral_index(folder_path,cluster_name,radio_catalog):



    flux_MeerKAT_raw=radio_cat['Total_Flux']*10**3
    flux_err_MeerKAT=radio_cat['E_Total_Flux']


    spec_indx_raw=radio_cat['Spec_indx']
    e_spec_indx=radio_cat['E_Spec_indx']

    mask=  (spec_indx_raw > -3) & (spec_indx_raw < 3)  & (radio_cat["Total_flux"] / radio_cat["Peak_flux"] > 0.8) & (radio_cat["Total_flux"] / radio_cat["Peak_flux"] < 1.5) & (radio_cat["Peak_flux"] / 15e-6  > 100) & (radio_cat["Peak_flux"] > np.percentile(radio_cat["Peak_flux"], 5.0))& (radio_cat["E_Total_flux"] / radio_cat["Total_flux"] * 100 < 10)

    flux_MeerKAT=flux_MeerKAT_raw[mask ]                          

    spec_indx = spec_indx_raw[mask]

    num_bins = 5

    # Calculate the bin edges based on the x data range
    bin_edges = np.linspace(50, flux_MeerKAT.max(), num_bins + 1)

    # Use np.digitize to bin the x data
    bin_indices = np.digitize(flux_MeerKAT, bin_edges)

    # Calculate the median of y for each bin
    bin_medians = [np.nanmedian(spec_indx[bin_indices == i]) for i in range(1, num_bins + 1)]

    plt.plot(bin_edges[:-1] + np.diff(bin_edges) / 2, bin_medians, color='red', marker='x', label=r'Median $\alpha^{1710}_{855}$')

    plt.scatter(flux_MeerKAT,spec_indx,alpha=0.7,s=10,label='Compact sources')

    plt.title(f"{cluster_name} Spectral index distribution as a function of flux density ", fontsize=13)
    plt.xlabel(r'$S_{1283 MHz} \; (\mu Jy)$',fontsize=15)
    plt.ylabel(r'$\alpha^{1710}_{855}$ ',fontsize=15)
    
    plt.legend()
    plt.savefig(folder_path+cluster_name+'_flux_spectral_indices.pdf')
    plt.show() 


def spatial_spectral_index(folder_path,radio_catalog):


    radio_catalogue_fits = fits.open(radio_catalog)

    radio_cat= radio_catalogue_fits[1].data

    code=radio_cat['S_Code']

    spec_indx=radio_cat['Spec_indx']
    e_spec_indx=radio_cat['E_Spec_indx']
    flux_MeerKAT=radio_cat['Total_flux']*10**3

    ra=radio_cat['RA']
    dec=radio_cat['DEC']    
    mask_1=(np.array(code) == 'S') & (spec_indx > -3) & (spec_indx < 3)  


    plt.scatter(ra[mask_1],dec[mask_1],c= spec_indx[mask_1],cmap='viridis', alpha=0.7,s=10)
    cbar = plt.colorbar(location='right')
    cbar.set_label('Spectral index',fontsize=15)


    #plt.title(f"{cluster_name}  Spectral index spatial distribution", fontsize=13)
    plt.xlabel(r'RA',fontsize=15)
    plt.ylabel(r'DEC',fontsize=15)
 

    plt.legend()
    plt.savefig(folder_path+'_spatial_spectral_indices.pdf')
    plt.show() 



def spectral_index_distance(folder_path,cluster_name,radio_catalog,cluster_centre):


    code=radio_catalog['S_Code']

    spec_indx_raw=radio_catalog['Spec_indx']
    e_spec_indx_raw=radio_catalog['E_Spec_indx']

    flux_MeerKAT=radio_catalog['Total_flux']*10**3

    ra=radio_catalog['RA']
    dec=radio_catalog['DEC']


    mask_1=(np.array(code) == 'S') & (spec_indx_raw > -3) & (spec_indx_raw < 3)  &  (flux_MeerKAT > 1) & (flux_MeerKAT < 100) 

    mask_2=(np.array(code) != 'S') & (spec_indx_raw > -3) & (spec_indx_raw < 3)  & (flux_MeerKAT > 1) & (flux_MeerKAT < 100)


    ra_point=ra[mask_1]
    dec_point=dec[mask_1]

    ra_other=ra[mask_2]
    dec_other=dec[mask_2]

    
    position_point=SkyCoord(ra_point, dec_point, frame='icrs',unit=(u.deg,u.deg))

    position_other=SkyCoord(ra_other, dec_other, frame='icrs',unit=(u.deg,u.deg))
    #import pdb; pdb.set_trace()

    distance_point= np.abs(cluster_centre.separation(position_point))

    distance_other= np.abs(cluster_centre.separation(position_other))


    spec_indx_point=spec_indx_raw[mask_1]
    spec_indx_other=spec_indx_raw[mask_2]

    e_spec_indx_point=e_spec_indx_raw[mask_1]
    e_spec_indx_other=e_spec_indx_raw[mask_2]

    num_bins = 10

    # Calculate the bin edges based on the x data range
    bin_edges_point = np.linspace(distance_point.min(), distance_point.max(), num_bins + 1)
    bin_edges_other = np.linspace(distance_point.min(), distance_point.max(), num_bins + 1)

    # Use np.digitize to bin the x data
    bin_indices_point = np.digitize(distance_point, bin_edges_point)
    bin_indices_other = np.digitize(distance_other, bin_edges_other)

    # Calculate the median of y for each bin
    bin_medians_point = [np.nanmedian(spec_indx_point[bin_indices_point == i]) for i in range(1, num_bins + 1)]
    bin_medians_other = [np.nanmedian(spec_indx_other[bin_indices_other == i]) for i in range(1, num_bins + 1)]

    
    plt.plot(bin_edges_point[:-1] + np.diff(bin_edges_point) / 2, bin_medians_point, color='red', marker='x', label=r'Median $\alpha^{1710}_{855}$ ratio for compact sources ')

    plt.plot(bin_edges_other[:-1] + np.diff(bin_edges_other) / 2, bin_medians_other, color='green', marker='x', label=r'Median $\alpha^{1710}_{855}$  ratio for other sources ')
    
    plt.scatter(distance_point,spec_indx_point, alpha=0.7,s=10,label='Compact sources')
    plt.scatter(distance_other,spec_indx_other,alpha=0.7,s=10,label='Non-compact sources')
    
    #plt.ylim(0,5)
    
    plt.axhline(y=-0.8, color='black',linewidth=1,linestyle='--')
    plt.title(f"{cluster_name}"r" $\alpha^{1710}_{855}$ vs Distance from phase centre", fontsize=13)
    plt.xlabel('Distance from pointing centre (deg)',fontsize=15)
    plt.ylabel(r'$\alpha^{1710}_{855}$ ',fontsize=15)
  
    plt.legend()
    plt.savefig(folder_path+cluster_name+'_spectral_index_distance.pdf')
    plt.show() 


def radio_lumo_distance(output_path,cluster_name,radio_optical_catalog,cluster_centre):


    flux_MeerKAT_raw=radio_optical_catalog['Total_Flux']*10**3
    spec_indx_raw=radio_optical_catalog['Spec_indx']
    e_spec_indx=radio_optical_catalog['E_Spec_indx']
    code=radio_optical_catalog['S_Code']

    photoz=radio_optical_catalog['z_phot_median']
    
    mask=(np.array(code) == 'S') & (flux_MeerKAT_raw > 1) & ( ~np.isnan(spec_indx_raw)) & (photoz > 0) & (flux_MeerKAT_raw < 100)

    z=photoz[mask]
    spec_indx = spec_indx_raw[mask]
    flux_MeerKAT=flux_MeerKAT_raw[mask]

    ra=radio_optical_catalog['RA'][mask]
    dec=radio_optical_catalog['DEC'][mask]    

    position=SkyCoord(ra, dec, frame='icrs',unit=(u.deg,u.deg))

    #import pdb; pdb.set_trace()

    distance= np.abs(cluster_centre.separation(position))
    h=0.7
    H0=h*100
    cosmo = cp.FlatLambdaCDM(H0=h*100, Om0=0.30)

    def radio_lum(flux,z,si,freq):

        S_14=(np.array(flux)/(freq**si)) * (1400e6**si)

        lumo_distance=np.array(cosmo.luminosity_distance(z))

        radio_lumo=(4*np.pi*(S_14*10**-26)*(lumo_distance*3.086e22)**2)*(1/(1+(z**(si+1))))

        return(radio_lumo)
    

    radio_lumo= radio_lum(flux_MeerKAT,z,spec_indx,1280e+6)

    num_bins = 5


    bin_edges = np.linspace(0, distance.value.max(), num_bins + 1)


    bin_indices = np.digitize(distance.value, bin_edges)

    # Calculate the median of y for each bin

    bin_medians = [np.nanmedian(radio_lumo[bin_indices == i]) for i in range(1, num_bins + 1)]

    plt.plot(bin_edges[:-1] + np.diff(bin_edges) / 2, bin_medians, color='red', marker='x')

    lumo=radio_lum(flux_MeerKAT,z,spec_indx,1280e6)


    plt.scatter(distance,lumo,c= spec_indx,cmap='viridis', alpha=0.7,s=10)
    cbar = plt.colorbar(location='right')
    cbar.set_label('Spectral index',fontsize=15)

    plt.title(r"{cluster_name}  L_{1.4 GHz} vs Distance", fontsize=13)
    plt.xlabel(r'Distance from phase centre',fontsize=15)
    plt.ylabel(r'Radio lumonisity',fontsize=15)
    plt.legend()
    plt.savefig(output_path+cluster_name+'_radio_power_distance.pdf')
    plt.show() 



def flux_distribution(output_path,radio_catalog):

    radio_catalogue_fits = fits.open(radio_catalog)

    radio_cat= radio_catalogue_fits[1].data

    flux_MeerKAT_raw=radio_cat['Total_Flux']*10**3

    code=radio_cat['S_Code']
    #import IPython;IPython.embed()

    
    mask=(np.array(code) == 'S')   & (flux_MeerKAT_raw < 100) 


    flux=flux_MeerKAT_raw[mask]

    
    n, bins = np.histogram(flux, bins=70)
    bin_centers = (bins[:-1] + bins[1:]) / 2

    spec_bin_centre=(bins[np.argmax(n)]+bins[np.argmax(n)+1])/2

    mean_value=np.mean(flux)

    print('Mean value', mean_value)

    print('Total enetries', len(flux))
    
    fig = plt.figure(figsize=(15, 7))

    plt.hist(flux, bins=bin_centers,alpha=0.7)
    plt.axvline(mean_value,linestyle='dashed',color='black')
    plt.xlabel('Flux in mJy',fontsize=18)
    plt.ylabel('Count',fontsize=18)
    plt.text(0.95, 0.95, rf'Mean flux value = {mean_value:.2f} mJy', transform=plt.gca().transAxes, ha='right', va='top',fontsize=17)
    plt.xlim(0,20*mean_value)
    #plt.text(0.95, 0.95, rf'$\alpha$ = {median_value:.2f}', transform=plt.gca().transAxes, ha='right', va='top',fontsize=20)
    plt.savefig(output_path+'_flux_histogram.pdf')
    plt.show()


def radio_power_distributions(output_path,cluster_name,radio_optical_catalog):

    flux_MeerKAT_raw=radio_optical_catalog['Total_Flux']*10**3 
    spec_indx_raw=radio_optical_catalog['Spec_indx']
    e_spec_indx=radio_optical_catalog['E_Spec_indx']
    code=radio_optical_catalog['S_Code']
    #import IPython;IPython.embed()
    photoz=radio_optical_catalog['z_phot_median']
    
    mask=(np.array(code) == 'S') & (flux_MeerKAT_raw > 1) & ( ~np.isnan(spec_indx_raw)) & (photoz > 0) & (flux_MeerKAT_raw < 100)

    z=photoz[mask]
    spec_indx = spec_indx_raw[mask]
    flux_MeerKAT=flux_MeerKAT_raw[mask]

    h=0.7
    H0=h*100
    cosmo = cp.FlatLambdaCDM(H0=h*100, Om0=0.30)

    def radio_lum(flux,z,si,freq):

        S_14=(np.array(flux)/(freq**si)) * (1400e6**si)

        lumo_distance=np.array(cosmo.luminosity_distance(z))

        radio_lumo=(4*np.pi*(S_14*10**-26)*(lumo_distance*3.086e22)**2)*(1/(1+(z**(si+1))))

        return(radio_lumo)
    

    radio_lumo= radio_lum(flux_MeerKAT,z,spec_indx,1280e+6)

    
    n, bins = np.histogram(radio_lumo, bins=30)
    bin_centers = (bins[:-1] + bins[1:]) / 2

    spec_bin_centre=(bins[np.argmax(n)]+bins[np.argmax(n)+1])/2

    median_value=np.median(radio_lumo)

    print('Median value', median_value)

    print('Total enetries', len(radio_lumo))

    fig = plt.figure(figsize=(15, 7))

    plt.hist(radio_lumo, bins=bin_centers,alpha=0.7)
    plt.axvline(median_value,linestyle='dashed',color='black')
    plt.xlabel(r'$L_{1.4GHz}$',fontsize=20)
    plt.ylabel('Count',fontsize=20)
    plt.title(cluster_name,fontsize=22)
    #plt.text(0.95, 0.95, rf'$\alpha$ = {median_value:.2f}', transform=plt.gca().transAxes, ha='right', va='top',fontsize=20)
    plt.savefig(output_path+cluster_name+'_radio_power_histogram.pdf')
    plt.show()


def redshift_distributions(output_path,cluster_name,radio_optical_catalog):


   #import IPython;IPython.embed()
    photoz=radio_optical_catalog['z_phot_median']
    
    mask= (photoz > 0) & (photoz < 1)

    z=photoz[mask]

    h=0.7
    H0=h*100
    cosmo = cp.FlatLambdaCDM(H0=h*100, Om0=0.30)


    
    n, bins = np.histogram(z, bins=30)
    bin_centers = (bins[:-1] + bins[1:]) / 2

    spec_bin_centre=(bins[np.argmax(n)]+bins[np.argmax(n)+1])/2

    median_value=np.mean(z)

    print('Median value', median_value)

    print('Min z value', np.min(z))

    print('Max z value', np.max(z))



    fig = plt.figure(figsize=(15, 7))

    plt.hist(z, bins=bin_centers,alpha=0.7)
    plt.axvline(median_value,linestyle='dashed',color='black')
    plt.xlabel(r'photo_z',fontsize=20)
    plt.ylabel('Count',fontsize=20)
    plt.text(0.15, 0.95, rf'Average redshift = {median_value:.2f}', transform=plt.gca().transAxes, ha='left', va='top',fontsize=20)
    plt.title(cluster_name,fontsize=22)
    #plt.text(0.95, 0.95, rf'$\alpha$ = {median_value:.2f}', transform=plt.gca().transAxes, ha='right', va='top',fontsize=20)
    plt.savefig(output_path+cluster_name+'_redshift_histogram.pdf')
    plt.show()



def astrometry_NVSS(output_path,MeerKAT_NVSS_cat):

        MeerKAT_NVSS_cat = fits.open(MeerKAT_NVSS_cat)[1].data
  
        corrective_offset=(0.0, 0.0)

        mask=  np.where((MeerKAT_NVSS_cat["Total_flux"] / MeerKAT_NVSS_cat["Peak_flux"] > 0.2) & (MeerKAT_NVSS_cat["Total_flux"] / MeerKAT_NVSS_cat["Peak_flux"] < 1.8) & (MeerKAT_NVSS_cat["S1.4"]  > 0.001) & (MeerKAT_NVSS_cat["Total_Flux"] > 0.001) &(MeerKAT_NVSS_cat['Total_flux'] / 15e-6  > 50))

        MeerKAT_NVSS_cat=MeerKAT_NVSS_cat[mask]

        MeerKAT_coord=SkyCoord(MeerKAT_NVSS_cat['RA']*u.deg,MeerKAT_NVSS_cat['DEC']*u.deg, frame='fk5')

        NVSS_coord=SkyCoord(MeerKAT_NVSS_cat['RAJ2000']*u.deg,MeerKAT_NVSS_cat['DEJ2000']*u.deg, frame='fk5')
     

        delta_RA= (MeerKAT_coord.ra.value - NVSS_coord.ra.value)*3600
        delta_DEC= (MeerKAT_coord.dec.value - NVSS_coord.dec.value)*3600
  
        

        fig, ax = plt.subplots(figsize=(11, 7))

        plt.scatter(delta_DEC,delta_RA, c="k", marker="o", alpha=0.3)

        plt.axvline(np.mean(delta_DEC),linestyle='dashed',color='black')
        plt.axhline(np.mean(delta_RA),linestyle='dashed',color='black')

        plt.axvline(np.mean(delta_DEC), color="k", linestyle="--", alpha=0.3,
            label="MeerKAT offset to NVSS $\Delta \\alpha , \Delta\delta$={0:.2f}\",{1:.2f}\"".format(np.mean(delta_RA),np.mean(delta_DEC)))
        
        plt.axhline(np.mean(delta_RA), color="k", linestyle="--", alpha=0.3)
        circle=plt.Circle((np.mean(delta_DEC), np.mean(delta_RA)), np.std(delta_RA), edgecolor= 'red',facecolor='None', linewidth=2, alpha=1 ,ls = 'dashed') 
        plt.gca().add_patch(circle)
        ax.add_patch(circle)
        circle2=plt.Circle((np.mean(delta_DEC), np.mean(delta_RA)), 3*np.std(delta_RA), edgecolor= 'red',facecolor='None', linewidth=2, alpha=1 ,ls = 'dashed') 
        plt.gca().add_patch(circle2)
        ax.add_patch(circle2)
        print('mean in RA is',np.mean(delta_RA) )   
        print('mean in DEC is',np.mean(delta_DEC) )
        plt.xlabel('$\delta_{MeerAKT} - $ (arcsec)',fontsize=17)
        plt.ylabel('dRA (arcsec)',fontsize=17)
        plt.title('NVSS',fontsize=20)
        plt.xlim(-5,5)
        plt.ylim(-5,5)
        plt.savefig(output_path+'NVSS_astrometry.pdf')
        plt.legend()
        plt.show()


def astrometry_FIRST(output_path,MeerKAT_NVSS_cat):

        MeerKAT_NVSS_cat = fits.open(MeerKAT_NVSS_cat)[1].data
  
        corrective_offset=(0.0, 0.0)

        mask=  np.where((MeerKAT_NVSS_cat["Total_flux"] / MeerKAT_NVSS_cat["Peak_flux"] > 0.2) & (MeerKAT_NVSS_cat["Total_flux"] / MeerKAT_NVSS_cat["Peak_flux"] < 1.8) & (MeerKAT_NVSS_cat["Fint"]  > 0.001) & (MeerKAT_NVSS_cat["Total_Flux"] > 0.001) &(MeerKAT_NVSS_cat['Total_flux'] / 15e-6  > 50))

        MeerKAT_NVSS_cat=MeerKAT_NVSS_cat[mask]

        MeerKAT_coord=SkyCoord(MeerKAT_NVSS_cat['RA']*u.deg,MeerKAT_NVSS_cat['DEC']*u.deg, frame='fk5')

        NVSS_coord=SkyCoord(MeerKAT_NVSS_cat['RAJ2000']*u.deg,MeerKAT_NVSS_cat['DEJ2000']*u.deg, frame='fk5')
     

        delta_RA= (MeerKAT_coord.ra.value - NVSS_coord.ra.value)*3600
        delta_DEC= (MeerKAT_coord.dec.value - NVSS_coord.dec.value)*3600
  
        

        fig, ax = plt.subplots(figsize=(11, 7))

        plt.scatter(delta_DEC,delta_RA, c="k", marker="o", alpha=0.3)
        plt.xlim(-4,4)
        plt.ylim(-4,4)
        plt.axvline(np.mean(delta_DEC),linestyle='dashed',color='black')
        plt.axhline(np.mean(delta_RA),linestyle='dashed',color='black')
        #plt.tight_layout()
        plt.axvline(np.mean(delta_DEC), color="k", linestyle="--", alpha=0.3,
            label="MeerKAT offset to FIRST $\Delta \\alpha , \Delta\delta$={0:.2f}\",{1:.2f}\"".format(np.mean(delta_RA),np.mean(delta_DEC)))
        
        plt.axhline(np.mean(delta_RA), color="k", linestyle="--", alpha=0.3)
        circle=plt.Circle((np.mean(delta_DEC), np.mean(delta_RA)), np.std(delta_RA), edgecolor= 'red',facecolor='None', linewidth=2, alpha=1 ,ls = 'dashed') 
        plt.gca().add_patch(circle)
        ax.add_patch(circle)
        circle2=plt.Circle((np.mean(delta_DEC), np.mean(delta_RA)), 3*np.std(delta_RA), edgecolor= 'red',facecolor='None', linewidth=2, alpha=1 ,ls = 'dashed') 
        plt.gca().add_patch(circle2)
        ax.add_patch(circle2)
        print('mean in RA is',np.mean(delta_RA) )   
        print('mean in DEC is',np.mean(delta_DEC) )
        plt.xlabel(r'$\delta_{MeerAKT} - \delta_{FIRST}$',fontsize=17)
        plt.ylabel(r'$\alpha_{MeerAKT} - \alpha_{FIRST}$',fontsize=17)
        plt.title('FIRST',fontsize=20)
        plt.legend(fontsize=15)
        plt.tight_layout()
        plt.savefig(output_path+'FIRST_astrometry.pdf')
        plt.show()
        

def astrometry_VLASS(output_path,MeerKAT_NVSS_cat):


        MeerKAT_NVSS_cat_fits = fits.open(MeerKAT_NVSS_cat)
        MeerKAT_NVSS_cat=MeerKAT_NVSS_cat_fits[1].data
        corrective_offset=(0.0, 0.0)

        MeerKAT_coord=SkyCoord(MeerKAT_NVSS_cat['RA']*u.deg,MeerKAT_NVSS_cat['DEC']*u.deg, frame='fk5')


        NVSS_coord=SkyCoord(MeerKAT_NVSS_cat['RAJ2000']*u.deg,MeerKAT_NVSS_cat['DEJ2000']*u.deg, frame='fk5')
     
        #import IPython;IPython.embed()

        delta_RA= (MeerKAT_coord.ra.value - NVSS_coord.ra.value)*3600
        delta_DEC= (MeerKAT_coord.dec.value - NVSS_coord.dec.value)*3600
  
        sel21 = np.logical_and(MeerKAT_NVSS_cat["Total_flux"] / MeerKAT_NVSS_cat["Peak_flux"] < 100,
                       MeerKAT_NVSS_cat["Total_flux"] / MeerKAT_NVSS_cat["Peak_flux"] > 0)
        sel21 = np.logical_and(sel21,
                       MeerKAT_NVSS_cat[sel21]["Peak_flux"] > np.percentile(MeerKAT_NVSS_cat[sel21]["Peak_flux"], 5.0))

        fig, ax = plt.subplots(figsize=(11, 7))

        plt.scatter(delta_DEC[sel21],delta_RA[sel21], c="k", marker="o", alpha=0.3)
        plt.xlim(-4,4)
        plt.ylim(-4,4)
        plt.axvline(np.mean(delta_DEC),linestyle='dashed',color='black')
        plt.axhline(np.mean(delta_RA),linestyle='dashed',color='black')

        plt.axvline(np.mean(delta_DEC), color="k", linestyle="--", alpha=0.3,
            label="MeerKAT offset to NVSS $\Delta \\alpha , \Delta\delta$={0:.2f}\",{1:.2f}\"".format(np.mean(delta_RA),np.mean(delta_DEC)))
        
        plt.axhline(np.mean(delta_RA), color="k", linestyle="--", alpha=0.3)
        circle=plt.Circle((np.mean(delta_DEC), np.mean(delta_RA)), np.std(delta_RA), edgecolor= 'red',facecolor='None', linewidth=2, alpha=1 ,ls = 'dashed') 
        plt.gca().add_patch(circle)
        ax.add_patch(circle)
        circle2=plt.Circle((np.mean(delta_DEC), np.mean(delta_RA)), 3*np.std(delta_RA), edgecolor= 'red',facecolor='None', linewidth=2, alpha=1 ,ls = 'dashed') 
        plt.gca().add_patch(circle2)
        ax.add_patch(circle2)
        print('mean in RA is',np.mean(delta_RA) )   
        print('mean in DEC is',np.mean(delta_DEC) )
        plt.xlabel(r'$\delta_{MeerAKT} - \delta_{FIRST}$',fontsize=17)
        plt.ylabel(r'$\alpha_{MeerAKT} - \alpha_{FIRST}$',fontsize=17)
        plt.title('VLASS',fontsize=20)
        plt.legend(fontsize=15)
        plt.tight_layout()
        plt.savefig(output_path+'VLASS_astrometry.pdf')
        plt.show()


def flux_scale_FIRST(output_path,combined_MeerKAT_cat,flux_colname,Pflux_colname,e_flux_colname,survey,freq):
        
        MeerKAT_cat = fits.open(combined_MeerKAT_cat)[1].data
     
    
        mask=  np.where((MeerKAT_cat["Total_flux"] / MeerKAT_cat["Peak_flux"] > 0.8) & (MeerKAT_cat["Total_flux"] / MeerKAT_cat["Peak_flux"] < 1.2)   & ((MeerKAT_cat['E_Total_flux']/MeerKAT_cat['Total_flux']) < 0.1)& ((MeerKAT_cat[e_flux_colname]/MeerKAT_cat[flux_colname]) < 0.1))


        #mask2= np.where((ref_cat[flux_colname] / ref_cat[Pflux_colanme] > 0.7) & (ref_cat[flux_colname] / ref_cat[Pflux_colanme] < 1.5) & (ref_cat[Pflux_colanme] / 15e-6  > 100) & (ref_cat[Pflux_colanme] > np.percentile(ref_cat[Pflux_colanme], 5.0))& (ref_cat[flux_err_colname] / ref_cat[flux_colname] * 100 < 10))


        # MeerKAT_cat=MeerKAT_cat[mask]

        

        # max_sep=10

        
        # c1s=SkyCoord(MeerKAT_cat["RA"]*u.deg, MeerKAT_cat["DEC"]*u.deg, frame='fk5')
        # c2s=SkyCoord(ref_cat["RAJ2000"]*u.deg, ref_cat["DEJ2000"]*u.deg, frame='fk5')

        # list_flux=[]
        # list_flux_err=[]
        # for  i in range(len(MeerKAT_cat["Total_flux"])) :
        #     c1=c1s[i]
     
        #     tot_flux=0
        #     tot_err=0
        #     tot_flux_err=0

        #     for j in range(len(ref_cat[flux_colname])):
        #         c2=c2s[j]
        #         sep=c1.separation(c2)
        #         if (sep.value < max_sep/3600):
        #             tot_flux +=ref_cat[flux_colname][j]
        #             #print(VLASS_cat["Flux"][j])
        #             tot_err += ref_cat[flux_err_colname][j]**2
        #     list_flux.append(tot_flux)
        #     list_flux_err.append(np.sqrt(tot_err))

        

        # ref_flux=np.array(list_flux)
        # ref_flux_err=np.array(list_flux_err)

        # mask1=np.where( (ref_flux > 0) & (ref_flux_err > 0 ))

        # ref_flux=ref_flux[mask1]

        # ref_flux_err=ref_flux_err[mask1]

        

        MeerKAT_flux=MeerKAT_cat["Total_flux"][mask]*10**3
        MeerKAT_flux_err=MeerKAT_cat["E_Total_flux"][mask]*10**3

        ref_flux = MeerKAT_cat[flux_colname][mask]
        ref_flux_err = MeerKAT_cat[e_flux_colname][mask]
        #import IPython;IPython.embed()
        

        def linear_function(x, m, b):
            return m * x + b
        
        
        params, covariance = curve_fit(linear_function,  np.log10(MeerKAT_flux), np.log10(ref_flux))

        
        from scipy import stats

        slope, intercept = params

        slope, intercept,r_value, p_value, std_err = stats.linregress(np.log10(MeerKAT_flux* (freq / 1.283e9)**-0.7), np.log10(ref_flux))

        print('r value is',r_value)


        err=((MeerKAT_flux* (freq / 1.283e9)**-0.7 - ref_flux)/ref_flux )*100

        print('Flux calibration error', err.mean())

        fig = plt.figure(figsize=(15, 7))
        
        xx = np.linspace(0.1,10000,1024)
        plt.plot(xx,xx, "k--")

        plt.plot(xx,linear_function(xx, slope, intercept))
        #plt.scatter(MeerKAT_flux* (freq / 1.283e9)**-0.7,ref_flux)
        plt.errorbar(MeerKAT_flux* (freq / 1.283e9)**-0.7,ref_flux ,
                    yerr=abs(MeerKAT_flux_err),
                    xerr=abs(MeerKAT_flux_err* (freq / 1.283e9)**-0.7),
                    capsize=3, linewidth=0, elinewidth=1,
                    color="k")
        plt.xlabel(r'MeerKAT $S_{int}$ mJy',fontsize=17)
        plt.ylabel(r'VLASS $S_{int}$ mJy',fontsize=17)
        plt.xlabel('MeerKAT flux in mJy',fontsize=17)
        plt.ylabel(survey + ' flux in mJy',fontsize=17)
        plt.xscale('log')
        plt.yscale('log')
        # plt.xlim(0,100)
        # plt.ylim(0,100)
        axtop = plt.axes([0.125, 0.85, 0.78, 0.15])
        axtop.hist(MeerKAT_flux* (freq / 1.283e9)**-0.7, bins=20, range=(0,50),color='lightblue', alpha=0.7, orientation='vertical',histtype='step',linewidth=2)
        axtop.axvline(np.median(MeerKAT_flux),linestyle='dashed',color='black')

        # Create the y-axis histogram on the right
        axright = plt.axes([0.85, 0.11, 0.15, 0.75])
        axright.hist(ref_flux , bins=20,range=(0,50), color='lightblue', alpha=0.7, orientation='horizontal',histtype='step',linewidth=2)
        axright.axhline(np.median(ref_flux  ),linestyle='dashed',color='black')

        axtop.set_xticks([])
        axtop.set_yticks([])
        axright.set_xticks([])
        axright.set_yticks([])

        plt.savefig(output_path+survey+'_flux_scale.pdf')
        plt.show()


def flux_scale_VLASS(output_path,combined_MeerKAT_cat,flux_colname,Pflux_colname,e_flux_colname,survey,freq):
        
        MeerKAT_cat = fits.open(combined_MeerKAT_cat)[1].data
     
    
        mask=  np.where((MeerKAT_cat["Total_flux"] / MeerKAT_cat["Peak_flux"] > 0.9) & (MeerKAT_cat["Total_flux"] / MeerKAT_cat["Peak_flux"] < 1.1)   & ((MeerKAT_cat['E_Total_flux']/MeerKAT_cat['Total_flux']) < 0.1)& ((MeerKAT_cat[e_flux_colname]/MeerKAT_cat[flux_colname]) < 0.1))

        #import IPython;IPython.embed()
        #mask2= np.where((ref_cat[flux_colname] / ref_cat[Pflux_colanme] > 0.7) & (ref_cat[flux_colname] / ref_cat[Pflux_colanme] < 1.5) & (ref_cat[Pflux_colanme] / 15e-6  > 100) & (ref_cat[Pflux_colanme] > np.percentile(ref_cat[Pflux_colanme], 5.0))& (ref_cat[flux_err_colname] / ref_cat[flux_colname] * 100 < 10))


        # MeerKAT_cat=MeerKAT_cat[mask]

        # ref_cat=ref_cat[mask2]

        # max_sep=20

        
        # c1s=SkyCoord(MeerKAT_cat["RA"]*u.deg, MeerKAT_cat["DEC"]*u.deg, frame='fk5')
        # c2s=SkyCoord(ref_cat["RAJ2000"]*u.deg, ref_cat["DEJ2000"]*u.deg, frame='fk5')

        # list_flux=[]
        # list_flux_err=[]
        # for  i in range(len(MeerKAT_cat["Total_flux"])) :
        #     c1=c1s[i]
     
        #     tot_flux=0
        #     tot_err=0
        #     tot_flux_err=0

        #     for j in range(len(ref_cat[flux_colname])):
        #         c2=c2s[j]
        #         sep=c1.separation(c2)
        #         if (sep.value < max_sep/3600):
        #             tot_flux +=ref_cat[flux_colname][j]
        #             #print(VLASS_cat["Flux"][j])
        #             tot_err += ref_cat[flux_err_colname][j]**2
        #     list_flux.append(tot_flux)
        #     list_flux_err.append(np.sqrt(tot_err))

        

        # ref_flux=np.array(list_flux)
        # ref_flux_err=np.array(list_flux_err)

        # mask1=np.where( (ref_flux > 0) & (ref_flux_err > 0 ))

        # ref_flux=ref_flux[mask1]

        # ref_flux_err=ref_flux_err[mask1]

        

        MeerKAT_flux=MeerKAT_cat["Total_flux"][mask]*10**3
        MeerKAT_flux_err=MeerKAT_cat["E_Total_flux"][mask]*10**3

        ref_flux = MeerKAT_cat[flux_colname][mask]*10**3
        ref_flux_err = MeerKAT_cat[e_flux_colname][mask]*10**3
        
        

        def linear_function(x, m, b):
            return m * x + b
        
        
        params, covariance = curve_fit(linear_function,  np.log10(MeerKAT_flux* (freq / 1.283e9)**-0.7), np.log10(ref_flux))
        #import IPython;IPython.embed()
        
        from scipy import stats

        slope, intercept = params

        slope, intercept,r_value, p_value, std_err = stats.linregress(np.log10(MeerKAT_flux* (freq / 1.283e9)**-0.7), np.log10(ref_flux))

        print('r value is',r_value)


        err=((MeerKAT_flux* (freq / 1.283e9)**-0.7 - ref_flux)/ref_flux )*100

        print('Flux calibration error', err.mean())

        fig = plt.figure(figsize=(15, 7))
        
        xx = np.linspace(0.1,10000,1024)
        plt.plot(xx,xx, "k--")

        plt.plot(xx,linear_function(xx, slope, intercept))
        #plt.scatter(MeerKAT_flux* (freq / 1.283e9)**-0.7,ref_flux)
        plt.errorbar(MeerKAT_flux* (freq / 1.283e9)**-0.7,ref_flux ,
                    yerr=abs(MeerKAT_flux_err),
                    xerr=abs(MeerKAT_flux_err* (freq / 1.283e9)**-0.7),
                    capsize=3, linewidth=0, elinewidth=1,
                    color="k")
        plt.xlabel(r'MeerKAT $S_{int}$ mJy',fontsize=17)
        plt.ylabel(r'VLASS $S_{int}$ mJy',fontsize=17)
        plt.xlabel('MeerKAT flux in mJy',fontsize=17)
        plt.ylabel(survey + ' flux in mJy',fontsize=17)
        plt.xscale('log')
        plt.yscale('log')
        # plt.xlim(0,100)
        # plt.ylim(0,100)
        axtop = plt.axes([0.125, 0.85, 0.78, 0.15])
        axtop.hist(MeerKAT_flux* (freq / 1.283e9)**-0.7, bins=20, range=(0,50),color='lightblue', alpha=0.7, orientation='vertical',histtype='step',linewidth=2)
        axtop.axvline(np.median(MeerKAT_flux),linestyle='dashed',color='black')

        # Create the y-axis histogram on the right
        axright = plt.axes([0.85, 0.11, 0.15, 0.75])
        axright.hist(ref_flux , bins=20,range=(0,50), color='lightblue', alpha=0.7, orientation='horizontal',histtype='step',linewidth=2)
        axright.axhline(np.median(ref_flux  ),linestyle='dashed',color='black')

        axtop.set_xticks([])
        axtop.set_yticks([])
        axright.set_xticks([])
        axright.set_yticks([])

        plt.savefig(output_path+survey+'_flux_scale.pdf')
        plt.show()


def flux_scale_NVSS(output_path,combined_MeerKAT_cat,flux_colname,Pflux_colname,e_flux_colname,survey,freq):
        
        MeerKAT_cat = fits.open(combined_MeerKAT_cat)[1].data
     
    
        mask=  np.where((MeerKAT_cat["Total_flux"] / MeerKAT_cat["Peak_flux"] > 0.8) & (MeerKAT_cat["Total_flux"] / MeerKAT_cat["Peak_flux"] < 1.2) & (MeerKAT_cat["Total_flux"]  > 0.01) & (MeerKAT_cat["S1.4"] > 0.01))#  & (MeerKAT_cat[flux_colname] / MeerKAT_cat[Pflux_colname] > 0.7) & (MeerKAT_cat[flux_colname] / MeerKAT_cat[Pflux_colname] < 1.5)) #&(MeerKAT_cat[flux_colname] / 15e-6  > 50) &(MeerKAT_cat[Pflux_colname] / 20e-6  > 50) & (MeerKAT_cat["E_Total_Flux"] / MeerKAT_cat["Total_Flux"] * 100 < 10)& (MeerKAT_cat["e_Flux"] / MeerKAT_cat["Flux"] * 100 < 10))


        #mask2= np.where((ref_cat[flux_colname] / ref_cat[Pflux_colanme] > 0.7) & (ref_cat[flux_colname] / ref_cat[Pflux_colanme] < 1.5) & (ref_cat[Pflux_colanme] / 15e-6  > 100) & (ref_cat[Pflux_colanme] > np.percentile(ref_cat[Pflux_colanme], 5.0))& (ref_cat[flux_err_colname] / ref_cat[flux_colname] * 100 < 10))


        # MeerKAT_cat=MeerKAT_cat[mask]

        # ref_cat=ref_cat[mask2]

        # max_sep=20

        
        # c1s=SkyCoord(MeerKAT_cat["RA"]*u.deg, MeerKAT_cat["DEC"]*u.deg, frame='fk5')
        # c2s=SkyCoord(ref_cat["RAJ2000"]*u.deg, ref_cat["DEJ2000"]*u.deg, frame='fk5')

        # list_flux=[]
        # list_flux_err=[]
        # for  i in range(len(MeerKAT_cat["Total_flux"])) :
        #     c1=c1s[i]
     
        #     tot_flux=0
        #     tot_err=0
        #     tot_flux_err=0

        #     for j in range(len(ref_cat[flux_colname])):
        #         c2=c2s[j]
        #         sep=c1.separation(c2)
        #         if (sep.value < max_sep/3600):
        #             tot_flux +=ref_cat[flux_colname][j]
        #             #print(VLASS_cat["Flux"][j])
        #             tot_err += ref_cat[flux_err_colname][j]**2
        #     list_flux.append(tot_flux)
        #     list_flux_err.append(np.sqrt(tot_err))

        

        # ref_flux=np.array(list_flux)
        # ref_flux_err=np.array(list_flux_err)

        # mask1=np.where( (ref_flux > 0) & (ref_flux_err > 0 ))

        # ref_flux=ref_flux[mask1]

        # ref_flux_err=ref_flux_err[mask1]

        

        MeerKAT_flux=MeerKAT_cat["Total_flux"][mask]*10**3
        MeerKAT_flux_err=MeerKAT_cat["E_Total_flux"][mask]*10**3

        ref_flux = MeerKAT_cat[flux_colname][mask]
        ref_flux_err = MeerKAT_cat[e_flux_colname][mask]
     
        

        def linear_function(x, m, b):
            return m * x + b
        
        
        params, covariance = curve_fit(linear_function,  MeerKAT_flux, ref_flux)

        
        from scipy import stats

        slope, intercept = params

        slope, intercept,r_value, p_value, std_err = stats.linregress(np.log10(MeerKAT_flux* (freq / 1.283e9)**-0.7), np.log10(ref_flux))

        print('r value is',r_value)


        err=((MeerKAT_flux* (freq / 1.283e9)**-0.7 - ref_flux)/ref_flux )*100

        print('Flux calibration error', err.mean())

        fig = plt.figure(figsize=(15, 7))
        
        xx = np.linspace(1,1000,1024)
        plt.plot(xx,xx, "k--")

        plt.plot(xx[4:],linear_function(xx[4:], slope, intercept))
        #plt.scatter(MeerKAT_flux* (freq / 1.283e9)**-0.7,ref_flux)
        plt.errorbar(MeerKAT_flux* (freq / 1.283e9)**-0.7,ref_flux ,
                    yerr=abs(MeerKAT_flux_err),
                    xerr=abs(MeerKAT_flux_err* (freq / 1.283e9)**-0.7),
                    capsize=3, linewidth=0, elinewidth=1,
                    color="k")
        plt.xlabel(r'MeerKAT $S_{int}$ mJy',fontsize=17)
        plt.ylabel(r'VLASS $S_{int}$ mJy',fontsize=17)
        plt.xlabel('MeerKAT flux in mJy',fontsize=17)
        plt.ylabel(survey + ' flux in mJy',fontsize=17)
        plt.xscale('log')
        plt.yscale('log')
        # plt.xlim(0,100)
        # plt.ylim(0,100)
        axtop = plt.axes([0.125, 0.85, 0.78, 0.15])
        axtop.hist(MeerKAT_flux* (freq / 1.283e9)**-0.7, bins=20, range=(0,50),color='lightblue', alpha=0.7, orientation='vertical',histtype='step',linewidth=2)
        axtop.axvline(np.median(MeerKAT_flux),linestyle='dashed',color='black')

        # Create the y-axis histogram on the right
        axright = plt.axes([0.85, 0.11, 0.15, 0.75])
        axright.hist(ref_flux , bins=20,range=(0,50), color='lightblue', alpha=0.7, orientation='horizontal',histtype='step',linewidth=2)
        axright.axhline(np.median(ref_flux  ),linestyle='dashed',color='black')

        axtop.set_xticks([])
        axtop.set_yticks([])
        axright.set_xticks([])
        axright.set_yticks([])

        plt.savefig(output_path+survey+'_flux_scale.pdf')
        plt.show()
        
        
def simulation(cluster_name,simulation_path,radio_catalogue_fits,fits_image,res_image,rms_image):


    cat=Table.read(radio_catalogue_fits)

    res_data=fits.open(res_image)[0].data

    
    print(np.shape(res_data))

    header=fits.getheader(fits_image)
    del header['HISTORY']


    def gaussian1(xx,yy,xc,yc,re,S):
        I=rr=np.zeros([xx,yy])
        for m in range(xx):
            for n in range(yy):
                I[n,m]=  S*np.exp(-((m-xc)/re1)**2 - ((n-yc)/re2)**2)
        return(I) 

    #numbers=1000;xx=6000;yy=6000;radii=5;flux=10;Data=0


    a0=1.655
    a1=-0.1150
    a2=0.2272
    a3=0.51788
    a4=-0.449661
    a5=0.160265
    a6=-0.028541
    a7=0.002041
    

    def source_count_flux(S,a0,a1,a2,a3,a4,a5,a6,a7):
        a = [a0,a1, a2, a3, a4, a5, a6, a7]
        #return(a0*(np.log10(S))**a0 + a1*(np.log10(S))**a1+a2*(np.log10(S))**a2+a3*(np.log10(S))**a3+a4*(np.log10(S))**a4+a5*(np.log10(S))**a5+a6*(np.log10(S))**a6+a7*(np.log10(S))**a7)
        return(sum(ai * (np.log10(S))**i for i,ai in enumerate(a)))
    
        
    flux_min=cat['Total_flux'].min()

    flux_max=cat['Total_flux'].max()

    
    S=np.random.randint(flux_min*10**6,flux_max*10**6,size=len(cat['Total_flux']))
    #flux_dist=np.random.choice(S,p=source_count_flux(S,a0,a1,a2,a3,a4,a5,a6,a7)/np.sum(source_count_flux(S,a0,a1,a2,a3,a4,a5,a6,a7)))


    number_sources=len(cat['Total_flux'])

    xx=header['NAXIS1']
    yy=header['NAXIS2']


    def gaussian(xx,yy,xc,yc,re1,re2,S):
        
        x = np.arange(xx, dtype=np.float64)[:, None]
        y = np.arange(yy, dtype=np.float64)[None, :]
        x -= xc
        y -= yc
        x /= re1
        y /= re2
        x **= 2
        y **= 2
        x *= -1. #-((n-xc)/re1)**2
        y *= -1. #-((n-yc)/re2)**2
        x_exp = np.exp(x, out=x)
        y_exp = np.exp(y, out=y)
        return S * x_exp * y_exp

   
    for j in range(5):

        Data=0
        res_data=fits.open(res_image)[0].data
        res_data=res_data[0,0,:,:]
        Data=res_data

        for i in range(number_sources):
            xc=np.random.randint(1,xx)
            yc=np.random.randint(1,yy)
            re1=np.random.randint(header['BMAJ']*3600,2*header['BMAJ']*3600) #Bmaj
            re2=np.random.randint(header['BMIN']*3600,2*header['BMIN']*3600)  #Bmin
            flux_dist=np.random.choice(S,p=source_count_flux(S,a0,a1,a2,a3,a4,a5,a6,a7)/np.sum(source_count_flux(S,a0,a1,a2,a3,a4,a5,a6,a7)))
            Data+=gaussian(xx,yy,xc,yc,re1,re2,S=flux_dist/10**6)

        fits_image=simulation_path+cluster_name+'_simulated_image_'+str(j)+'.fits'
        fits.writeto(fits_image,data=Data,header=header,overwrite=True)
        print(fits_image+ ' ' +'written')


    S=np.logspace(-1,4,1000)
    
    plt.xscale('log')
    plt.yscale('log')
    plt.ylabel('dN /dS')
    plt.xlabel('Log S')
    #plt.plot(S,S**(5/2)*simple_powerlaw())
    plt.plot(S,10**source_count_flux(S,a0,a1,a2,a3,a4,a5,a6,a7))
    #plt.plot(S,simple_powerlaw(S))
    plt.show()



def simulation_catalog(simulation_path):
    
   
    images=glob.glob(simulation_path + '*.fits' )

    for image in images:

        img = bdsf.process_image(image, rms_box=(40,40),rms_box_bright=(15,15),adaptive_thresh=150,thresh_isl=4.0,thresh_pix=5.0,
                    detection_image=image,interactive=False ,clobber=True,spectralindex_do = False)#,atrous_do = True)
        

        img.write_catalog(outfile=image[:-5]+'_srl.fits',format='fits', catalog_type='srl',clobber=True)
        print(image[:-5]+'_srl.fits' + ' catalog written')


def completness(simulation_path,radio_catalogue_fits):

    sim_catalogs=glob.glob(simulation_path+'*_srl.fits')

    real_cat=Table.read(radio_catalogue_fits)

    flux_real=real_cat['Total_flux']

    min_flux=flux_real.min()
    max_flux=flux_real.max()

   
    intervals=np.logspace(-6,5,500)

    #intervals_sparce=np.logspace(-6,5,20)


    fig, ax = plt.subplots(1, 1, figsize=(6,6))

    for sim_cat in sim_catalogs:
        frac = []
        print(sim_cat)
        for int in range(len(intervals)-1):
            cat=Table.read(sim_cat)

            try:
                mask_real = (intervals[int] < real_cat['Total_flux']) & (real_cat['Total_flux'] < intervals[int+1])
                mask = (intervals[int] < (cat['Total_flux'])) & ((cat['Total_flux']) < intervals[int+1])
                frac.append(np.sum(mask)/np.sum(mask_real))
                print(frac)
                
            except FloatingPointError:
                #print('interval is ',intervals[int],intervals[int+1])
                frac.append(np.nan)

            #print('mask and real counts',np.sum(mask),np.sum(mask_real))
        
        
        plt.plot(((intervals[:-1]+intervals[1:])/2), np.nancumsum(frac)/np.nancumsum(frac).max(), label=sim_cat)

#        np.median(intervals[:-1]+intervals[1:])/2
        
        plt.scatter(((intervals[:-1]+intervals[1:])/2), np.nancumsum(frac)/np.nancumsum(frac).max())
        plt.xscale('log')
        plt.xlim(10**-2,10**2)
        ax.set_ylabel('Fraction',fontsize=15)
        ax.set_xlabel('Flux density [mJy]',fontsize=15)
        ax.legend()
        
 
    plt.show()

def angular_distribution(simulation_path,radio_catalogue_fits,fits_image,unresolved_mask,resolved_mask):


    rms=(15e-6)

    cat=Table.read(radio_catalogue_fits)

    resolved_cat=cat[resolved_mask]

    unresolved_cat=cat[unresolved_mask]


    mask=resolved_cat['Total_flux']>(5*rms)

    unresolved_cat=resolved_cat[mask]

    flux=resolved_cat['Total_flux']

    flux_unresolved=unresolved_cat['Total_flux']

 

    peak=resolved_cat['Peak_flux']

    size1=resolved_cat['Maj']*3600

    size2=resolved_cat['Min']*3600

    header=fits.getheader(fits_image)

    bmaj=header['BMAJ']*3600
    bmin=header['BMIN']*3600



    A=1;B=1

    sizes_resolved = np.sqrt(size1 * size2)

    sizes_unresolved = np.zeros(len(unresolved_cat['Total_flux']))
    

    theta_N=np.sqrt(bmaj*bmin)

    x=peak/rms
    
    flux_linspace=np.linspace(flux.min(),flux.max(),1000)

    rms_linspace=np.linspace(x.min(),x.max(),1000)

    theta_max=theta_N*np.sqrt((flux_linspace/(5*rms)) -1)

    
    theta_min=theta_N*np.sqrt(A*(1+B/(rms_linspace))-1)

    num_bins = 10

    # Calculate the bin edges based on the x data range
    bins = np.linspace(flux.min(), flux.max(), num_bins + 1)


    bins_mid = 0.5* (bins[1:] + bins[:-1])

    
    median_size=sizes_resolved[np.where(bins_mid)]


    plt.plot(bins_mid*10**3, median_size, color='red', marker='x', label='Median flux ratio')
    
    #plt.plot( bin_edges,bin_medians,color='purple',marker='D')
    #import IPython;IPython.embed()
    plt.plot(flux_linspace*10**3,theta_max,color='orange')
    plt.plot(rms_linspace*10**3,theta_min,'--',color='orange')
    plt.scatter(flux*10**3,sizes_resolved,alpha=0.7,s=10)
    plt.scatter(flux_unresolved*10**3,sizes_unresolved,alpha=0.7,s=10)
    #plt.scatter(resolved*10**3,sizes)
    plt.axhline(y=8, color='black',linewidth=2)
    plt.xscale('log')
    plt.ylim(-10,80)
    #plt.yscale('log')
    plt.show()



def source_counts(radio_catalogue_fits,COSMOS_catalogue_fits,Super_CLASS_source_counts,Super_CLASS_catalogue_fits,output_path,cluster_name):



    def fixed_source_perbin(flux,number_bins,survey_area,counts_freq,data_freq,Spectral_Index):
         
        flux = flux * (counts_freq / data_freq) ** Spectral_Index
        number_sources=len(flux)

        print('total number of sources',number_sources)

        number_per_bin= np.int32(np.ceil(number_sources/number_bins))

        counts=np.zeros(number_bins)

        counts_err=np.zeros(number_bins)

        left_bin_array=np.zeros(number_bins)

        right_bin_array=np.zeros(number_bins)

        bin_centre_array=np.zeros(number_bins)


        for i in range(number_bins):
            Name_Bin_File    = 'Bins_PYTHON.txt'
            sources=flux[number_per_bin*i:np.min([number_per_bin*(i+1),len(flux)])]

            sources=np.min([len(flux)-number_per_bin,number_per_bin*(i+1)])
            # mean_flux=np.mean(sources)
            
            right_bin=flux[sources]

            left_bin=(flux[number_per_bin*(i)])
        
            bin_width = right_bin-left_bin

            subset=(flux >= left_bin) & (flux < right_bin)

            mean_flux=np.mean(flux[subset])

            source_tot0=np.sum(subset)

            source_tot0_err=np.sqrt(np.sum(subset))

            source_tot1=source_tot0/bin_width
        
            source_tot2=source_tot1/((survey_area)*(np.pi/180)**2)

            source_norm=source_tot2/mean_flux**(-2.5)

            source_tot1_err=source_tot0_err/bin_width
        
            source_tot2_err=source_tot1_err/((survey_area)*(np.pi/180)**2)

            source_norm_err=source_tot2_err/mean_flux**(-2.5)

            left_bin_array[i]=left_bin

            right_bin_array[i]=right_bin

            bin_centre_array[i]=mean_flux

            counts[i]=source_norm

            counts_err[i]=source_norm_err
        
       
        Bin_Data = np.column_stack([left_bin_array, right_bin_array, bin_centre_array])
        
        with open(Name_Bin_File, 'w') as Bins:
            Bins.write('#Left_Edge\t\tRight_Edge\t\tCentre\n')
            np.savetxt(Bins, Bin_Data)
        
    
        return(bin_centre_array,counts,counts_err)
        
        
    def equidistant_bindwidth(flux,number_bins,survey_area,counts_freq,data_freq, Spectral_Index):

        flux = flux * (counts_freq / data_freq) ** Spectral_Index

        flux_min=np.min(flux)

        flux_max=np.max(flux)


        Range_x    = np.linspace(start=np.log10(flux_min), stop=np.log10(flux_max), num=2*number_bins+1)

        left_bin  = 10 ** Range_x[0:-1:2]
        bin_centre  = 10 ** Range_x[1::2]
        right_bin   = 10 ** Range_x[2::2]

        
        counts=np.zeros(len(left_bin))
        counts_err=np.zeros(len(left_bin))
        
        Name_Bin_File    = 'fixed_Bins_PYTHON.txt'


        for i in range(len(left_bin)):
            try:
                #mean_flux=np.mean(flux[mask])
               
                subset = flux[flux >= left_bin[i]]
                
                subset = subset[subset < right_bin[i]]

                source_tot0=len(subset)

                print(left_bin[i],bin_centre[i],right_bin[i],source_tot0)

                source_tot0_err=np.sqrt(source_tot0)

                mean_flux=np.mean(subset)

                source_tot1=source_tot0/ (right_bin[i]- left_bin[i])

                source_tot1_err=source_tot0_err/ (right_bin[i]- left_bin[i])

                source_tot2=source_tot1/ ((survey_area)*(np.pi/180)**2)

                source_tot2_err=source_tot1_err/((survey_area)*(np.pi/180)**2)

                source_norm=source_tot2*bin_centre[i]**(2.5)

                source_norm_err=source_tot2_err*bin_centre[i]**(2.5)
                
                counts[i]=source_norm

                counts_err[i]=source_norm_err
           
                
            except FloatingPointError:
                #print('interval is ',intervals[int],intervals[int+1])
                counts[i]=0#np.nan
                counts_err[i]=0
            
            Bin_Data = np.column_stack([left_bin, right_bin, bin_centre])

            with open(Name_Bin_File, 'w') as Bins:
                Bins.write('#Left_Edge\t\tRight_Edge\t\tCentre\n')
                np.savetxt(Bins, Bin_Data)

        return(bin_centre,counts,counts_err)
        

    COSMOS_cat=Table.read(COSMOS_catalogue_fits)

    SC_cat=Table.read(Super_CLASS_source_counts)

    SC_catalogue=Table.read(Super_CLASS_catalogue_fits)

    RA=np.array(SC_catalogue['RAh'])*15 + np.array(SC_catalogue['RAm'])*15/60 + np.array(SC_catalogue['RAs']) *15/3600
    DEC=np.array(SC_catalogue['DEd'])+np.array(SC_catalogue['DEm'])/60+ np.array(SC_catalogue['DEs'])/3600
    SC_catalogue['Ra']=RA
    SC_catalogue['Dec']=DEC

    SC_catalogue.write('SCS_cat.fits', format='fits', overwrite=True)




    real_cat=Table.read(radio_catalogue_fits)

    cluster_centre=SkyCoord(str(150), str(2.3), frame='icrs',unit=(u.deg,u.deg))


    def mask_region(ra,dec,radius):
    
        centroid_ra = np.mean(ra)
        centroid_dec = np.mean(dec)
        
        mask=np.sqrt((ra-centroid_ra)**2+(dec- centroid_dec)**2) <=radius

        area=radius**2*np.pi

        return(mask,area)
        

    cluster_centre=SkyCoord(str(150), str(2.3), frame='icrs',unit=(u.deg,u.deg))
    mask_COSMOS_wall=np.sqrt((COSMOS_cat['ra']-cluster_centre.ra.value)**2+(COSMOS_cat['dec']- cluster_centre.dec.value)**2) <=0.3
    COSMOS_wall_cat=COSMOS_cat[mask_COSMOS_wall]

   
    fig, ax = plt.subplots(1, 1, figsize=(9,7))
    

    radius=1

    mask_COSMOS,area=mask_region(COSMOS_cat['ra'],COSMOS_cat['dec'],radius=radius)
    mask_MeerKAT,area = mask_region(real_cat['DEC'],real_cat['DEC'],radius=radius)
    mask_SCS,area=mask_region(RA,DEC,radius=radius)

    COSMOS_cat=COSMOS_cat[mask_COSMOS]
    real_cat=real_cat[mask_MeerKAT]
    SCS_cat=SC_catalogue[mask_SCS]

    MeerKAT_flux=np.sort(real_cat['Total_flux'])

    SCS_cat_flux=np.sort(SCS_cat['Si'])*10**-3

    COSMOS_flux=np.sort(COSMOS_cat['flux'])*10**-6

   

    bins_COSMOS,counts_COSMOS,counts_COSMOS_err=equidistant_bindwidth(flux=COSMOS_flux,number_bins=20,survey_area=area,data_freq=3,counts_freq=1.4, Spectral_Index=-0.7)

    bins_SCS,counts_SCS,counts_SCS_err=equidistant_bindwidth(flux=SCS_cat_flux,number_bins=20,survey_area=area,data_freq=0.325,counts_freq=1.4, Spectral_Index=-0.7)

    #bins_COSMOS_wall,counts_COSMOS_wall,counts_COSMOS_wall_err=equidistant_bindwidth(flux=COSMOS_wall_flux,number_bins=50,survey_area=area,data_freq=3,counts_freq=1.4, Spectral_Index=-0.7)

    bins_M,counts_M,counts_M_err=equidistant_bindwidth(flux=MeerKAT_flux,number_bins=20,survey_area=area,data_freq=1.28,counts_freq=1.4, Spectral_Index=-0.7)



    # plt.scatter(bins_M, counts_M,color='green',label=f'MeerKAT equal bin width of radius = '+str(radius),marker='o')
    # plt.scatter(bins_COSMOS, counts_COSMOS,color='blue',label=' COSMOS equal bin width of radius = '+str(radius),marker='o')
    # plt.scatter( SC_cat['flux']*10**-3,SC_cat['Source_counts'],color='orange',label=' Super-CLASS equal bin width',marker='o')

    
    plt.errorbar(bins_M, counts_M,yerr=counts_M_err,color='orange',label=f'MeerKAT equal bin width of radius = '+str(radius),fmt='o')

    plt.errorbar(bins_COSMOS, counts_COSMOS,yerr=counts_COSMOS_err,color='blue',label=' COSMOS equal bin width of radius = '+str(radius),fmt='o')

    #plt.errorbar(bins_SCS, counts_SCS,yerr=counts_SCS_err,color='green',label=' SCS equal bin width of radius = '+str(radius),fmt='o')
   
    plt.errorbar( SC_cat['flux']*10**-3,SC_cat['Source_counts'],yerr=SC_cat['error'],color='green',label=' Super-CLASS equal bin width',fmt='x')

    
    import pandas as pd
    file_path='Counts_COSMOS.txt'
    COSMOS_real = pd.read_csv(file_path, delimiter='\t')
  
    # plt.errorbar(x=bins_M_fix, y=counts_M_fix,yerr=counts_M_fix_err,color='orange',label='MeerKAT equal sources per bin',marker='x')
   
    #plt.scatter(S_TLA, N_TLA,marker='x',label='325 MHz GMRT Super-CLASS field')
    ax.set_xscale("log")#, nonposx='clip')
    ax.set_yscale("log")
    plt.ylim(10**-3,10**3)
    plt.xlim(10**-5,10**-1)
    ax.set_ylabel(r'$S^{2.5}\; dN/dS [Jy^{-1} \, sr^{-1} ]$',fontsize=15)
    ax.set_xlabel('Flux density [Jy]',fontsize=15)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path+cluster_name+'_source_counts.pdf')
    plt.show()

    
    
    