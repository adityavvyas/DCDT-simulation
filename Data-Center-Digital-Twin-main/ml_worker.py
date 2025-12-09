from PyQt5.QtCore import QObject, pyqtSignal

class MLCalibrationWorker(QObject):
    """
    A PyQt-compatible worker that runs the ML calibration in a separate thread.
    """
    finished = pyqtSignal() # Signal to emit when calibration is done

    def __init__(self, ml_engine):
        super().__init__()
        self.ml_engine = ml_engine

    def run(self):
        """
        This method is executed in the new thread.
        """
        self.ml_engine.calibrate()
        self.finished.emit()