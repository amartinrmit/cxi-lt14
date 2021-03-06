"""
cxilt14py
- Analysis scripts for performing angular correlation analysis on the cspad detector @ CXI @ LCLS

aduHistogram.py - make histogram of pixel values in detector, asic, or pixel(s)

September 2018

authors: Andrew Martin (andrew.martin@rmit.edu.au)
         

"""


import numpy as np
import analysisTools as at
import h5py


def histindex( x, xmin, xmax, xbins):
    ib = int((x - xmin)*xbins/(xmax-xmin))
    if ib>xbins-1: ib = xbins-1
    if ib<0 : ib = 0
    return ib


#
# set up parsing of command line arguments
#
atp = at.params.parameters()

# add another command line argument
atp.parser.add_argument( "--outputext", help="File extention for output image: .dbin or .h5", default="dbin")
atp.parser.add_argument( "--average", help="Choose to output data average or data sum", type=bool, default=False)
atp.parser.add_argument( "--assemble",  help="assemble data (true) or leave as array of asic data", type=bool, default=True)
atp.parser.add_argument( "--raw", help="output uncorrected data (true) or all corrections [dark/gain/common mode]", type=bool, default=False)
atp.parser.add_argument( "--applymask", help="apply a mask retrieved from psana", type=bool, default=True)
atp.parser.add_argument( "--hmax", help="max value in histogram", type=float, default=1000.0)
atp.parser.add_argument( "--hmin", help="min value in histogram", type=float, default=0.0)
atp.parser.add_argument( "--hbins", help="number of bins in histogram", type=int, default=1000)
atp.parser.add_argument( "--hpix", help="string of pixel coordinates to analyse. 3 comma seperated indices per pixel. Pixels seperated by colons ", default="")

atp.parser.add_argument( "--imax", help="max value in histogram", type=float, default=1e8)
atp.parser.add_argument( "--imin", help="min value in histogram", type=float, default=1e6)
atp.parser.add_argument( "--ibins", help="number of bins in histogram", type=int, default=1)

atp.parser.add_argument( "--pixelMask", help="a numpy file to specify which pixels to create histogram for ", default="None")
atp.parser.add_argument( "--pixelMask2", help="a numpy file to specify  pixels correlate against pixels in first pixelMask ", default="None")
atp.parser.add_argument( "--rebinx", help="rebin data in x by this factor", type=int, default=-1)
atp.parser.add_argument( "--rebiny", help="rebin data in y by this factor", type=int, default=-1)
atp.parser.add_argument( "--polarRange", nargs=4, help="pixel range to evaluate polar plots of assembled images ", type=float)
atp.parser.add_argument( "--nq", help="number of radial (q) polar bins ", type=int)
atp.parser.add_argument( "--nth", help="number of angular polar bins ", type=int)



# parse the command line arguments
atp.parse_arguments()

print atp.args.hmin-int(atp.args.hmin)
if (atp.args.hmin-int(atp.args.hmin))<0.5:
    print "changing hmin"
    atp.args.hmin = -float(int(atp.args.hmin))

# write all the input arguments to a log file
atp.write_all_params_to_file( script=atp.parser.prog )



#
# Set up the psana variables from psana wrapper
#
print atp.args.exp, atp.args.run
psbb = at.psanaWrapper.psanaBlackBox( exp=atp.args.exp, run=atp.args.run )


#
# Set up polar indices
#
# get arrays with q values
print "Arg test:", atp.args.polarRange[0]

qarrays = psbb.qarrays( psbb.evt )
#tharr = #np.outer( np.ones(atp.args.nq), np.arange(atp.args.nth) )*(atp.args.polarRange[3]-atp.args.polarRange[2])/float(atp.args.nth)
atpp = at.powder.powder()
atpp.set_up_qth_indices( qarrays[3], qarrays[4], nqbins=atp.args.nq,\
                         qmin=atp.args.polarRange[0], qmax=atp.args.polarRange[1],\
                         nthbins=atp.args.nth, thmin=atp.args.polarRange[2],\
                         thmax=atp.args.polarRange[3])
#print "qarrays max min", np.max(qarrays[4]), np.min(qarrays[3])


#
# retrieve mask if required
#
if atp.args.applymask == True:
    mask = psbb.cspad.mask( psbb.run.event( psbb.times[0]), calib=True, status=True, edges=True, central=True, unbondnbrs=True)

