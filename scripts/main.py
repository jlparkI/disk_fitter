from user_interface import main_window
from PyQt5.QtWidgets import QApplication
from alerts import display_start_message

  
#Entry point. When script runs, create an object of class main_window after
#giving the user some preliminary information. The main_window class is the user
#interface and has as one of its attributes an object of class model_parameter_set,
#which will store user data and fit parameters. 
if __name__ == '__main__':
  app = QApplication([])
  display_start_message()
  current_app = main_window()
  app.exec_()
  exit()
