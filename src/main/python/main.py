# -*-coding:utf-8 -*-
import json
import os
import shutil
import sys
import zipfile
from glob import glob

import PySide2
from PySide2 import QtCore
from PySide2.QtCore import QUrl
from PySide2.QtGui import QFont, QPixmap, Qt
from PySide2.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from PySide2.QtMultimediaWidgets import QVideoWidget
from PySide2.QtWidgets import QLabel, QWidget, QGridLayout, QLayout, QStyleFactory
from fbs_runtime.application_context.PySide2 import ApplicationContext


# noinspection PyArgumentList
class Ui(QWidget):
    def __init__(self, _app_context: ApplicationContext, parent=None):
        super().__init__(parent)

        self.app_context = _app_context
        self.gridLayout = QGridLayout(self)
        self.gridLayout.setSizeConstraint(QLayout.SetFixedSize)
        self.objectExt = None
        self.support_object = {}
        self.temp_path = 'temp'

        self.default_model = json.load(
            open(self.app_context.get_resource('object_model/default.json'), 'r', encoding='UTF-8'))
        shutil.rmtree(self.temp_path, ignore_errors=True)

    def list_image_frame(self, item, _config):
        index = 0
        if _config['orientation'] == "vertical":
            for _width in range(0, _config['max_width'], _config['position'][3]):
                for _height in range(0, _config['max_height'], _config['position'][3]):
                    list_image_item = QLabel(self)
                    list_image_item.setObjectName(f'list_image_{item}_{index}')
                    self.gridLayout.addWidget(list_image_item,
                                              _config['position'][0] + _height,
                                              _config['position'][1] + _width,
                                              _config['position'][2],
                                              _config['position'][3], )
                    index += 1
        elif _config['orientation'] == "horizontal":
            for _height in range(0, _config['max_height'], _config['position'][2]):
                for _width in range(0, _config['max_width'], _config['position'][3]):
                    list_image_item = QLabel(self)
                    list_image_item.setObjectName(f'list_image_{item}_{index}')
                    self.gridLayout.addWidget(list_image_item,
                                              _config['position'][0] + _height,
                                              _config['position'][1] + _width,
                                              _config['position'][2],
                                              _config['position'][3], )
                    index += 1

    def list_image_read(self, file, name, _config):
        images = glob(f"{self.app_context.get_resource()}/{self.temp_path}/{file}/{_config['file_format']}")
        for _index in range(
                int((_config['max_width'] / (_config['position'][3])))
                * int((_config['max_height'] / (_config['position'][2])))):
            self.findChildren(QLabel, f'list_image_{name}_{_index}')[0].clear()
        for _index, image in enumerate(images):
            pixmap = QPixmap(image)
            pixmap = pixmap.scaled(
                int(self.screen().geometry().width() / 4),
                int(self.screen().geometry().height() / 3), Qt.KeepAspectRatio)
            self.findChildren(QLabel, f'list_image_{name}_{_index}')[0].setPixmap(pixmap)
            self.findChildren(QLabel, f'list_image_{name}_{_index}')[0].setScaledContents(True)

    def image_frame(self, item, _config):
        image = QLabel(self)
        image.setScaledContents(True)
        image.setObjectName(f'image_{item}')
        self.gridLayout.addWidget(image, *_config['position'])

    def image_read(self, file_name, item, _config):
        if self._model['data'][item]['type'] == 'image':
            image_path = glob(f"{self.app_context.get_resource()}/{self.temp_path}/{file_name}/{item}.*")[0]
        else:
            image_path = glob(
                f"{self.app_context.get_resource()}/{self.temp_path}/{file_name}/{item}"
                f".{self._model['data'][item]['type']}")[0]
        pixmap = QPixmap(image_path)
        # pixmap = pixmap.scaled(
        #     int(self.screen().geometry().width() / 4),
        #     int(self.screen().geometry().height() / 3), Qt.KeepAspectRatio)
        self.findChildren(QLabel, f'image_{item}')[0].setPixmap(pixmap)

    def video_frame(self, item, _config):
        self.support_object[f'{item}_player'] = QMediaPlayer()
        _video_widget = QVideoWidget()
        _video_widget.setObjectName(item)
        self.gridLayout.addWidget(_video_widget, *_config['position'])
        self.support_object[f'{item}_player'].setVideoOutput(_video_widget)

    def video_read(self, file, name, _config):
        url = glob(f"{self.app_context.get_resource()}/{self.temp_path}/{file}/{name}*")[0]

        playlist = QMediaPlaylist(self)
        playlist.addMedia(QMediaContent(QUrl.fromLocalFile(url)))
        playlist.setPlaybackMode(QMediaPlaylist.CurrentItemInLoop)
        playlist.setCurrentIndex(0)
        self.support_object[f'{name}_player'].setPlaylist(playlist)
        if _config['autoplay']:
            self.support_object[f'{name}_player'].play()

    def format_str_read(self, _, name, _config):
        format_args = (self.info[key] for key in _config['format_args'][1:])
        self.findChildren(QLabel, name)[0].setText(
            _config['format_args'][0].format(*format_args)
        )

    def keyPressEvent(self, event: PySide2.QtGui.QKeyEvent) -> None:
        if (event.key() == QtCore.Qt.Key_Right) or (event.key() == QtCore.Qt.Key_Down):
            if self.file_index < len(self.file_dirs) - 1:
                self.read_file(f"{self.file_path}\\{self.file_dirs[self.file_index + 1]}")
        elif (event.key() == QtCore.Qt.Key_Left) or (event.key() == QtCore.Qt.Key_Up):
            if self.file_index > 0:
                self.read_file(f"{self.file_path}\\{self.file_dirs[self.file_index - 1]}")
        event.accept()

    def str_read(self, _, item, _config):
        if "value" not in self._model['data'][item]:
            self.findChildren(QLabel, item)[0].setText(str(self.info[item]))

    def str_frame(self, item, _config: dict):
        str_label = QLabel(self)
        str_label.setObjectName(item)
        str_label.setAlignment(Qt.AlignCenter)
        if "value" in self._model['data'][item]:
            str_label.setText(str(self._model['data'][item]['value']))
        font = QFont()
        font.setPointSize(self.default_model['str']['font']['textSize'])
        if 'font' in _config:
            if 'textSize' in _config['font']:
                font.setPointSize(_config['font']['textSize'])
        str_label.setFont(font)
        self.gridLayout.addWidget(str_label, *_config['position'])

    format_str_frame = str_frame

    def make_frame(self):
        for item in self._model['data']:
            if self._model['data'][item]['type'] == 'video':
                self.video_frame(item, self._model['data'][item])
            elif self._model['data'][item]['type'] == 'list_image':
                self.list_image_frame(item, self._model['data'][item])
            elif self._model['data'][item]['type'] == 'format_str':
                self.format_str_frame(item, self._model['data'][item])
            elif self._model['data'][item]['type'] == 'str':
                self.str_frame(item, self._model['data'][item])
            elif self._model['data'][item]['type'] in ['image', 'jpg', 'png', 'bmp']:
                self.image_frame(item, self._model['data'][item])

    def read_data(self, file_name):
        for item in self._model['data']:
            if self._model['data'][item]['type'] == 'video':
                self.video_read(file_name, item, self._model['data'][item])
            elif self._model['data'][item]['type'] == 'list_image':
                self.list_image_read(file_name, item, self._model['data'][item])
            elif self._model['data'][item]['type'] == 'format_str':
                self.format_str_read(file_name, item, self._model['data'][item])
            elif self._model['data'][item]['type'] == 'str':
                self.str_read(file_name, item, self._model['data'][item])
            elif self._model['data'][item]['type'] in ['image', 'jpg', 'png', 'bmp']:
                self.image_read(file_name, item, self._model['data'][item])

    def set_window_center(self):

        screen = self.screen().geometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2, (screen.height() - size.height()) / 2)

    # noinspection PyAttributeOutsideInit
    def read_file(self, file):
        name, ext = os.path.splitext(os.path.split(file)[1])

        if ext == "":
            self.temp_path = os.path.abspath(f'{name}/..')
            ext = f'.{os.path.split(self.temp_path)[1]}'
            self.file_path = self.temp_path
            self.file_dirs = os.listdir(self.file_path)
            self.file_index = self.file_dirs.index(name)
        elif ext == '.json':
            os.makedirs(f"{self.app_context.get_resource()}/{self.temp_path}/{name}", exist_ok=True)
            shutil.copy(file, f"{self.app_context.get_resource()}/{self.temp_path}/{name}/info.json")
        else:
            zipobj = zipfile.ZipFile(file, 'r', )
            zipobj.extractall(f"{self.app_context.get_resource()}/{self.temp_path}/{name}")
            zipobj.close()
            self.file_path = os.path.split(file)[0]
            self.file_dirs = os.listdir(self.file_path)
            self.file_index = self.file_dirs.index(os.path.split(file)[1])
        if self.objectExt != ext:
            self.objectExt = ext
            self.support_object.clear()
            for i in reversed(range(self.gridLayout.count())):
                self.gridLayout.itemAt(i).widget().deleteLater()
            self._model = json.load(open(
                f'{self.app_context.get_resource()}/object_model/{self.objectExt[1:]}.json', 'r', encoding='UTF-8'))
            self.make_frame()
        self.info = json.load(open(
            f'{self.app_context.get_resource()}/{self.temp_path}/{name}/info.json', 'r', encoding='UTF-8'))
        self.read_data(name)


if __name__ == '__main__':
    app_context = ApplicationContext()  # 1. Instantiate ApplicationContext
    window = Ui(app_context)
    window.setStyle(QStyleFactory.create("windowsvista"))
    if len(sys.argv) > 1:
        window.read_file(sys.argv[1])
    else:
        window.read_file(f"{app_context.get_resource()}/data/50pd0/01.frame_predict")
    window.show()
    window.set_window_center()
    shutil.rmtree(f"{app_context.get_resource()}/temp", ignore_errors=True)
    exit_code = app_context.app.exec_()