#
# load the pixel mask
#
if atp.args.pixelMask != "None":
    ipmaskin = np.load( atp.args.pixelMask )
    print ipmaskin.shape, ipmaskin
    pflag = True
    #ipmask = np.where( pmask == 1.0 )
    ipmask = ( ipmaskin[0], ipmaskin[1] ) #, ipmaskin[2])
    npix = ipmask[0].size
    print npix, ipmaskin.shape, type(ipmaskin)

    t = psbb.times[10]
    evt = psbb.run.event(t)
    mk = np.zeros( (32,185,388) ) + 0.05

    for i in np.arange(ipmask[0].shape[0]):
        m = ipmaskin[0,i]*ipmask[0].shape[0] + ipmaskin[1,i]
        indices = atpp.iqth[m] #ipmaskin[0,i], ipmaskin[1,i]]
        print i, ipmask[0], ipmaskin[0,i], ipmaskin[1,i], indices[0].shape
        mk[indices] = 1.0
    assembledmask =  psbb.cspad.image(  evt, mk )
    outname = atp.args.outpath+atp.parser.prog[:-3]+"_"+atp.args.tag+"_"+atp.args.exp+"_"+atp.args.run+"_pixelmask."+atp.args.outputext
    print outname
    at.io.saveImage( atp.args, assembledmask, "polarpixelmask", prog=atp.parser.prog, outname=outname )   


#
# load the pixel mask
#
if atp.args.pixelMask2 != "None":
    ipmaskin2 = np.load( atp.args.pixelMask2 )
    pflag2 = True
    #ipmask = np.where( pmask == 1.0 )
    ipmask2 = ( ipmaskin2[0], ipmaskin2[1] ) #, ipmask2[2])
    npix2 = ipmask2[0].size

    t = psbb.times[10]
    evt = psbb.run.event(t)
    mk = np.zeros( (32,185,388) ) + 0.05
    for i in np.arange(ipmask2[0].shape[0]):
        m = ipmaskin2[0,i]*atp.args.nq + ipmaskin2[1,i]
        indices = atpp.iqth[m] 
        mk[indices] = 1.0
    assembledmask =  psbb.cspad.image(  evt, mk )
    outname = atp.args.outpath+atp.parser.prog[:-3]+"_"+atp.args.tag+"_"+atp.args.exp+"_"+atp.args.run+"_pixelmask2."+atp.args.outputext
    print outname
    at.io.saveImage( atp.args, assembledmask, "polarpixelmask2", prog=atp.parser.prog, outname=outname )   

    
#    exit()
else:
    pflag = False

#
# set intensity binning flag
#
if atp.args.ibins>0:
    ibinflag = True
    ibins = atp.args.ibins
else:
    ibinflag = False
    ibins = 1

#
# parse pixel indices
#
pix = atp.args.hpix.split(";")
plist = []
for p in pix:
    ind = p.split(",")
    if len(ind)!=3:
        continue
    plist.append( ind )
print "plist", len(plist)




#
# sum nframes of data from a run
#
datasum = psbb.cspad.calib( psbb.evt ) * 0.0
dethistsum = np.zeros( atp.args.hbins )
det2x1histsum = np.zeros( (32, ibins, atp.args.hbins) )
pixelhistsum = np.zeros( (len(plist),  atp.args.hbins) )
totalIhist = np.zeros( 1000 )

if pflag:
    print npix,npix2,ibins,atp.args.hbins,atp.args.hbins
    pmhistsum = np.zeros( (npix,npix2,ibins,atp.args.hbins,atp.args.hbins) )
    pmhiststat = np.zeros( (npix,npix2,ibins,atp.args.hbins,atp.args.hbins,2) )

#for i, t in enumerate( psbb.times, atp.args.nstart ):
for i in range(atp.args.nframes ):
    t = psbb.times[i + atp.args.nstart ]

    if atp.args.verbose >0:
        print "Processing event ", i+atp.args.nstart
    evt = psbb.run.event(t)

    # sum the data
    if atp.args.raw == True:
        data = psbb.cspad.raw( evt )
    else:
        data = psbb.cspad.calib( evt, cmpars=(5,0,0,0) )

    totalI = np.sum(data) 
    ii = histindex( totalI, 1e6, 1e9, 1000 )
    totalIhist[ii] += 1

    if ibinflag:
        ib = int((totalI - atp.args.imin)*ibins/(atp.args.imax-atp.args.imin))
        if ib>ibins-1: ib = ibins-1
        if ib<0 : ib = 0
    else:
        ib = 0

    # normalize
    istep = (atp.args.imax-atp.args.imin) / float(ibins)
    data *= (ib+0.5)*istep / totalI

    dethist, dethist_x = np.histogram( data, bins=atp.args.hbins, range=(atp.args.hmin,atp.args.hmax) )
    dethistsum += dethist
    print "hmin", atp.args.hmin

    for j in np.arange(32):
        dethist, dethist_x = np.histogram( data[j,:,:], bins=atp.args.hbins, range=(atp.args.hmin,atp.args.hmax) )
        det2x1histsum[j,ib,:] += dethist
    
    print "debug :", atp.args.rebinx, atp.args.rebiny
    #if (atp.args.rebinx>0) and (atp.args.rebiny>0):
    #    dataB = psbb.asic_intensity( data, rebinx=atp.args.rebinx, rebiny=atp.args.rebiny )
    #else:
    #    dataB = data
    dataB = atpp.polarplot_otf( data, mask )
    
    if pflag and pflag2:
        dpix =  dataB[0][ipmask]
        dpix2 =  dataB[0][ipmask2]
        for j in np.arange(npix):
            for k in np.arange(npix2):
