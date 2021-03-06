"""
cxilt14py
- Analysis scripts for performing angular correlation analysis on the cspad detector @ CXI @ LCLS

angularCorrelation.py - simple script to calculate angular correlations and check convergence

September 2018

authors: Andrew Martin (andrew.martin@rmit.edu.au)
         

"""


import numpy as np
import analysisTools as at


#
# set up parsing of command line arguments
#
atp = at.params.parameters()

# add another command line argument
atp.parser.add_argument( "--outputext", help="File extention for output image: .dbin or .h5", default="dbin")

atp.parser.add_argument( "--raw", help="output uncorrected data (true) or all corrections [dark/gain/common mode]", type=bool, default=False)

atp.parser.add_argument( "--normalize", help="normalize the data by the average pixels intensity", type=bool, default=False)
atp.parser.add_argument( "--intensity_veto", help="skip frames with intensity lower than minI", type=bool, default=False)
atp.parser.add_argument( "--diffCorr", help="Calculate the correlation of intenisty difference between current frame and a random frame.", type=bool, default=False)
atp.parser.add_argument( "--randomXcorr", help="Calculate the correlation between current frame and a random frame.", type=bool, default=False)

atp.parser.add_argument( "--pcrange", nargs=4, help="pixel range to evaluate the similarity (pearson correlation) of odd/even frame angular correlation functions ", type=int)

atp.parser.add_argument( "--polarRange", nargs=4, help="pixel range to evaluate polar plots of assembled images ", type=float)
atp.parser.add_argument( "--nq", help="number of radial (q) polar bins ", type=int)
atp.parser.add_argument( "--nth", help="number of angular polar bins ", type=int)
atp.parser.add_argument( "--minI", help="minimum total integrated intensity ", type=float, default=1e5)

atp.parser.add_argument( "--svdfile", help="a h5 file with mode information." )
atp.parser.add_argument( "--svdnsub", help="number of modes to subtract (project out). Default value 0", type=int, default=0)
atp.parser.add_argument( "--rankmax", help="maximum rank of svd calculation", type=int, default=20 )


#atp.parser.add_argument( "--cenx", help="beam centre in pixels from middle of assembled array : xcoord ", type=int)
#atp.parser.add_argument( "--ceny", help="beam centre in pixels from middle of assembled array : ycoord ", type=int)


# parse the command line arguments
atp.parse_arguments()
print "raw", atp.args.raw
print "diffCorr", atp.args.diffCorr
print "normalize", atp.args.normalize
print "intensity_veto", atp.args.intensity_veto
# write all the input arguments to a log file
atp.write_all_params_to_file( script=atp.parser.prog )


#
# Set up the psana variables from psana wrapper
#
print atp.args.exp, atp.args.run
psbb = at.psanaWrapper.psanaBlackBox( exp=atp.args.exp, run=atp.args.run )
nmax = len(psbb.times)
if atp.args.nframes > nmax:
    atp.args.nframes = nmax - ato.args.nstart -1
print "nmax, atp.args.nframes =", nmax, atp.args.nframes



# angular correlation struct
ac = at.correlation.angular_correlation()

# copy some parameters for polar plot
nq, nth = atp.args.nq, atp.args.nth
qmin, qmax, thmin, thmax = atp.args.polarRange[0], atp.args.polarRange[1], atp.args.polarRange[2], atp.args.polarRange[3]
cenx, ceny = atp.args.cenx, atp.args.ceny

# read svd information if required
if atp.args.svdnsub > 0:
    svdt = at.svdOnTheFly.SVDthin( atp.args.rankmax)
    svdt.h5read_svdmodes( atp.args.svdfile, (nq,nth) )

