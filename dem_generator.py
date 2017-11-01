# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DemGenerator
                              Random DEM generator
                              -------------------
        begin                : 2017-08-29
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Alexandre Delahaye
        email                : menoetios@gmail.com
 ***************************************************************************/
 """
import argparse
import numpy as np
import sys
from math import *
from osgeo import gdal
from osgeo.gdalconst import *

class GaussianKernel():

	def __init__(self, fwhm, amplitude, orientation, ratio, level):
		"""Constructor.

		:param fwhm: full-width-half-maximum (effective radius).
		:param amplitude:
		:param orientation: orientation (in rad)
		:param ratio: aspect ratio (eg 2 means that the kernel is 2 times
			larger in the <orientation> direction. Should be >= 1
		:param level:
		"""
		self.fwhm = fwhm
		self.ornt = orientation
		self.ratio = ratio
		self.ampl = amplitude
		self.level = level
		self.size = int( fwhm * 3.5 * sqrt(ratio) ) # kernel size (in px)
		if not self.size % 2:
			self.size += 1 # always get an odd size
		# self.kern = self.getAsArray( offset )
		# print "fwhm={0}, ampl={1}, orient={2}, ratio={3}".format(fwhm,amplitude,orientation,ratio)


	def getAsArray(self, offset):
		"""
		Make a square gaussian kernel.

		:param offset:
		:return numpy array 
		"""

		x = np.arange( 0, self.size, 1, float )
		y = np.copy(x[:,np.newaxis])
		x -= offset[0]
		y -= offset[1]
		x0 = y0 = self.size / 2
		# x and y centering and orientation
		x1 = (x-x0) * cos(self.ornt) - (y-y0) * sin(self.ornt)
		y1 = (x-x0) * sin(self.ornt) + (y-y0) * cos(self.ornt)

		return self.ampl * np.exp(-4*np.log(2) * \
			(x1**2 / self.ratio + y1**2 * self.ratio) / self.fwhm**2)


	def getRandomLocation(self, offset, thresh=0):
		"""
		Returns a random location inside a Gaussian kernel.

		:param offset:
		:param thresh: must be between 0 and 1. If 0, the returned location is 
		randomly selected following the kernel distribution (i.e. the closest to 
		the kernel center, the more	likely). Else, it is picked amongst all pixels
		whose value is higher than thresh*amplitude, following a uniform law.

		:return tuple
		"""
		if thresh == 0:
			a = self.ampl * np.random.random()
		else:
			a = self.ampl * thresh
		val = 0

		kernArray = self.getAsArray( offset ) 

		while val < a:
			x = np.random.randint( 0, self.size-1 )
			y = np.random.randint( 0, self.size-1 )
			val = kernArray[ x, y ]

		return (x, y)


class DemGenerator():


	def __init__(self):
		"""
		Constructor.

		:param xxx: Xxx
		"""


	def setParams(self, verbose=False, width=1000, height=1000, waterRatio=0.5, island=False, scale=20, 
		detailsLevel=3,	spread=3, roughness=5, directionality=5, preset=None):
		"""
		Sets generator parameters. Must be called right after instantiation.

		:param width: DEM width (default=1000)
		:param height: DEM height (default=1000)
		:param waterRatio: ratio of negative DEM values (default=0.5)
		:param island: island mode. Ensures that no piece of land is cut at the DEM border (default=False)
		:param scale: scale of main terrain features. Range: 1-100 (default=20)
		:param detailsLevel: depth of the "kernel tree". Higher value means more roughness.
			Warning: computation time increases exponentially with this parameter (default=3)
		:param spread: 1-6 (default=3)
		:param roughness: 1-10 (default=5)
		:param directionality: the higher this parameter, the more "oriented" the map features.
			Range: 1-10 (default=5)
		"""

		self.demWidth 		= width
		self.demHeight 		= height
		self.dem 			= np.zeros( (self.demWidth, self.demHeight), dtype=np.float32 )

		# Preset parameters
		# -----------------
		if preset == 'archipelago':
			waterRatio 		= 0.9 # 0.5
			island 			= False
			scale 			= 5 # 20
			detailsLevel	= 2 # 3
			spread 			= 6 # 3
			roughness 		= 3.5 # 5
			directionality 	= 5
		elif preset == 'mountainous_island':
			waterRatio 		= 0.5
			island 			= True # False
			scale 			= 20
			detailsLevel	= 3
			spread 			= 4 # 3
			roughness 		= 5
			directionality 	= 10 # 5


		# Parameters pre-initialisation
		# -----------------------------
		# Scale
		if scale < 1: scale = 1
		if scale > 100: scale = 100
		initMeanFwhm		= int(max(width, height) / 100 * scale)

		# Details
		if detailsLevel < 0: detailsLevel = 0
		maxLevelChildren 	= detailsLevel

		# Spread
		if spread < 1: spread = 1
		if spread > 6: spread = 6
		nInitKernels		= int(spread * 2)
		locationThresh		= pow(10, (1-float(spread))/2)
		if island: 	initLocRatio = float(spread) / 30 # Range: 0.033-0.2
		else:		initLocRatio = min(0.5, float(spread) / 15) # Range: 0.1-0.4

		# Roughness
		if roughness < 1: roughness = 1
		if roughness > 10: roughness = 10
		initMeanAmpl		= roughness * 4
		meanReducFactor		= float(roughness) / 12 # Range: 0.083-0.83
		maxReducFactor		= float(roughness) / 6 # Range: 0.167-1.67
		nChildren			= int(float(spread) * sqrt(float(roughness))) # Range: 1-15

		# Directionality
		if directionality < 1: directionality = 1
		if directionality > 10: directionality = 10
		initMaxRatio		= 1 + (float(directionality-1) / 3) # Range: 1-4.333
		deltaOrnt			= (11 - directionality) * pi / 10
		
		# Parameters related to first-level kernels
		# -----------------------------------------
		self.nInitKernels 	= nInitKernels # Nbr of first-level kernels
		self.initLocRatio 	= initLocRatio # Max relative distance of the centers of the first-level
										   # kernels to the center of the image (must be <= 0.5)
		self.initMeanFwhm	= initMeanFwhm # Mean full width at half maximum of first-level kernels.
								  		   # FWHM follows a triangular distribution centered on this value.
		self.initMeanAmpl	= initMeanAmpl # Mean amplitude of first-level kernels.
								 		   # Amplitude follows a triangular distribution centered on this value.
		self.initMaxRatio	= initMaxRatio # Max gaussian ratio of first-level kernels.
										   # Gaussian ratio follows a uniform distribution between 1 and this value.

		# Parameters related to children kernels
		# --------------------------------------
		self.nChildren 		= nChildren
		self.maxLevelChildren = maxLevelChildren
		self.meanReducFactor = meanReducFactor # The reduction factor determines the FWHM and amplitude of
		self.maxReducFactor = maxReducFactor   # children kernels, relative to the parent kernel. It follows
								   # a triangular distribution between 0 and self.maxReducFactor, 
								   # whose mode is self.meanReducFactor.
		self.deltaOrnt		= deltaOrnt # Maximum change of orientation
		self.locationThresh	= 0.01 # Threshold used for random children location. The closer to 1,
								   # the closer to the center of the parent kernel.

		# Other parameters
		# ----------------
		self.islandMode		= island # If true, the sea level will be raised until there is at least 
									 # a 1-pixel margin of sea arounf the DEM
		self.waterRatio 	= waterRatio # Ratio of negative height values. If the island mode is
										 # enabled, this parameter might not be taken into account.
		self.verbose 		= verbose


	def generate(self):

		for i in range(self.nInitKernels):
			fwhm = np.random.triangular( 0.5*self.initMeanFwhm, self.initMeanFwhm, 1.5*self.initMeanFwhm )
			# ampl = np.random.triangular( 0.5*self.initMeanAmpl, self.initMeanAmpl, 1.5*self.initMeanAmpl )
			ampl = np.random.triangular( 0, self.initMeanAmpl, 1.5*self.initMeanAmpl ) # 0 allows for plains
			ornt = np.random.uniform( 0, 2*pi )
			ratio = np.random.uniform( 1, self.initMaxRatio )
			gauss = GaussianKernel( fwhm, ampl, ornt, ratio, 0 )
			location = ( \
				self.demWidth * (.5 + np.random.uniform(-self.initLocRatio, self.initLocRatio)) - gauss.size/2, \
				self.demHeight * (.5 + np.random.uniform(-self.initLocRatio, self.initLocRatio)) - gauss.size/2 )
			# print location[0]+(gauss.size/2), location[1]+(gauss.size/2)
			self.addKernelToDem( gauss.getAsArray((0,0)), location )

			# Recursive call
			self.generateChildren( gauss, location, (0,0), nChildren=self.nChildren )

			if self.verbose:
				sys.stdout.write(('%.0f' % (100*float(i+1)/float(self.nInitKernels))) + '%... ')
				sys.stdout.flush()

		if self.verbose: print '' # Line break

		self.setSeaLevel()
		#self.correctElevation()
		self.printStats()

		print 'Done'


	def generateChildren(self, krn, krnLoc, krnOffset, nChildren):
		"""
		Generates children kernels from a parent kernel

		:param krn: parent kernel
		:param krnLoc: location of parent kernel (UL corner)
		:param nChildren: number of children
		"""

		if krn.level > self.maxLevelChildren:
			return

		for i in range(nChildren):

			# Get random parameters and create kernel
			reduct = np.random.triangular( 0, self.meanReducFactor, self.maxReducFactor )
			fwhm = reduct * krn.fwhm
			ampl = reduct * krn.ampl * 0.9
			ornt = np.random.triangular( krn.ornt-self.deltaOrnt, krn.ornt, krn.ornt+self.deltaOrnt )
			ratio = np.random.triangular( max(1, 0.8*krn.ratio), \
				max(1, 0.9*krn.ratio)+.01, max(1, 1.0*krn.ratio)+.02 )
			gauss = GaussianKernel(fwhm, ampl, ornt, ratio, krn.level+1)

			# Skip if kernel is too small
			if gauss.size < 5:
				continue

			# Get random position inside parent kernel
			cnt_x, cnt_y = krn.getRandomLocation(krnOffset, self.locationThresh)
			x, y = krnLoc
			childKrnLoc = (cnt_x - float(gauss.size)/2.0 + x, \
				cnt_y - float(gauss.size)/2.0 + y)
			childOffset = (np.modf(childKrnLoc[0])[0], np.modf(childKrnLoc[1])[0])
			# print "parent location=", krnLoc
			# print cnt_x, cnt_y
			# print childKrnLoc
			# print "child location=", childKrnLoc

			# Add child kernel to DEM and create grand-children
			# print "Adding kernel with offset ", childOffset
			self.addKernelToDem( gauss.getAsArray(childOffset), childKrnLoc )
			self.generateChildren( gauss, childKrnLoc, childOffset, nChildren=self.nChildren )


	def addKernelToDem(self, kernArray, ul):
		"""
		Add a gaussian kernel to a larger DEM.

		:param kernel: GaussianKernel instance
		:param ul: kernel upper left coordinates in the DEM
		"""
		krn_x, krn_y = np.shape(kernArray)

		krn_start_x, krn_start_y = 0, 0
		krn_end_x, krn_end_y = krn_x - 1, krn_y - 1
		dem_start_x, dem_start_y = int(ul[0]), int(ul[1])
		dem_end_x, dem_end_y = dem_start_x + krn_end_x, dem_start_y + krn_end_y

		if dem_start_x < 0:
			krn_start_x = -dem_start_x
			dem_start_x = 0
		if dem_start_y < 0:
			krn_start_y = -dem_start_y
			dem_start_y = 0
		if dem_end_x >= self.demWidth:
			krn_end_x = krn_x - (dem_end_x - self.demWidth + 1)
			dem_end_x = self.demWidth
		if dem_end_y >= self.demHeight:
			krn_end_y = krn_y - (dem_end_y - self.demHeight + 1)
			dem_end_y = self.demHeight

		# print dem_start_x, dem_start_y
		# print dem_end_x, dem_end_y
		# print krn_start_x, krn_start_y
		# print krn_end_x, krn_end_y

		try:
			self.dem[dem_start_x:dem_end_x, dem_start_y:dem_end_y] = \
				self.dem[dem_start_x:dem_end_x, dem_start_y:dem_end_y] + \
				kernArray[krn_start_x:krn_end_x, krn_start_y:krn_end_y]
		except ValueError:
			0
			# print "Error when adding kernel: ", "shape=", np.shape(kernArray), "  UL=", ul


	def setSeaLevel(self):
		"""
		Adjusts the sea level (0-level) according to self.waterRatio and self.island
		"""
		# Initial water raising
		zeroLevel = np.percentile(self.dem, 100*self.waterRatio)
		if self.verbose: print '[Water ratio] Sea level raised by ', zeroLevel
		self.dem -= zeroLevel

		# Island mode: set at least a 1-pixel margin of water
		if self.islandMode:
			maxInMargin = max(np.max(self.dem[0,:]), \
				np.max(self.dem[-1,:]), \
				np.max(self.dem[:,0]), \
				np.max(self.dem[:,-1]))
			if maxInMargin > 0:
				if self.verbose: print '[Island mode] Sea level raised by ', maxInMargin
				self.dem -= maxInMargin
	

	def correctElevation(self):
		"""
		Adjusts mean elevation 
		TODO...
		"""
		self.dem /= 10


	def printStats(self):
		"""
		Prints DEM statistics
		"""
		print 'Water ratio:', float(np.count_nonzero(self.dem < 0)) / float(self.dem.size)
		print 'Lowest point:', np.min(self.dem)
		print 'Highest point:', np.max(self.dem)
		print 'Mean positive elevation:', np.mean(self.dem[self.dem >= 0])
		print 'Median positive elevation:', np.median(self.dem[self.dem >= 0])



	def writeToFile(self, path):

		driver = gdal.GetDriverByName('GTiff')
		outDs = driver.Create(path, self.demWidth, self.demHeight, 1, GDT_Float32)

		if outDs is None:
		    print 'Could not create', path
		    sys.exit(1)

		outDs.SetGeoTransform((0, 1, 0, self.demHeight, 0, -1))

		# write the data
		outBand = outDs.GetRasterBand(1)
		outBand.WriteArray(np.transpose(self.dem), 0, 0)

		# flush data to disk, set the NoData value and calculate stats
		outBand.FlushCache()
		outBand.SetNoDataValue(-99)






parser = argparse.ArgumentParser(description='Generates a random DEM.')
parser.add_argument("dempath", metavar='path', help='output DEM path')
parser.add_argument("--verbose", action="store_true", help="increase output verbosity")
parser.add_argument("--height", type=int, default=1000, help="DEM height (default: 1000)")
parser.add_argument("--width", type=int, default=1000, help="DEM width (default: 1000)")
parser.add_argument("--waterratio", type=float, default=0.5, help="water ratio (default: 0.5)")
parser.add_argument("--island", action="store_true", help="set island mode")
parser.add_argument("--scale", type=float, default=20, help="features scale (default: 20)")
parser.add_argument("--detailslevel", type=float, default=3, help="level of features details (default: 3)")
parser.add_argument("--spread", type=float, default=3, help="features spread (default: 3)")
parser.add_argument("--roughness", type=float, default=5, help="features roughness (default: 5)")
parser.add_argument("--directionality", type=float, default=5, help="features directionality (default: 5)")
parser.add_argument("--preset", type=str, choices=['archipelago', 'mountainous_island'], \
	help="predefined set of parameters (overrides all parameters except height and width)")
args = parser.parse_args()

dem = DemGenerator()
dem.setParams(
	verbose=args.verbose,
	height=args.height,
	width=args.width,
	waterRatio=args.waterratio,
	island=args.island,
	scale=args.scale,
	detailsLevel=args.detailslevel,
	spread=args.spread,
	roughness=args.roughness,
	directionality=args.directionality,
	preset=args.preset)
dem.generate()
dem.writeToFile(args.dempath)