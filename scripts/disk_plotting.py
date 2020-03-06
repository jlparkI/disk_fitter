import numpy as np, matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.pyplot import cm
import matplotlib.colors as colors
from matplotlib.colors import ListedColormap
import generate_tabletext


def create_christmas_colormap():
  christmas_colormap = cm.get_cmap('viridis', 31)
  christmas_colormap.colors[0,0:-1] = [1,1,1]
  for i in range(1,29):
    christmas_colormap.colors[i,0:-1] = [0,0.9-i*0.02,0]
  christmas_colormap.colors[-2,0:-1] = [0.5,0,0]
  christmas_colormap.colors[-1,0:-1] = [1,0,0]
  return christmas_colormap


def gen_plot(qtapp, data_type='disk'):
  current_model = qtapp.curr_model
  mic_cutoffS = float(current_model.ycutoffS)
  mic_cutoffR = float(current_model.ycutoffR)
  try:
    #Some cutoffs and breakpoints are very unlikely to be encuontered in reality and these
    #limits are below.
    if float(current_model.ycutoffS) < 0.06 or float(current_model.ycutoffS) > 120:
      return "You have entered an invalid MIC breakpoint (<0.06 or >120). Try again."
    if float(current_model.ycutoffR) < 0.06 or float(current_model.ycutoffR) > 120:
      return "You have entered an invalid MIC breakpoint (<0.06 or >120). Try again."
    if float(current_model.xcutoffS) < 0.12 or float(current_model.xcutoffS) > 64:
      return "You have entered an invalid disk cutoff(<0.12 or >64). Try again."
    if float(current_model.xcutoffR) < 0.12 or float(current_model.xcutoffR) > 64:
      return "You have entered an invalid disk cutoff(<0.12 or >64). Try again."
  except:
    return "You have entered a non-numeric MIC breakpoint or disk cutoff. Try again."
  #If user imported non-numeric values, as they sometimes may, return error message.
  try:
    yreal = np.log(np.clip(np.asarray(current_model.current_dataset['mics']), a_min=0.016, a_max = 256))
    if current_model.mic_vs_mic:
      x = np.log(np.clip(np.asarray(current_model.current_dataset['disks']), a_min=0.016, a_max=256))
    else:
      x = np.clip(np.asarray(current_model.current_dataset['disks']), a_min=5, a_max=50)
  except:
    return "Your data could not be plotted. It probably contains non-numeric or negative values. Try again."
  #Update the error tables before plotting...
  error_code = current_model.update_error_tables(current_model.mic_vs_mic)
  if error_code != '0':
    return error_code
  cell_text = generate_tabletext.generate_celltext(current_model)
  #vertpoints will be used to fill in the vertical lines that mark cutoffs on the heatmap.
  vertpoints1 = np.arange(0.0161,255,0.5)


  #The .clf call here clears any existing figure, which prevents Matplotlib from stacking colorbars generated
  #when plotting a new dataset.
  qtapp.central_plot.clf()
  ax = qtapp.central_plot.add_subplot(121)
  ax2 = qtapp.central_plot.add_subplot(122)
  qtapp.central_plot.subplots_adjust(left=0.08, right=0.95, bottom=0.18)
  ax2.clear()
  ax.clear()
  #Since MIC data is on y, y-axis is always a log scale. The values shown below are standard reporting values
  #for MICs so they are convenient to use as bins.
  ybins = np.asarray([0.016,0.03,0.06,0.12,0.25,0.5,1,2,4,8,16,32,64,128,256])
  #For the susceptibility MIC breakpoint, we have to draw the line 1 category up because of the way the axis is set up.
  #Must round up to next highest mic bin.
  mic_cutoffS = float(current_model.ycutoffS)
  for i in range(0, len(ybins)-1):
      if mic_cutoffS >= ybins[i] and mic_cutoffS < ybins[i+1]:
        mic_cutoffS = ybins[i+1]
        break
  ybins = np.log(ybins)
  ax.set_yticks(ybins)
  ax.set_yticklabels([0.016,0.03,0.06,0.12,0.25,0.5,1,2,4,8,16,32,64,128,''])
  ax.set_ylabel('MIC (mg/L)')
  
  #If the user imported mic vs mic data, the x-axis will need to be a log scale as well, with the same bin
  #values as y.
  if current_model.mic_vs_mic:
    xbins = np.log(np.asarray([0.016,0.03,0.06,0.12,0.25,0.5,1,2,4,8,16,32,64,128,256]))
    horizpoints1 = np.log(np.asarray([0.016,0.03,0.06,0.12,0.25,0.5,1,2,4,8,16,32,64,128,256]))
    #If using MIC data on x-axis, will need to round the cutoffs to the nearest common MIC reporting
    #value (will do the same thing when we export final results)
    ax.set_xlabel('MIC, alternate method (mg/L)')
    ax.set_xticks(xbins)
    ax.set_xticklabels([0.016,0.03,0.06,0.12,0.25,0.5,1,2,4,8,16,32,64,128,''], rotation=90)
    ax.xaxis.tick_top()

    xbins = [0.016,0.03,0.06,0.12,0.25,0.5,1,2,4,8,16,32,64,128,256]
    if current_model.xcutoffS <= 128:
      rounded_cutoffS = xbins[xbins.index(current_model.xcutoffS)+1]
    else:
      rounded_cutoffS = 256
    ax.plot(np.full(vertpoints1.shape[0], np.log(rounded_cutoffS)),
            np.log(vertpoints1), color='k', linewidth=0.5)
    ax.plot(np.full(vertpoints1.shape[0], np.log(current_model.xcutoffR)), np.log(vertpoints1), color='k', linewidth=0.5)
    xbins = np.log(np.asarray(xbins))
  else:
    #If plotting MIC vs disk, the x-axis is much simpler -- no log scale required; disk values are in [5,50].
    xbins = np.arange(5,50,1)
    horizpoints1 = np.arange(5,50,1)
    ax.set_xlabel('Disk zone (mm)')
    ax.plot(np.full(vertpoints1.shape[0], current_model.xcutoffS), np.log(vertpoints1), color='k', linewidth=0.5)
    ax.plot(np.full(vertpoints1.shape[0], current_model.xcutoffR+1), np.log(vertpoints1), color='k', linewidth=0.5)


  #try:
  if current_model.colormap_type == 'christmas_colors':
    im = ax.hist2d(x, yreal, bins=[xbins, ybins], cmap=create_christmas_colormap(), norm=colors.PowerNorm(gamma=0.5))
  elif current_model.colormap_type == 'continuous_blue':
    im = ax.hist2d(x, yreal, bins=[xbins, ybins], cmap='Blues',norm=colors.PowerNorm(gamma=0.5))
  elif current_model.colormap_type == 'continuous_green':
    im = ax.hist2d(x, yreal, bins=[xbins, ybins], cmap='Greens',norm=colors.PowerNorm(gamma=0.5))
  qtapp.central_plot.colorbar(im[3], ax=ax)
  #We plot the MIC breakpoints and disk cutoffs as horizontal and vertical lines.
  ax.plot(horizpoints1, np.full(horizpoints1.shape[0], np.log(mic_cutoffS)), color='k', linewidth=0.5)
  ax.plot(horizpoints1, np.full(horizpoints1.shape[0], np.log(float(current_model.ycutoffR))), color='k', linewidth=0.5)

  #except:
  #    return "There was an unspecified error during plotting. The data plot & error count table have not been updated."
  table = ax2.table(cellText = cell_text,cellLoc='center',
        loc='center', colWidths=[0.4, 0.17, 0.17, 0.17, 0.17, 0.17])
  ax2.axis('off')
  generate_tabletext.fix_table(table, current_model.mic_vs_mic)
  qtapp.canvas.draw()
  return '0'
