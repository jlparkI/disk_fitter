import numpy as np

def generate_next_line(caption, range_value, error_dict):
  nextline = [caption, range_value]
  nextline.append(str(error_dict['num_strains']))
  if error_dict['num_strains'] > 0:
    nextline.append('%s (%s)'%(str(error_dict['very major errors']),
                             str(round(100*error_dict['very major errors'] /
                                       error_dict['num_strains'], 2))))
    nextline.append('%s (%s)'%(str(error_dict['major errors']),
                             str(round(100*error_dict['major errors'] /
                                       error_dict['num_strains'], 2))))
    nextline.append('%s (%s)'%(str(error_dict['minor errors']),
                             str(round(100*error_dict['minor errors'] /
                                       error_dict['num_strains'], 2))))
  else:
    nextline += ['0 (0)', '0 (0)', '0 (0)']
  return nextline

#The plot shown to the user is divided into two panes: a heatmap and a table with error information.
#The table celltext is in this function.
def generate_celltext(current_model):
  diskcutoffS = float(current_model.xcutoffS)
  diskcutoffR = float(current_model.xcutoffR)
  if current_model.mic_vs_mic == False:
    celltext = [['Proposed Disk\nBreakpoint (mm)', 'Range',
               'No.\nIsolates', '', 'No. of Errors', '']]
  else:
    celltext = [['MIC breakpoints (mg/L)', 'Range',
               'No.\nIsolates', '', 'No. of Errors', '']]
  celltext.append(['','','','Very\nmajor (%)', 'Major (%)', 'Minor (%)'])
  celltext.append([current_model.strain_name, '', '', '', '', ''])
  if current_model.mic_vs_mic == False:
    if current_model.xcutoffS > current_model.xcutoffR + 1:
      int_range = [current_model.xcutoffR + 1, current_model.xcutoffS - 1]
      disk_cutoff_text = '>=%s (S) / %s-%s (I) /\n<=%s (R)'%(str(diskcutoffS),
                                                        str(int_range[0]),
                                                        str(int_range[1]),
                                                        str(diskcutoffR))
    else:
      disk_cutoff_text = '>=%s (S) / <=%s (R)'%(str(diskcutoffS), str(diskcutoffR))
  else:
    xbins = [0.016,0.03,0.06,0.12,0.125,0.25,0.5,1,2,4,8,16,32,64,128,256]
    if (xbins.index(current_model.xcutoffR) >
        (xbins.index(current_model.xcutoffS) + 1)):
      int_range = [xbins[xbins.index(current_model.xcutoffS) + 1],
                   xbins[xbins.index(current_model.xcutoffR) - 1]]
      disk_cutoff_text = '<=%s (S) / %s-%s (I) /\n>=%s (R)'%(str(diskcutoffS),
                                                        str(int_range[0]),
                                                        str(int_range[1]),
                                                        str(diskcutoffR))
    else:
      disk_cutoff_text = '<=%s (S) / >=%s (R)'%(str(diskcutoffS), str(diskcutoffR))
  celltext.append(generate_next_line(disk_cutoff_text, 'Total', current_model.error_counts))
  celltext.append(generate_next_line('', '>=I+2', current_model.i_plus2_error))
  celltext.append(generate_next_line('', 'I+1 to I-1', current_model.i_plus1_minus1_error))
  celltext.append(generate_next_line('', '<=I-2', current_model.i_minus2_error))
  if current_model.mic_vs_mic == True:
    celltext.append(['Essential agreement (%)', str(round(current_model.essential_agreement,2)),
                     '', '', '', ''])
    celltext.append(['Categorical agreement (%)', str(round(current_model.categorical_agreement,2)),
                     '', '', '', ''])
  return celltext
  
def mergecells(table, ix0, ix1):
        d = np.asarray(ix1) - np.asarray(ix0)
        if d[0] == -1:
                edges = ('BRL', 'TRL')
        elif d[0] == 1:
                edges = ('TRL', 'BRL')
        elif d[1] == -1:
                edges = ('BTR', 'BTL')
        elif d[1] == 1:
                edges = ('BTL', 'BTR')
        else:
                return
        if len(table[ix1].visible_edges) < 4:
                edges = (edges[0], ''.join([x for x in edges[1] if x in
                                            table[ix1].visible_edges]))
        if len(table[ix0].visible_edges) < 4:
                edges = (''.join([x for x in edges[0] if x in table[ix0].visible_edges]),
                         edges[1])
        for ix, e in zip((ix0, ix1), edges):
                table[ix[0], ix[1]].visible_edges = e


def fix_table(table, is_mic_vs_mic=False):
  for i in range(0,6):
    table[(0,i)].set_height(0.12)
    table[(0,i)]._text.set_fontweight('bold')
    table[(1,i)].set_height(0.12)
    table[(3,i)].set_height(0.1)
    mergecells(table, (3,i), (2,i))
    mergecells(table, (4,i), (3,i))
    mergecells(table, (5,i), (4,i))
    mergecells(table, (6,i), (5,i))
    if is_mic_vs_mic:
      mergecells(table, (7,i), (6,i))
      mergecells(table, (8,i), (7,i))
    if i > 0:
      mergecells(table, (2,i-1), (2,i))
      mergecells(table, (3,i-1), (3,i))
      mergecells(table, (4,i-1), (4,i))
      mergecells(table, (5,i-1), (5,i))
      mergecells(table, (6,i-1), (6,i))
      if is_mic_vs_mic:
        mergecells(table, (7,i-1), (7,i))
        mergecells(table, (8,i-1), (8,i))
  mergecells(table, (1,0), (0,0))
  mergecells(table, (0, 3), (0,4))
  mergecells(table, (0, 4), (0,5))
  mergecells(table, (1,1), (0,1))
  mergecells(table, (1,2), (0,2))
  table.auto_set_font_size(False)
  table.set_fontsize(7)
  table[(2,0)]._loc = 'left'
  table[(3,0)]._loc = 'left'
  table[(2,0)]._text.set_fontstyle('italic')
