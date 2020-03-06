from PyQt5 import QtCore
from PyQt5.QtWidgets import QLabel, QWidget, QPushButton, QVBoxLayout, QMainWindow
from PyQt5.QtWidgets import QFileDialog, QLineEdit, QHBoxLayout, QCheckBox, QComboBox
import disk_plotting, data_processing, data_export, model_object, alerts
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

#Each instance of the application is an object of class disk_fitter, with all of the user-defined parameters,
#the input data, the current model (object of class model_parameter_set) and the results for export stored as class attributes.
#This is an extremely simple approach adopted because the application is relatively simple and only needs to
#perform specific tasks. If this were to be expanded to perform additional tasks, this structure might
#need to be expanded.
class main_window(QMainWindow):

  def __init__(self):
    super().__init__()
    self.curr_model = model_object.model_parameter_set()

    self.central_plot = Figure()
    self.canvas = FigureCanvas(self.central_plot)
    self.toolbar = NavigationToolbar(self.canvas, self)
    
    #In this next part, we're just building the interface by adding box layouts
    #and adding widgets to each box layout to get the overall layout we want.
    self.setWindowTitle('Disk Fitter 1.0')
    self.central_widget = QWidget()
    self.setCentralWidget(self.central_widget)
    self.resize(950,600)
    mainlayout = QVBoxLayout(self.central_widget)
    main_controls = QHBoxLayout()
    horiz_layouts = [QHBoxLayout() for i in range(0,7)]

    mainlayout.addWidget(self.toolbar)
    mainlayout.addWidget(self.canvas)

    ###Three main buttons, one to import data, one to fit and one to export results.

    import_button = QPushButton('Import data')
    main_controls.addWidget(import_button)
    import_button.clicked.connect(self.load_file)

    fit_button = QPushButton('Fit/Plot data')
    fit_button.setDefault(True)
    fit_button.setAutoDefault(True)
    main_controls.addWidget(fit_button)
    fit_button.clicked.connect(self.fit_data)

    export_button = QPushButton('Export results')
    main_controls.addWidget(export_button)
    export_button.clicked.connect(self.export_results)

    ###Now add text boxes user can add to modify the MIC breakpoints. These are stacked next to each other

    self.susceptibility_label = QLabel('Susceptibility breakpoint (<=, mg/L)')
    horiz_layouts[0].addWidget(self.susceptibility_label)
    self.resistance_label = QLabel('Resistance breakpoint (>=, mg/L)')
    horiz_layouts[0].addWidget(self.resistance_label)

    self.susceptibility_breakpoint = QLineEdit()
    self.susceptibility_breakpoint.setText('4')
    self.susceptibility_breakpoint.textChanged.connect(self.update_s_cutoff)
    horiz_layouts[1].addWidget(self.susceptibility_breakpoint)

    self.resistance_breakpoint = QLineEdit()
    self.resistance_breakpoint.setText('16')
    self.resistance_breakpoint.textChanged.connect(self.update_r_cutoff)
    horiz_layouts[1].addWidget(self.resistance_breakpoint)
    
    #Here's where the user can select the type of model they will use to fit, and the coloring scheme they
    #want for the plot.
    self.regression_type = QComboBox()
    self.regression_type.addItem("min gini impurity")
    self.regression_type.activated[str].connect(self.change_regression_type)
    horiz_layouts[2].addWidget(self.regression_type)

    self.color_palette = QComboBox()
    self.color_palette.addItem("Christmas Colors")
    self.color_palette.addItem("Blue Palette")
    self.color_palette.addItem("Green Palette")
    self.color_palette.activated[str].connect(self.change_color_palette)
    horiz_layouts[2].addWidget(self.color_palette)


    ##Now add text boxes user can add to modify the disk cutoffs if desired, after a checkbox to indicate
    #whether or not manual cutoffs should override.
    self.manual_override = QCheckBox('Use user-specified cutoffs and override fitting procedure', self)
    self.manual_override.stateChanged.connect(self.manual_fit_button)
    horiz_layouts[3].addWidget(self.manual_override)

    #This box is extremely important -- determines whether we are dealing with MIC vs MIC data or not. If we are dealing
    #with MIC vs MIC data, we don't need to fit, and the way we process the data must be completely different, because
    #it's a completely different kind of data.
    self.mic_vs_mic_checkbox = QCheckBox('Process MIC vs MIC data', self)
    self.mic_vs_mic_checkbox.stateChanged.connect(self.mic_vs_mic_data)
    horiz_layouts[3].addWidget(self.mic_vs_mic_checkbox)

    #The user-specified resistance and susceptible cutoffs and their somewhat arbitrary defaults.
    self.diskR_label = QLabel('Resistance disk cutoff (<=, mm)')
    horiz_layouts[4].addWidget(self.diskR_label)
    self.diskS_label = QLabel('Susceptibility disk cutoff(>=, mm)')
    horiz_layouts[4].addWidget(self.diskS_label)
    
    self.diskR_breakpoint = QLineEdit()
    self.diskR_breakpoint.setText('32')
    self.diskR_breakpoint.textChanged.connect(self.diskR_manual_cutoff)
    horiz_layouts[5].addWidget(self.diskR_breakpoint)
    self.diskS_breakpoint = QLineEdit()
    self.diskS_breakpoint.setText('12')
    self.diskS_breakpoint.textChanged.connect(self.diskS_manual_cutoff)
    horiz_layouts[5].addWidget(self.diskS_breakpoint)

    #Enables the user to change the strain name to prettify the output table.
    self.strain_name_label = QLabel('Strain Name:')
    horiz_layouts[6].addWidget(self.strain_name_label)
    self.strain_name_input = QLineEdit()
    self.strain_name_input.setText(self.curr_model.strain_name)
    self.strain_name_input.textChanged.connect(self.strain_name_change)
    horiz_layouts[6].addWidget(self.strain_name_input)

    mainlayout.addLayout(main_controls)
    for horiz_layout in horiz_layouts:
        mainlayout.addLayout(horiz_layout)
    self.show()


    
  def strain_name_change(self, text):
    self.curr_model.strain_name = text

  #Currently there is only one model type available; this function
  #is here in case we ever add another...
  def change_regression_type(self, text):
    if text == 'min gini model':
      self.curr_model.model_type = 'mgm'

  def change_color_palette(self, text):
    if text == 'Blue Palette':
      self.curr_model.colormap_type = 'continuous_blue'
    elif text == 'Christmas Colors':
      self.curr_model.colormap_type = 'christmas_colors'
    elif text == 'Green Palette':
      self.curr_model.colormap_type = 'continuous_green'

  #If loading a file, call the load_dataset method of class model_parameter_set.
  #If it finds a problem with the file passed to it, it will return a non-'0' error code.
  #The sudden death function (defined in alerts.py) prints
  #a message box with the error message passed to it and is used for error handling
  #throughout.
  def load_file(self):
    options = QFileDialog.Options()
    filename, _ = QFileDialog.getOpenFileName(self,"Load File",
            "","CSV Files (*.csv);;", options=options)
    if filename:
      error_code = self.curr_model.load_dataset(filename)
      if error_code != '0':
        alerts.sudden_death(error_code)




  #If fitting data, call fit_data in data_processing.py, which will do some preprocessing on the
  #data then call the appropriate method associated with the curr_model object of class model_parameter_set.
  #For cases where no fitting is required (MIC vs MIC data, user-specified cutoffs) it will make no changes
  #to the cutoffs and return '0' so that we can proceed to data plotting.
  def fit_data(self):
    output_code = data_processing.fit_data(self.curr_model)
        
    #If it was possible to fit using several different window sizes, the fitting function will return a
    #code starting with !. This is not an error, just an informational message. The end user asked
    #that the program make them aware whenever this occurred.
    if output_code.startswith('!'):
      window_sizes = output_code.split('!, ')[1]
      alerts.non_fatal_message('It was possible to fit the data using intermediate disk zone sizes of '
                           '%s mm. The program has defaulted to the smallest window size possible.'
                           %window_sizes)
    #If neither ! nor 0, the fitting function returned an error, tell the user what it is.
    elif output_code != '0':
      alerts.sudden_death(output_code)
      return
    #Update the disk cutoff boxes to use the updated cutoffs from fitting.
    self.diskS_breakpoint.setText(str(self.curr_model.xcutoffS))
    self.diskR_breakpoint.setText(str(self.curr_model.xcutoffR))
    #OK, now plot the data regardless of whether we fitted it or used their cutoffs.
    output_code = disk_plotting.gen_plot(self)
    #Return code other than 0 indicates an error.
    if output_code != '0':
      alerts.sudden_death(output_code)
      return
    


  def update_s_cutoff(self, text):
    try:
      self.curr_model.ycutoffS = float(text)
    except:
      pass

  def update_r_cutoff(self, text):
    try:
      self.curr_model.ycutoffR = float(text)
    except:
      pass

  def diskS_manual_cutoff(self, text):
    try:
      self.curr_model.xcutoffS = float(text)
    except:
      pass

  def diskR_manual_cutoff(self, text):
    try:
      self.curr_model.xcutoffR = float(text)
    except:
      pass

  def manual_fit_button(self, state):
    if state == QtCore.Qt.Checked:
      alerts.non_fatal_message("You have selected use of manual cutoffs! This will override the fitting procedure and use the cutoffs you have specified whether "
          "they are reasonable or not. 'Just because you can, doesn't mean you should.'")
      self.curr_model.use_user_defined_disk_cutoffs = True
    else:
      self.curr_model.use_user_defined_disk_cutoffs = False

  #Because of how susceptibility and resistance are defined differently for disks vs MICs, if the user selects
  #MIC vs MIC, we need to change the labels on the cutoff boxes. Same in reverse if they indicate they are
  #loading disk data by unchecking the MIC vs MIC box.
  def mic_vs_mic_data(self, state):
    if state == QtCore.Qt.Checked:
      alerts.non_fatal_message("The program will now assume that data which you import is MIC vs MIC (i.e. broth vs e-test) "
                            "data. Uncheck the box to return to processing disk vs MIC data. "
                            "Note that the program will now expect to have broth MICs in column 1 of any csv you load, "
                            "and alternate-method MICs in column 2.")
      self.diskS_label.setText('Susceptibility cutoff (<=, mg/L)')
      self.diskR_label.setText('Resistance cutoff (>=, mg/L)')
      self.curr_model.mic_vs_mic = True
    else:
      self.curr_model.mic_vs_mic = False
      alerts.non_fatal_message("The program will now assume that data which you import is disk vs MIC data (the default setting). "
                             "When loading a csv, MIC data should be column 1, disk data in column 2.")
      self.diskS_label.setText('Susceptibility disk cutoff(>=, mm)')
      self.diskR_label.setText('Resistance disk cutoff (<=, mm)')

  #The end user wanted the ability to output to a csv file with the same data
  #as contained in the plot but in a text-based histogram.
  #This is all handled under data_export.py
  def export_results(self):
    options = QFileDialog.Options()
    filename, _ = QFileDialog.getSaveFileName(self,"Save File",
            "","CSV Files (*.csv);;", options=options)
    if filename:
      error_code = data_export.export_results(self.curr_model, filename)
      if error_code != '0':
        alerts.sudden_death(error_code)
        return
      alerts.non_fatal_message('Your results have been exported to a csv file entitled "%s" .'%filename)
