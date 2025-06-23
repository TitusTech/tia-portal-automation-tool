from pathlib import Path
import slint



class MainWindow(slint.loader.ui.app_window.AppWindow):
    @slint.callback
    def request_increase_value(self):
        self.counter = self.counter + 1

    @slint.callback
    def select_json(self):
        print('wtf')
    


main_window = MainWindow()
main_window.show()
main_window.run()
