import numpy as np, matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.pyplot import cm
import matplotlib.colors as colors
import modeler

#The plot shown to the user is divided into two panes: a heatmap and a table with error information.
#The table celltext is in this function.
def generate_celltext(qtapp):
	labels = ['Susceptible', 'Intermediate', 'Resistant']
	celltext = []
	for i in range(0,3):
		celltext.append(list(qtapp.confusion_matrix[i,:]))
	return celltext, labels
	



def gen_plot(qtapp, data_type='disk'):
	try:
		cutoffs_and_breakpoints = [float(current_value) for current_value in [qtapp.miccutoffS, qtapp.miccutoffR,
									qtapp.diskcutoffS, qtapp.diskcutoffR]]
		#Some cutoffs and breakpoints are very unlikely to be encuontered in reality and these
		#limits are below.
		if cutoffs_and_breakpoints[0] < 0.06 or cutoffs_and_breakpoints[0] > 120:
			return "You have entered an invalid MIC breakpoint (<0.06 or >120). Try again."
		if cutoffs_and_breakpoints[1] < 0.06 or cutoffs_and_breakpoints[1] > 120:
			return "You have entered an invalid MIC breakpoint (<0.06 or >120). Try again."
		if cutoffs_and_breakpoints[2] < 0.12 or cutoffs_and_breakpoints[2] > 64:
			return "You have entered an invalid disk cutoff(<0.12 or >64). Try again."
		if cutoffs_and_breakpoints[3] < 0.12 or cutoffs_and_breakpoints[3] > 64:
			return "You have entered an invalid disk cutoff(<0.12 or >64). Try again."
	except:
		return "You have entered a non-numeric MIC breakpoint or disk cutoff. Try again."
	#If user imported non-numeric values, as they sometimes may, return error message.
	try:
		yreal = np.log(np.clip(np.asarray(qtapp.current_dataset['mics'].values), a_min=0.016, a_max = 256))
		if data_type == 'mic':
			x = np.log(np.clip(np.asarray(qtapp.current_dataset['disks'].values), a_min=0.016, a_max=256))
		else:
			x = np.clip(np.asarray(qtapp.current_dataset['disks'].values), a_min=5, a_max=50)
	except:
		return "Your data could not be plotted. It probably contains non-numeric or negative values. Try again."
	#Update the error tables before plotting...
	modeler.update_error_tables(qtapp, data_type)
	cell_text, labels = generate_celltext(qtapp)
	#vertpoints will be used to fill in the vertical lines that mark cutoffs on the heatmap.
	vertpoints1 = np.arange(0.0161,255,0.5)


	#The .clf call here clears any existing figure, which prevents Matplotlib from stacking colorbars generated
	#when plotting a new dataset.
	qtapp.central_plot.clf()
	ax = qtapp.central_plot.add_subplot(121)
	ax2 = qtapp.central_plot.add_subplot(122)
	ax2.clear()
	ax.clear()
	#Since MIC data is on y, y-axis is always a log scale. The values shown below are standard reporting values
	#for MICs so they are convenient to use as bins.
	ybins = np.log(np.asarray([0.016,0.03,0.06,0.12,0.25,0.5,1,2,4,8,16,32,64,128,256]))
	ax.set_yticks(ybins)
	ax.set_yticklabels([0.016,0.03,0.06,0.12,0.25,0.5,1,2,4,8,16,32,64,128,''])
	ax.set_ylabel('MIC (mg/L)')
	
	#If the user imported mic vs mic data, the x-axis will need to be a log scale as well, with the same bin
	#values as y.
	if data_type == 'mic':
		xbins = np.asarray([0.016,0.03,0.06,0.12,0.25,0.5,1,2,4,8,16,32,64,128,256])
		horizpoints1 = np.log(np.asarray([0.016,0.03,0.06,0.12,0.25,0.5,1,2,4,8,16,32,64,128,256]))
		rounded_cutoffS = cutoffs_and_breakpoints[2]
		rounded_cutoffR = cutoffs_and_breakpoints[3]
		#If using MIC data on x-axis, will need to round the cutoffs to the nearest common MIC reporting
		#value (will do the same thing when we export final results)
		for i in range(1, len(xbins)):
			if cutoffs_and_breakpoints[2] > xbins[i-1] and cutoffs_and_breakpoints[2] < xbins[i]:
				rounded_cutoffS = xbins[i]
			if cutoffs_and_breakpoints[3] > xbins[i-1] and cutoffs_and_breakpoints[3] < xbins[i]:
				rounded_cutoffR = xbins[i]
		xbins = np.log(xbins)
		ax.set_xlabel('MIC, alternate method (mg/L)')
		ax.set_xticks(xbins)
		ax.set_xticklabels([0.016,0.03,0.06,0.12,0.25,0.5,1,2,4,8,16,32,64,128,''], rotation=90)
		ax.xaxis.tick_top()
		ax.plot(np.full(vertpoints1.shape[0], np.log(float(rounded_cutoffS))), np.log(vertpoints1), color='k', linewidth=0.5)
		ax.plot(np.full(vertpoints1.shape[0], np.log(float(rounded_cutoffR))), np.log(vertpoints1), color='k', linewidth=0.5)
		ax2.set_title('Status based on x-axis MIC/disk cutoff (column)\nvs status based on y-axis MIC breakpoint (row)')
	else:
		#If plotting MIC vs disk, the x-axis is much simpler -- no log scale required; disk values are in [5,50].
		xbins = np.arange(5,50,1)
		horizpoints1 = np.arange(5,50,1)
		ax.set_xlabel('Disk zone (mm)')
		ax.plot(np.full(vertpoints1.shape[0], float(qtapp.diskcutoffS)), np.log(vertpoints1), color='k', linewidth=0.5)
		ax.plot(np.full(vertpoints1.shape[0], float(qtapp.diskcutoffR)), np.log(vertpoints1), color='k', linewidth=0.5)
		ax2.set_title('Status based on disk value (column)\nvs status based on MIC breakpoint (row)')


	try:
		#The continuous colormaps are better for most real data because they ensure cells with small populations
		#aren't lost. Discrete map is provided just in case user wants it.
		if qtapp.colormap_type == 'discrete_blue':
			im = ax.hist2d(x, yreal, bins=[xbins, ybins], cmap=cm.get_cmap('Blues',20))
		elif qtapp.colormap_type == 'continuous_blue':
			im = ax.hist2d(x, yreal, bins=[xbins, ybins], cmap='Blues',norm=colors.PowerNorm(gamma=0.5))
		elif qtapp.colormap_type == 'continuous_green':
			im = ax.hist2d(x, yreal, bins=[xbins, ybins], cmap='Greens',norm=colors.PowerNorm(gamma=0.5))
		qtapp.central_plot.colorbar(im[3], ax=ax)
		#We plot the MIC breakpoints and disk cutoffs as horizontal and vertical lines.
		ax.plot(horizpoints1, np.full(horizpoints1.shape[0], np.log(float(qtapp.miccutoffS))), color='k', linewidth=0.5)
		ax.plot(horizpoints1, np.full(horizpoints1.shape[0], np.log(float(qtapp.miccutoffR))), color='k', linewidth=0.5)
		ax2.table(cellText = cell_text, rowLabels=labels, cellLoc='center',
				colLabels=labels, loc='center right', colWidths=[0.25 for col in labels])
		ax2.axis('off')
		qtapp.canvas.draw()

	except:
			return "There was an unspecified error during plotting. The data plot & error count table have not been updated."
	return '0'