#
# retrieve mask and calculate its angular correlation
#
mask = psbb.cspad.mask( psbb.run.event( psbb.times[0]), calib=True, status=True, edges=True, central=True, unbondnbrs8=True)
#assembled image of mask
imgmsk =  psbb.cspad.image(psbb.evt,mask)
ione = np.where( imgmsk < 1.0 )
imgmsk[ione] = 0.0
# polar plot of mask
pplot_mask = ac.polar_plot( imgmsk, nq, nth, qmin, qmax, thmin, thmax, cenx+imgmsk.shape[0]/2, ceny+imgmsk.shape[1]/2, submean=True )
ineg = np.where( pplot_mask < 0.0 )
pplot_mask[ineg] = 0.0
pplot_maskones = pplot_mask*0.0 + 1.0
pplot_maskones[ineg] = 0.0
#angular correlation of mask
corrqq_mask = ac.polarplot_angular_correlation( pplot_mask )


#
# sum nframes of data from a run
#
s = psbb.cspad.calib( psbb.evt ).shape
datasum =  np.zeros( (s[0], s[1], s[2], 2 ))
pplotsum = np.zeros( (nq,nth,2) )
pplot_mean_sum = np.zeros( (nq,nth,2) )
pplotsvdsub = np.zeros( (nq,nth,atp.args.svdnsub,2) )
corrqqsum = np.zeros( (nq,nth,2) )
corrqqsum_svdsub = np.zeros( (nq,nth,atp.args.svdnsub,2) )
nprocessed = np.zeros( 2 )
if atp.args.randomXcorr == True:
    corrqqsumX = np.zeros( (nq,nth,2) )

norm1, norm2 = 0.0, 0.0
   
totalIList = []
#for i, t in enumerate( psbb.times, atp.args.nstart ):
for i in np.arange(len(psbb.times)-atp.args.nstart)+atp.args.nstart:
    t = psbb.times[i]
    if i>=(atp.args.nframes+atp.args.nstart):
        break

    m = i % 2

    if atp.args.verbose >0:
        print "Processing event ", i
    evt = psbb.run.event(t)

    r = np.int( np.random.rand()*atp.args.nframes/2 )
    j = (2*r) +m + atp.args.nstart
    if j >= atp.args.nstart+len(psbb.times):
        j = atp.args.nstart+len(psbb.times) - 1
    print "m, j", m, j
    evtj = psbb.run.event(psbb.times[j])

    # sum the data
    if atp.args.raw == True:
        data = psbb.cspad.raw( evt )
        data2 = psbb.cspad.raw( evtj )
    else:
        data = psbb.cspad.calib( evt )
        data2 = psbb.cspad.calib( evtj )

    if (data is None) or (data2 is None):
        continue

    totalI = data.sum()
    totalI2 = data2.sum()
    if atp.args.verbose >0:
        print "total intenisty :", totalI, totalI2

    if ((totalI < atp.args.minI) or (totalI2 < atp.args.minI)) and (atp.args.intensity_veto==True):
        print "Skipping event. Integrated intensity too low"
        continue
    else:
        nprocessed[m] += 1
        totalIList.append( [totalI, totalI2] )

    if atp.args.normalize==True:
        norm1 += 1.0/np.average(data*mask)
        norm2 += 1.0/np.average(data2*mask)
        data *= 1.0/np.average(data*mask)
        data2 *= 1.0/np.average(data2*mask)


    datasum[:,:,:,m] += data*mask

    if atp.args.diffCorr == True:
        diff = data - data2
        img = psbb.cspad.image(evt,diff*mask)
    else:
        img = psbb.cspad.image(evt,data*mask)

    pplot_mean = ac.polar_plot( img, nq, nth, qmin, qmax, thmin, thmax, cenx+img.shape[0]/2, ceny+img.shape[1]/2, submean=False )
    pplot = ac.polar_plot( img, nq, nth, qmin, qmax, thmin, thmax, cenx+img.shape[0]/2, ceny+img.shape[1]/2, submean=True )
    pplotcopy = np.copy( pplot)

    if atp.args.svdnsub > 0:
        print "subtracting modes:", atp.args.svdnsub
        pplot_svd_corrected = svdt.project_data( pplot, smax=atp.args.svdnsub, nstart=0)
        pplot += -pplot_svd_corrected

    if atp.args.svdnsub > 0:
        print "subtracting modes:", atp.args.svdnsub
        for i in np.arange(atp.args.svdnsub):
            pplot_svd_corrected = svdt.project_data( pplotcopy, smax=1, nstart=i)
            pplotcopy += -pplot_svd_corrected
            pplotsvdsub[:,:,i,m] = np.copy(pplotcopy)
            corrqqsum_svdsub[:,:,i,m] += ac.polarplot_angular_correlation( pplotsvdsub[:,:,i,m] * pplot_maskones )

    corrqq = ac.polarplot_angular_correlation( pplot_mean * pplot_maskones )      
    
    pplot_mean_sum[:,:,m] += pplot_mean
    pplotsum[:,:,m] += pplot
    corrqqsum[:,:,m] += corrqq


    if atp.args.randomXcorr == True:
        img = psbb.cspad.image(evt,data*mask)
        img2 = psbb.cspad.image(evt,data2*mask)
        pplot = ac.polar_plot( img, nq, nth, qmin, qmax, thmin, thmax, cenx+img.shape[0]/2, ceny+img.shape[1]/2, submean=True )
        pplot2 = ac.polar_plot( img2, nq, nth, qmin, qmax, thmin, thmax, cenx+img.shape[0]/2, ceny+img.shape[1]/2, submean=True )
        corrqq = ac.polarplot_angular_correlation( pplot, pplot2 )      
        corrqqsumX[:,:,m] += corrqq

