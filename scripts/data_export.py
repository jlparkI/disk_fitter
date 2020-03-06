import numpy as np, generate_tabletext

#Our microbiology team requested a specific format for export data. Basically, we're going to take the same
#table shown in the application and write it to csv by joining all lists with ','. 
def export_results(current_model, filename):
  if current_model.current_dataset['mics'] is None:
    return "You want to export data but you haven't loaded any? Try loading some first. Now there's an idea!"
  output_file = open(filename, 'w+')
  output_table = generate_tabletext.generate_celltext(current_model)
  for i in range(0, len(output_table)):
    output_table[i] = [z.replace('\n',' ') for z in output_table[i]]
    output_file.write(','.join(output_table[i]) + '\n')
  try:
    ybins = np.asarray([0.016,0.03,0.06,0.12,0.25,0.5,1,2,4,8,16,32,64,128,256])
    xbins = np.arange(4,54,1)
    #If the user is providing MIC vs MIC data, the xbins will be the same as y. Otherwise,
    #they are based on typical disk values (between 4 and 54 mm).
    if current_model.mic_vs_mic:
      xbins = np.copy(ybins)
    #Our microbiology team wanted to have a text-based histogram. The code below writes a text-based
    #histogram into the csv file.
    
  except:
    return ("The data could not be exported. The program is trying to write to a file called '%s'. Make sure that you don't "
      "have a file by this name already open."%filename)
  output_file.write('\n\n\nThe chart below plots disk zone (on x) vs mic (on y)\n')
  text_histogram, xedges, yedges = np.histogram2d(np.asarray(current_model.current_dataset['disks']),
                                       np.asarray(current_model.current_dataset['mics']),
                                       bins=[xbins,ybins])
  text_histogram = np.flip(text_histogram, axis=1)
  yedges = np.flip(yedges, axis=0)
  for i in range(0, text_histogram.shape[1]):
    if i < (yedges.shape[0]-1):
      output_line = [str(yedges[i+1])]
    else:
      output_line = ['']
    for j in range(0, text_histogram.shape[0]):
      if text_histogram[j,i] > 0:
        output_line.append(str(text_histogram[j,i]))
      else:
        output_line.append('')
    output_file.write(','.join(output_line))
    output_file.write('\n')
  output_file.write(',' + ','.join([str(z) for z in xedges]))
  output_file.close()
  return '0'