#                if j == 5: print "adu pixel 5:",  dpix[j]
                index = histindex(dpix[j], atp.args.hmin, atp.args.hmax, atp.args.hbins )
                index2 = histindex(dpix[k], atp.args.hmin, atp.args.hmax, atp.args.hbins )
                pmhistsum[j,k,ib,index,index2] += 1
                pmhiststat[j,k,ib,index,index2,0] += dpix[j]
                pmhiststat[j,k,ib,index,index2,1] += dpix[j]**2
                
    for j in range(len(plist)):
        p = plist[j]
        dethist, dethist_x = np.histogram( data[p[0],[1],p[2]], bins=atp.args.hbins, range=(atp.args.hmin,atp.args.hmax) )
        pixelhistsum[j,:] += dethist

if atp.args.average == True:
    dethistsum *= 1.0/float(atp.args.nframes)
    det2x1histsum *= 1.0/float(atp.args.nframes)
#    pixelhistsum *= 1.0/float(atp.args.nframes)
#    pmhistsum *= 1.0/float(atp.args.nframes)

#
# process pixel stats
#
if pflag:
#npix,ibins,atp.args.hbins) )
    for i in np.arange(npix):
        for i2 in np.arange(npix2):
            for j in np.arange(ibins):
                for k in np.arange(atp.args.hbins):
                    for k2 in np.arange(atp.args.hbins):
                        if pmhistsum[i,i2,j,k,k2] > 0:
                            pmhiststat[i,i2,j,k,k2,0] *= 1.0/float(pmhistsum[i,i2,j,k,k2])
                            pmhiststat[i,i2,j,k,k2,1] *= 1.0/float(pmhistsum[i,i2,j,k,k2])
                            pmhiststat[i,i2,j,k,k2,1] = pmhiststat[i,i2,j,k,k2,1] - pmhiststat[i,i2,j,k,k2,0]**2
                            if pmhiststat[i,i2,j,k,k2,1] > 0:
                                pmhiststat[i,i2,j,k,k2,1] = np.sqrt(pmhiststat[i,i2,j,k,k2,1])
                            else:
                                pmhiststat[i,i2,j,k,k2,1] = 0.0

#
# store the per pixel histograms
#
if pflag:
    outname = atp.args.outpath+atp.parser.prog[:-3]+"_"+atp.args.tag+"_"+atp.args.exp+"_"+atp.args.run+"_"+str(atp.args.nstart)+"_"+str(atp.args.nframes)+"_polar_pixel_histograms.h5"

    f = h5py.File(outname, 'w')    # overwrite any existing file
    field = "/ibinflag_imin_imax_ibins"
    f.create_dataset(field, data=np.array([ibinflag, atp.args.imin,atp.args.imax,ibins]) )
    
    field = "/pflag_hmin_hmax_hbins"
    f.create_dataset(field, data=np.array([pflag, atp.args.hmin,atp.args.hmax,atp.args.hbins]) )
    
    field = "/pixel_indices"
    f.create_dataset(field, data=ipmask )

    field = "/pixel_histograms"
    f.create_dataset(field, data=pmhistsum )

    field = "/totalIhist"
    f.create_dataset(field, data=totalIhist )

    field = "/pixel_hist_stats"
    f.create_dataset(field, data=pmhiststat )
    
    f.close()
    

#
# store average detector and asic histograms
#
outname = atp.args.outpath+atp.parser.prog[:-3]+"_"+atp.args.tag+"_"+atp.args.exp+"_"+atp.args.run+"_"+str(atp.args.nstart)+"_"+str(atp.args.nframes)+"_polar_histograms.h5"

f = h5py.File(outname, 'w')    # overwrite any existing file

field = "/dethist"
f.create_dataset(field, data=dethistsum )

field = "/dethist_x"
f.create_dataset(field, data=dethist_x )

# store asic
field = "/asic2x1hist"
dset = f.create_dataset(field, data=det2x1histsum)

# store pixel
for i in np.arange(len(plist)):
    field = "/pixelhist/pixel_ind_"+str(i)
    dset = f.create_dataset(field, data=np.array(plist[i]))
    field = "/pixelhist/pixel_hist_"+str(i)
    dset = f.create_dataset(field, data=pixelhistsum[i,:])

f.close()