# divide by number of processed frames
corrqqsum[:,:,0] *= 1.0/float(nprocessed[0])
corrqqsum[:,:,1] *= 1.0/float(nprocessed[1])
norm1 *= 1.0/float(nprocessed[0])
norm2 *= 1.0/float(nprocessed[1])


if atp.args.svdnsub > 0:
    for i in np.arange(atp.args.svdnsub):
        corrqqsum_svdsub[:,:,i,0] *= 1.0/float(nprocessed[0])
        corrqqsum_svdsub[:,:,i,1] *= 1.0/float(nprocessed[1])


print "Number of procesed frames even/odd", nprocessed
totalIarr = np.array(totalIList)
print "Min max integrated intensity :", np.min(totalIarr), np.max(totalIarr)

#
# correct correlations by mask correlation
#
corrqqsum[:,:,0] = ac.mask_correction( corrqqsum[:,:,0], corrqq_mask )
corrqqsum[:,:,1] = ac.mask_correction( corrqqsum[:,:,1], corrqq_mask )
if atp.args.randomXcorr == True:
    corrqqsum[:,:,0] = ac.mask_correction( corrqqsumX[:,:,0], corrqq_mask) 
    corrqqsum[:,:,1] = ac.mask_correction( corrqqsumX[:,:,1], corrqq_mask )
if atp.args.svdnsub > 0:
    for i in np.arange(atp.args.svdnsub):
        corrqqsum_svdsub[:,:,i,0] = ac.mask_correction( corrqqsum_svdsub[:,:,i,0], corrqq_mask )
        corrqqsum_svdsub[:,:,i,1] = ac.mask_correction( corrqqsum_svdsub[:,:,i,1], corrqq_mask )

#
# output normalization data
#
outname = at.io.formatted_filename( atp.args, "intensity_norm", "txt", prog=atp.parser.prog )
fnorm = open( outname, 'w' )
fnorm.write( "norm1 :"+str(norm1)+"\n" ) 
fnorm.write("norm2 :"+str(norm2)+"\n" ) 
fnorm.close()


#
# pearson correlation to measure similarity of odd/even frame angular correlations
#
pc = ac.pearsonCorrelation2D( corrqqsum[:,:,0], corrqqsum[:,:,1], lim=atp.args.pcrange )
pca = ac.pearsonCorrelation2D_angular( corrqqsum[:,:,0], corrqqsum[:,:,1], lim=atp.args.pcrange )

if atp.args.verbose > 0:
    print "Pearson value of odd/even frame angular correlation :", pc
    print "Pearson value of odd/even frame angular correlation function of q :", pca
    print "average of q-ring pearson correlations :", pca.mean()

outname = at.io.formatted_filename( atp.args, "pearson_values", "txt", prog=atp.parser.prog )
f = open( outname, 'w' )
f.write( "Pearson value of odd/even frame angular correlation :"+str(pc)+"\n" ) 
f.write("Pearson value of odd/even frame angular correlation function of q : \n")
for i in np.arange(pca.size):
    f.write( str(pca[i])+" ")
f.write("\n")
f.write( "average of q-ring pearson correlations :"+str(pca.mean())+"\n")

f.write("\n")
f.write( "Num modes subtracted, av q-ring pearson correlation\n" )
if atp.args.svdnsub > 0:
    for i in np.arange(atp.args.svdnsub):
         pca = ac.pearsonCorrelation2D_angular( corrqqsum_svdsub[:,:,i,0], corrqqsum_svdsub[:,:,i,1], lim=atp.args.pcrange )
         f.write(str(i)+", "+str(pca.mean())+"\n")
         if atp.args.verbose > 0:
             print "modes subtracted:", i, ", average of q-ring pearson correlations :", pca.mean()

f.close()
#
# save some output
#
lim = atp.args.pcrange
at.io.saveImage( atp.args, corrqqsum[:,:,0], "even_frame_angular_correlation", prog=atp.parser.prog )   
at.io.saveImage( atp.args, corrqqsum[:,:,1], "odd_frame_angular_correlation", prog=atp.parser.prog )   
at.io.saveImage( atp.args, np.sum(corrqqsum,2), "total_angular_correlation", prog=atp.parser.prog )   
at.io.saveImage( atp.args, corrqq_mask[:,:], "mask_angular_correlation", prog=atp.parser.prog )   
#at.io.saveImage( atp.args, corrqqsum[lim[0]:lim[1],lim[2]:lim[3],0], "even_frame_angular_correlation", prog=atp.parser.prog )   
#at.io.saveImage( atp.args, corrqqsum[lim[0]:lim[1],lim[2]:lim[3],1], "odd_frame_angular_correlation", prog=atp.parser.prog )   
#at.io.saveImage( atp.args, np.sum(corrqqsum[lim[0]:lim[1],lim[2]:lim[3],:],2), "total_angular_correlation", prog=atp.parser.prog )   
#at.io.saveImage( atp.args, corrqq_mask[lim[0]:lim[1],lim[2]:lim[3]], "mask_angular_correlation", prog=atp.parser.prog )   
img = psbb.cspad.image(evt,datasum[:,:,:,0])
at.io.saveImage( atp.args, img, "datasum_even", prog=atp.parser.prog )   

img = psbb.cspad.image(evt,datasum[:,:,:,1])
at.io.saveImage( atp.args, img, "datasum_odd", prog=atp.parser.prog )   

at.io.saveImage( atp.args, pplotsum[:,:,0], "polarplotsum_even", prog=atp.parser.prog )   
at.io.saveImage( atp.args, pplotsum[:,:,1], "polarplotsum_odd", prog=atp.parser.prog )   
at.io.saveImage( atp.args, pplot_mean_sum[:,:,0], "polarplot_mean_sum_even", prog=atp.parser.prog )   
at.io.saveImage( atp.args, pplot_mean_sum[:,:,1], "polarplot_mean_sum_odd", prog=atp.parser.prog )   
at.io.saveImage( atp.args, pplot_mask, "polarplot_mask", prog=atp.parser.prog )   

